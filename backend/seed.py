import sys
import os
from datetime import datetime, date, timedelta

# Add backend directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal
from app.models import Role, User, Employee, Department, Category, Asset, Allocation, Transfer, AssetHistory
from app.core.security import get_password_hash


def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Role).first() is not None:
            print("Database already seeded. Skipping...")
            return

        print("Seeding default roles...")
        admin_role = Role(name="Admin")
        manager_role = Role(name="Asset Manager")
        head_role = Role(name="Department Head")
        emp_role = Role(name="Employee")
        
        db.add_all([admin_role, manager_role, head_role, emp_role])
        db.commit()

        # Refresh roles to get IDs
        db.refresh(admin_role)
        db.refresh(manager_role)
        db.refresh(head_role)
        db.refresh(emp_role)

        print("Seeding default users...")
        users = [
            User(name="System Administrator", email="admin@assetflow.com", hashed_password=get_password_hash("admin123"), role_id=admin_role.id, is_active=True),
            User(name="Jane Manager", email="manager@assetflow.com", hashed_password=get_password_hash("manager123"), role_id=manager_role.id, is_active=True),
            User(name="Robert Head", email="head@assetflow.com", hashed_password=get_password_hash("head123"), role_id=head_role.id, is_active=True),
            User(name="John Employee", email="employee@assetflow.com", hashed_password=get_password_hash("employee123"), role_id=emp_role.id, is_active=True),
        ]
        db.add_all(users)
        db.commit()

        for u in users:
            db.refresh(u)

        admin_user, manager_user, head_user, employee_user = users

        print("Seeding default departments...")
        dept_it = Department(name="Information Technology", is_active=True)
        dept_hr = Department(name="Human Resources", is_active=True)
        dept_finance = Department(name="Finance", is_active=True)
        
        db.add_all([dept_it, dept_hr, dept_finance])
        db.commit()
        db.refresh(dept_it)
        db.refresh(dept_hr)
        db.refresh(dept_finance)

        print("Seeding employee directory records...")
        emp_admin = Employee(user_id=admin_user.id, employee_code="EMP-001", department_id=dept_it.id, is_active=True)
        emp_manager = Employee(user_id=manager_user.id, employee_code="EMP-002", department_id=dept_it.id, is_active=True)
        emp_head = Employee(user_id=head_user.id, employee_code="EMP-003", department_id=dept_hr.id, is_active=True)
        emp_std = Employee(user_id=employee_user.id, employee_code="EMP-004", department_id=dept_finance.id, is_active=True)

        db.add_all([emp_admin, emp_manager, emp_head, emp_std])
        db.commit()
        db.refresh(emp_admin)
        db.refresh(emp_manager)
        db.refresh(emp_head)
        db.refresh(emp_std)

        # Set Department head relation
        dept_it.department_head_id = emp_manager.id
        dept_hr.department_head_id = emp_head.id
        db.commit()

        print("Seeding asset categories...")
        cat_laptop = Category(
            name="Laptops",
            description="Company issue laptops and workstations",
            category_specific_fields={"RAM": "text", "CPU": "text", "Storage": "text", "Warranty Years": "number"},
            is_active=True
        )
        cat_furniture = Category(
            name="Office Furniture",
            description="Desks, chairs, filing cabinets",
            category_specific_fields={"Material": "text", "Dimensions": "text"},
            is_active=True
        )
        db.add_all([cat_laptop, cat_furniture])
        db.commit()
        db.refresh(cat_laptop)
        db.refresh(cat_furniture)

        print("Seeding physical assets...")
        asset1 = Asset(
            name="MacBook Pro 16",
            asset_tag="AST-0001",
            description="Apple M2 Pro 16GB RAM 512GB SSD",
            category_id=cat_laptop.id,
            is_bookable=False,
            status="Available",
            serial_number="SN-MBP16-001",
            purchase_date=date(2023, 5, 10),
            purchase_cost=2499.00,
            warranty_expiry=date(2026, 5, 10),
            category_specific_data={"RAM": "16GB", "CPU": "M2 Pro", "Storage": "512GB SSD", "Warranty Years": 3}
        )
        asset2 = Asset(
            name="ThinkPad T14 Gen 3",
            asset_tag="AST-0002",
            description="Lenovo Intel Core i7 16GB RAM 512GB SSD",
            category_id=cat_laptop.id,
            is_bookable=False,
            status="Available",
            serial_number="SN-TPT14-002",
            purchase_date=date(2023, 6, 15),
            purchase_cost=1250.00,
            warranty_expiry=date(2025, 6, 15),
            category_specific_data={"RAM": "16GB", "CPU": "Intel i7", "Storage": "512GB SSD", "Warranty Years": 2}
        )
        asset3 = Asset(
            name="Ergonomic Mesh Chair",
            asset_tag="AST-0003",
            description="Steelcase Gesture Ergonomic Office Chair",
            category_id=cat_furniture.id,
            is_bookable=True,
            status="Available",
            serial_number="SN-SCGC-003",
            purchase_date=date(2022, 11, 20),
            purchase_cost=450.00,
            warranty_expiry=date(2027, 11, 20),
            category_specific_data={"Material": "Polyester Mesh & Aluminum", "Dimensions": "27W x 26D x 44H"}
        )
        db.add_all([asset1, asset2, asset3])
        db.commit()

        print("Database seeded successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
