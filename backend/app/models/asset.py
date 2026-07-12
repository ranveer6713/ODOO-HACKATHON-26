from sqlalchemy import Column, Integer, String, Boolean, Date, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    asset_tag = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    serial_number = Column(String(100), unique=True, nullable=True, index=True)

    # Category linkage
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Status: Available | Allocated | Under Maintenance | Retired | Lost
    status = Column(String(50), nullable=False, default="Available")

    # Financial
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, nullable=True)
    warranty_expiry = Column(Date, nullable=True)

    # Flags
    is_bookable = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Dynamic category-specific JSON fields (e.g. RAM, CPU for Laptops)
    category_data = Column(JSON, nullable=True)

    # Relationships
    category = relationship("Category")
    allocations = relationship("Allocation", back_populates="asset", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="asset", cascade="all, delete-orphan")
    history = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")
