from sqlalchemy import Boolean, Column, Integer, JSON, String

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False)

    description = Column(String(500), nullable=True)

    category_specific_fields = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)