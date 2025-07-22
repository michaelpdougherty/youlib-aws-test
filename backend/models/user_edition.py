from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from db.session import Base

class UserEdition(Base):
    __tablename__ = "user_editions"
    __table_args__ = (
        UniqueConstraint("edition_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    edition_id = Column(Integer, ForeignKey("editions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)  # Add ForeignKey if users table exists
    condition = Column(String)
    location = Column(String)
    is_available = Column(Boolean, default=True)
    added_at = Column(TIMESTAMP, server_default=func.now())
