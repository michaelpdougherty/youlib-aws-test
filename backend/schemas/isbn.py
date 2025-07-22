from pydantic import BaseModel

class ISBN(BaseModel):
    isbn: str