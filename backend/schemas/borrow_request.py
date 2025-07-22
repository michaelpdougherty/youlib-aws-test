from pydantic import BaseModel

class BorrowRequest(BaseModel):
    id: int