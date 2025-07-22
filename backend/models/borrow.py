from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    TIMESTAMP,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from enum import Enum
from db.session import Base

class BorrowStatus(str, Enum):
    requested = "requested"
    approved = "approved"
    borrowed = "borrowed"
    returned = "returned"
    canceled = "canceled"

class Borrow(Base):
    __tablename__ = "borrows"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested', 'approved', 'borrowed', 'returned', 'canceled')",
            name="borrow_status_check"
        ),
        # Enforces unique book_id
        UniqueConstraint("book_id", name="uq_borrow_book_id")
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("user_editions.id", ondelete="CASCADE"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status = Column(String, nullable=False)

    requested_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    confirmed_at = Column(TIMESTAMP, nullable=True)
    borrowed_at = Column(TIMESTAMP, nullable=True)
    due_date = Column(Date, nullable=True)
    returned_at = Column(TIMESTAMP, nullable=True)

    renewal_count = Column(Integer, nullable=False, default=0)
    max_renewals = Column(Integer, nullable=False, default=2)