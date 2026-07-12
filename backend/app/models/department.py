from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)

    parent_department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True
    )

    department_head_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=True
    )

    is_active = Column(Boolean, default=True, nullable=False)

    parent_department = relationship(
        "Department",
        remote_side=[id],
        foreign_keys=[parent_department_id]
    )

    employees = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="Employee.department_id"
    )

    department_head = relationship(
        "Employee",
        foreign_keys=[department_head_id],
        post_update=True
    )