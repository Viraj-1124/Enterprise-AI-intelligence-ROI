from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Department, Employee, Role
from app.schemas.schemas import DepartmentCreate, DepartmentOut, EmployeeCreate, EmployeeOut
from app.services.auth import hash_password, require_roles

router = APIRouter(prefix="/api", tags=["organization"])


@router.post("/departments", response_model=DepartmentOut)
def create_department(req: DepartmentCreate, db: Session = Depends(get_db),
                       _admin=Depends(require_roles("admin"))):
    dept = Department(name=req.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.post("/employees", response_model=EmployeeOut)
def create_employee(req: EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(Employee).filter(Employee.email == req.email).first():
        raise HTTPException(status_code=422, detail="Employee with this email already exists")
    try:
        role = Role(req.role)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid role")
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
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee
