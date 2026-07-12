from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class AssetHistory(Base):
    __tablename__ = "asset_histories"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Action types: registration, allocation, return, transfer_request, transfer_approve, transfer_reject, maintenance_start, maintenance_end, status_change, audit
    action = Column(String(50), nullable=False)
    
    action_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_date = Column(DateTime, nullable=False)
    
    notes = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)  # Detailed log (e.g. status changes, transfer details)

    asset = relationship("Asset", back_populates="history")
    action_by = relationship("User")
