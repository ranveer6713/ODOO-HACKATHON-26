from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    employee_code = Column(
        String(50),
        unique=True,
        index=True,
        nullable=True
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=True
    )

    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship(
        "User",
        back_populates="employee"
    )

    department = relationship(
        "Department",
        back_populates="employees",
        foreign_keys=[department_id]
    )