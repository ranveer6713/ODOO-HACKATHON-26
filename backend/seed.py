"""
backend/seed.py
Initialises the database schema and populates default seed data.
Usage:  python backend/seed.py
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal
from app.models import Role, User, Employee, Department, Category, Asset, Allocation, Transfer, AssetHistory
from app.core.security import get_password_hash


def seed():
    print("[*] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Role).first():
            print("[OK] Database already seeded -- skipping.")
            return

        # -- Roles -------------------------------------------------------------
        print("[*] Seeding roles...")
        roles = {name: Role(name=name) for name in ["Admin", "Asset Manager", "Department Head", "Employee"]}
        db.add_all(roles.values())
        db.commit()
        for r in roles.values():
            db.refresh(r)

        # -- Users -------------------------------------------------------------
        print("[*] Seeding users...")
        users_data = [
            ("Admin User",    "admin@assetflow.com",    "admin123",    "Admin"),
            ("Jane Manager",  "manager@assetflow.com",  "manager123",  "Asset Manager"),
            ("Robert Head",   "head@assetflow.com",     "head123",     "Department Head"),
            ("John Employee", "employee@assetflow.com", "employee123", "Employee"),
        ]
        users = []
        for name, email, pwd, role_name in users_data:
            u = User(
                name=name,
                email=email,
                hashed_password=get_password_hash(pwd),
                role_id=roles[role_name].id,
                is_active=True,
            )
            db.add(u)
            users.append(u)
        db.commit()
        for u in users:
            db.refresh(u)

        admin_u, manager_u, head_u, emp_u = users

        # -- Departments -------------------------------------------------------
        print("[*] Seeding departments...")
        dept_it  = Department(name="Information Technology", is_active=True)
        dept_hr  = Department(name="Human Resources",        is_active=True)
        dept_fin = Department(name="Finance",                is_active=True)
        db.add_all([dept_it, dept_hr, dept_fin])
        db.commit()
        for d in [dept_it, dept_hr, dept_fin]:
            db.refresh(d)

        # -- Employees ---------------------------------------------------------
        print("[*] Seeding employees...")
        emp_records = [
            Employee(user_id=admin_u.id,   employee_code="EMP-0001", department_id=dept_it.id,  is_active=True),
            Employee(user_id=manager_u.id, employee_code="EMP-0002", department_id=dept_it.id,  is_active=True),
            Employee(user_id=head_u.id,    employee_code="EMP-0003", department_id=dept_hr.id,  is_active=True),
            Employee(user_id=emp_u.id,     employee_code="EMP-0004", department_id=dept_fin.id, is_active=True),
        ]
        db.add_all(emp_records)
        db.commit()
        for e in emp_records:
            db.refresh(e)

        emp_admin, emp_manager, emp_head, emp_standard = emp_records
        dept_it.department_head_id = emp_manager.id
        dept_hr.department_head_id = emp_head.id
        db.commit()

        # -- Categories --------------------------------------------------------
        print("[*] Seeding categories...")
        cat_laptop = Category(
            name="Laptops",
            description="Portable computers and workstations",
            category_specific_fields={"RAM": "text", "CPU": "text", "Storage": "text", "OS": "text"},
            is_active=True,
        )
        cat_furniture = Category(
            name="Office Furniture",
            description="Desks, chairs, cabinets",
            category_specific_fields={"Material": "text", "Colour": "text"},
            is_active=True,
        )
        db.add_all([cat_laptop, cat_furniture])
        db.commit()
        db.refresh(cat_laptop)
        db.refresh(cat_furniture)

        # -- Assets ------------------------------------------------------------
        print("[*] Seeding assets...")
        assets_data = [
            Asset(
                name="MacBook Pro 16-inch",
                asset_tag="AST-0001",
                description="Apple M2 Pro, 16 GB RAM, 512 GB SSD",
                serial_number="SN-MBP16-001",
                category_id=cat_laptop.id,
                status="Available",
                purchase_date=date(2023, 5, 10),
                purchase_cost=2499.00,
                warranty_expiry=date(2026, 5, 10),
                is_bookable=False,
                category_data={"RAM": "16 GB", "CPU": "M2 Pro", "Storage": "512 GB SSD", "OS": "macOS"},
            ),
            Asset(
                name="ThinkPad T14 Gen 3",
                asset_tag="AST-0002",
                description="Lenovo, Intel Core i7, 16 GB RAM, 512 GB SSD",
                serial_number="SN-TPT14-002",
                category_id=cat_laptop.id,
                status="Available",
                purchase_date=date(2023, 6, 15),
                purchase_cost=1250.00,
                warranty_expiry=date(2025, 6, 15),
                is_bookable=False,
                category_data={"RAM": "16 GB", "CPU": "Intel i7", "Storage": "512 GB SSD", "OS": "Windows 11"},
            ),
            Asset(
                name="Ergonomic Mesh Chair",
                asset_tag="AST-0003",
                description="Steelcase Gesture, lumbar support",
                serial_number="SN-SCGC-003",
                category_id=cat_furniture.id,
                status="Available",
                purchase_date=date(2022, 11, 20),
                purchase_cost=450.00,
                warranty_expiry=date(2027, 11, 20),
                is_bookable=True,
                category_data={"Material": "Polyester Mesh + Aluminium", "Colour": "Black"},
            ),
        ]
        db.add_all(assets_data)
        db.commit()

        print("\n[OK] Database seeded successfully!\n")
        print("Test accounts:")
        print("  admin@assetflow.com    / admin123    (Admin)")
        print("  manager@assetflow.com  / manager123  (Asset Manager)")
        print("  head@assetflow.com     / head123     (Department Head)")
        print("  employee@assetflow.com / employee123 (Employee)")

    except Exception as exc:
        print(f"[ERR] Seeding failed: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
