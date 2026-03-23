"""
User feedback model for scan results
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base


class Feedback(Base):
    """Stores user feedback on scan results."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(String(20), nullable=False)  # helpful, not_helpful, suggestion
    comment = Column(Text, nullable=True)
    product_name = Column(String(255), nullable=True)
    overall_safety = Column(String(20), nullable=True)
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
