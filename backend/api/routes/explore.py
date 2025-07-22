# api/routes/explore.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/explore")
async def explore():
  return {"route": "GET /explore"}
