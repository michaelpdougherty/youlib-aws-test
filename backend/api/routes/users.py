# api/routes/users.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
  return {"route": "POST /login"}

@router.post("/register")
async def register():
  return {"route": "POST /register"}
