from datetime import UTC, datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import models
from database import get_db

password_hash = PasswordHash.recommended() # Creates a password hash with argon2 using the recommended settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/token")

def hash_password(password: str) -> str:
  return password_hash.hash(password) # Returns Hashed password. Note: We never store plain passwords in database, only hashed ones

def verify_password(plain_password: str, hashed_password: str) -> bool:
  return password_hash.verify(plain_password, hashed_password) # Checks if plain password is same as hashed password

def create_access_token(data: dict, expires_delta: timedelta | None):
  # NOTE: `data` should contain {"sub": str(user.id)} — sub must be a string
  # per the JWT spec. get_current_user() calls int(sub) after decoding, so
  # passing a raw int here can cause inconsistent behavior across JWT libraries.
  
  to_encode = data.copy()

  if expires_delta:
    expire = datetime.now(UTC) + expires_delta
  else: 
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expires_minutes)

  to_encode.update({"exp": expire})

  encoded_jwt = jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm)

  return encoded_jwt

def verify_access_token(token: str) -> str | None:
  try:

    payload = jwt.decode(
      token,
      settings.secret_key.get_secret_value(),
      algorithms=[settings.algorithm],
      options={"require": ["exp", "sub"]}
      )
  except jwt.InvalidTokenError:
    return None
  else:
    return payload.get("sub") # sub contains the user_id

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]) -> models.User:
  
  user_id = verify_access_token(token)

  if user_id is None: # means token is invalid
    raise HTTPException(
      status_code = status.HTTP_401_UNAUTHORIZED,
      detail= "Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  try:
    user_id_int = int(user_id)

  except (TypeError, ValueError): # If token is not of the appropriate type integer
      raise HTTPException(
      status_code = status.HTTP_401_UNAUTHORIZED,
      detail= "Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  result = await db.execute(select(models.User).where(models.User.id == user_id_int))

  user = result.scalars().first()

  if not user: # If verify_access_token(0 runs successfully and user_id is of form int but there exists no user pertaining to that id in database
    raise HTTPException(
      status_code = status.HTTP_401_UNAUTHORIZED,
      detail= "User Not Found",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  return user # returns the current user

# TYPE ANNOTATION to add to function definitions
CurrentUser = Annotated[models.User, Depends(get_current_user)]



