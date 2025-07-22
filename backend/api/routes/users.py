# api/routes/users.py
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from schemas import UserLogin, UserRegistration
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from utils.jwt_utils import create_jwt

router = APIRouter()

@router.post("/login")
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_session)):
  email = user_login.email
  password = user_login.password
  # Check email and password match
  # TODO hash passwords
  statement = text("SELECT COUNT(*) FROM users WHERE email = :email AND password = :password")
  bindings = {
     "email": email,
     "password": password,
  }
  data = await session.execute(statement, bindings)
  success = data.scalar_one() == 1
  if not success:
     return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
           "userSafeErrorMessage": "The username and/or password is incorrect."
        }
     )

  # Get user id
  statement = text("SELECT id FROM users WHERE email = :email AND password = :password")
  data = await session.execute(statement, bindings)
  user_id = data.scalar_one()
  jwt = create_jwt(user_id)
  return JSONResponse(
     status_code=200,
     content={
        "accessToken": jwt,
     }
  )

@router.post("/register")
async def register():
  return {"route": "POST /register"}
