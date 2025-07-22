from pydantic import BaseModel
from typing import List

class EditionData(BaseModel):
    title: str
    publisher: str
    published_date: str
    description: str
    thumbnail: str
    authors: List[str]