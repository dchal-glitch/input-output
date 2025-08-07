from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from db.database import Base


class IOMatrix(Base):
    __tablename__ = "io_matrices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    sectors = Column(JSON, nullable=False)  # List of sector names
    intermediate_consumption_data = Column(JSON, nullable=False)  # 2D matrix data
    final_demand_data = Column(JSON, nullable=False)  # 2D matrix data
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
