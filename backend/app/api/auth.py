from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Employee, Role
from app.schemas.schemas import BootstrapRequest, EmployeeOut, LoginRequest, Token
from app.services.auth import get_current_employee, hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == req.email).first()
    if not employee or not verify_password(req.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(employee.id, employee.role.value)
    return Token(access_token=token, role=employee.role.value)


@router.get("/me", response_model=EmployeeOut)
def current_user(employee: Employee = Depends(get_current_employee)):
    return employee


@router.get("/bootstrap-status")
def bootstrap_status(db: Session = Depends(get_db)):
    return {"setup_required": db.query(Employee).count() == 0}


@router.post("/bootstrap", response_model=Token)
def bootstrap(req: BootstrapRequest, db: Session = Depends(get_db)):
    if db.query(Employee).count() > 0:
        raise HTTPException(status_code=409, detail="Workspace already has an administrator")
    employee = Employee(name=req.name, email=req.email, role=Role.admin, hourly_cost=0,
                        hashed_password=hash_password(req.password))
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return Token(access_token=create_access_token(employee.id, employee.role.value), role=employee.role.value)
