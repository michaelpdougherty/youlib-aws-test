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
async def register(user_registration: UserRegistration, session: AsyncSession = Depends(get_session)):
  # get email
  # TODO validate email
  email = user_registration.email

  # get password
  # TODO validate password
  password = user_registration.password

  # get name
  first_name = user_registration.firstName
  last_name = user_registration.lastName

  # get zip code
  zip_code = user_registration.zipCode

  # get library name
  library_name = user_registration.libraryName

  statement = text("SELECT COUNT(*) FROM users WHERE email = :email")
  data = await session.execute(statement, {"email": email})
  result = data.scalar_one()  # returns the scalar value directly
  if result > 0:
     return JSONResponse(
        status_code=400,
        content={
          "userSafeErrorMessage": "A user with this email already exists. Please sign in."
        }
     )
  # TODO add password hashing
  statement = text("INSERT INTO users (email, password, first_name, last_name, zip_code, library_name) VALUES (:email, :password, :first_name, :last_name, :zip_code, :library_name)")
  await session.execute(
    statement,
    {
      "email": email,
      "password": password,
      "first_name": first_name,
      "last_name": last_name,
      "zip_code": zip_code,
      "library_name": library_name,
    }
  )
  await session.commit()

  # get user ID and generate access token
  statement = text("SELECT id FROM users WHERE email = :email AND password = :password")
  data = await session.execute(statement, { "email": email, "password": password })
  user_id = data.scalar_one()
  jwt = create_jwt(user_id)
  
  content = {
    "email": email,
    "firstName": first_name,
    "lastName": last_name,
    "zipCode": zip_code,
    "libraryName": library_name,
    "token": jwt,
  }

  return JSONResponse(
    status_code=200,
    content=content,
  )
