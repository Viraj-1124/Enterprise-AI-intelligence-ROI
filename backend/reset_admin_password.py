"""Reset a local administrator password using the application's configured database."""

import getpass
import sys

from app.database.session import SessionLocal
from app.models.models import Employee, Role
from app.services.auth import hash_password


def main() -> int:
    email = sys.argv[1].strip() if len(sys.argv) > 1 else input("Admin email: ").strip()
    if len(sys.argv) > 2:
        print("Usage: python reset_admin_password.py [admin-email]")
        return 2

    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.email == email).first()
        if employee is None or employee.role != Role.admin:
            print("No administrator account found for that email.")
            return 1

        password = getpass.getpass("New password (minimum 8 characters): ")
        confirmation = getpass.getpass("Confirm new password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return 1
        if password != confirmation:
            print("Passwords did not match; no changes were made.")
            return 1

        employee.hashed_password = hash_password(password)
        db.commit()
        print(f"Password reset for {employee.email}. You can now sign in.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
