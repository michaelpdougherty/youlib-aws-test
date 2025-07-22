# api/routes/books.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/books/")
async def get_books():
  return {"route": "GET /books/"}

@router.post("/books/")
async def add_book():
  return {"route": "POST /books/"}

# Delete library 
@router.delete("/books/")
async def register():
  return {"route": "DELETE /books/"}
