from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Employee
from app.schemas.schemas import LoginRequest, Token
from app.services.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == req.email).first()
    if not employee or not verify_password(req.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(employee.id, employee.role.value)
    return Token(access_token=token, role=employee.role.value)
