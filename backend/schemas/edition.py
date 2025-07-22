from pydantic import BaseModel
from typing import List

class Edition(BaseModel):
    id: int
    work_id: int
    title: str
    publisher: str
    published_date: str
    description: str
    thumbnail: str
    authors: List[str]