from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class BorrowOut(BaseModel):
    id: int
    book_id: int
    borrower_id: int
    status: str
    requested_at: datetime
    confirmed_at: Optional[datetime] = None
    borrowed_at: Optional[datetime] = None
    due_date: Optional[date] = None
    returned_at: Optional[datetime] = None
    renewal_count: int
    max_renewals: int

    class Config:
        from_attributes = True