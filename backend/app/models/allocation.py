from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Target Type: "employee" or "department"
    allocated_to_type = Column(String(50), nullable=False)
    
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    allocated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    allocated_at = Column(DateTime, nullable=False)
    expected_return_date = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    
    condition_on_allocation = Column(String(200), nullable=True)
    condition_on_return = Column(String(200), nullable=True)
    
    # Status: "active", "returned", "overdue"
    status = Column(String(50), default="active", nullable=False)

    asset = relationship("Asset", back_populates="allocations")
    employee = relationship("Employee", foreign_keys=[employee_id])
    department = relationship("Department", foreign_keys=[department_id])
    allocated_by = relationship("User", foreign_keys=[allocated_by_id])
