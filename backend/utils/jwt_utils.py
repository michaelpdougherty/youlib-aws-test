from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
import datetime
import jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
security = HTTPBearer()

def create_jwt(user_id):
  payload = {
      "sub": str(user_id),
      "iat": datetime.datetime.utcnow()
      # TODO: no 'exp' claim
  }
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  return token

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
            # Todo add userSafeErrorMessage when you learn how this gets passed as an API response
        )