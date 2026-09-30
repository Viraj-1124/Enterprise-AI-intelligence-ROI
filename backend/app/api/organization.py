from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import ActivityEvent, AIUsage, Department, Employee, EmployeeConnection, Role, Task, WorkSession
from app.schemas.schemas import DepartmentCreate, DepartmentOut, EmployeeCreate, EmployeeOut
from app.services.auth import get_current_employee, hash_password, require_roles

router = APIRouter(prefix="/api", tags=["organization"])


@router.post("/departments", response_model=DepartmentOut)
def create_department(req: DepartmentCreate, db: Session = Depends(get_db),
                       _manager=Depends(require_roles("admin", "manager"))):
    dept = Department(name=req.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _manager=Depends(require_roles("admin", "manager"))):
    return db.query(Department).all()


@router.post("/employees", response_model=EmployeeOut)
def create_employee(req: EmployeeCreate, db: Session = Depends(get_db),
                    actor=Depends(require_roles("admin", "manager"))):
    if db.query(Employee).filter(Employee.email == req.email).first():
        raise HTTPException(status_code=422, detail="Employee with this email already exists")
    try:
        role = Role(req.role)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid role")
    if role == Role.admin and actor.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only administrators can create administrator accounts")
    employee = Employee(
        name=req.name,
        email=req.email,
        department_id=req.department_id,
        role=role,
        hourly_cost=req.hourly_cost,
        hashed_password=hash_password(req.password),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db), _manager=Depends(require_roles("admin", "manager"))):
    return db.query(Employee).all()


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: str, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    record = db.query(Employee).filter(Employee.id == employee_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current.role == Role.employee and current.id != employee_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return record


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db),
                    _manager=Depends(require_roles("admin", "manager"))):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.role == Role.admin:
        raise HTTPException(status_code=400, detail="Administrator accounts cannot be deleted here")
    has_history = any((
        db.query(Task.id).filter(Task.employee_id == employee_id).first(),
        db.query(AIUsage.id).filter(AIUsage.employee_id == employee_id).first(),
        db.query(WorkSession.id).filter(WorkSession.employee_id == employee_id).first(),
        db.query(ActivityEvent.id).filter(ActivityEvent.employee_id == employee_id).first(),
    ))
    if has_history:
        raise HTTPException(status_code=409, detail="This employee has tracked work history. Remove is blocked to preserve ROI and usage analytics.")
    db.query(EmployeeConnection).filter(EmployeeConnection.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()
    return {"status": "deleted", "employee_id": employee_id}


@router.delete("/departments/{department_id}")
def delete_department(department_id: str, db: Session = Depends(get_db),
                      _manager=Depends(require_roles("admin", "manager"))):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    if department.employees:
        raise HTTPException(status_code=409, detail="Move employees to another department before deleting this department")
    db.delete(department)
    db.commit()
    return {"status": "deleted", "department_id": department_id}
