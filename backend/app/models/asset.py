from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    asset_tag = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Files & Media
    image_url = Column(String(500), nullable=True)
    document_urls = Column(JSON, nullable=True)  # List of URLs/names
    
    is_bookable = Column(Boolean, default=False, nullable=False)
    
    # Asset Lifecycle Status: Available, Allocated, Reserved, Under Maintenance, Lost, Retired, Disposed
    status = Column(String(50), default="Available", nullable=False)
    
    serial_number = Column(String(100), nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    
    # Dynamic values corresponding to category_specific_fields
    category_specific_data = Column(JSON, nullable=True)

    category = relationship("Category")
    allocations = relationship("Allocation", back_populates="asset", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="asset", cascade="all, delete-orphan")
    history = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")
