# api/routes/borrow_requests.py
from fastapi import APIRouter

router = APIRouter(prefix="/borrow-requests", tags=["borrows"])

@router.post("/")
async def request_book():
  return {"route": "POST /borrow-requests/"}

@router.get("/sent")
async def get_sent_requests():
  return {"route": "GET /borrow-requests/sent"}

@router.get("/received")
async def get_received_requests():
  return {"route": "GET /borrow-requests/received"}
