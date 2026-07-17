from fastapi import APIRouter
from schemas import Token, UserCreate, UserPrivate, UserUpdate, UserPublic
from fastapi import status, Depends, HTTPException
from database import get_db
import models
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from config import settings
from auth import create_access_token, hash_password, verify_password, CurrentUser
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta


router = APIRouter()

# ROUTES

# CREATING A USER
@router.post("/register", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
  
  # Checking if user with the same email already exists
  result = await db.execute(
    select(models.User).where(func.lower(models.User.email)==user.email.lower())
  )
  existing_email = result.scalars().first()

  if existing_email:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail = "User with given email already exists"
    )
  
  new_user = models.User(
    email=user.email.lower(),
    hashed_password=hash_password(user.password)
  )

  db.add(new_user)

  await db.commit()
  await db.refresh(new_user)

  return new_user

# LOGIN FUNCTION
@router.post("/login", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Annotated[AsyncSession, Depends(get_db)]
):
  result = await db.execute(
     select(models.User).where(models.User.email==form_data.username)
  )
  user = result.scalars().first()

  # Check to see if user exists and password matches
  if not user or not verify_password(form_data.password, user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail = "Invalid Email or Password",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  # Creating access token in the case of successful log in
  access_token_expires = timedelta(minutes=settings.access_token_expires_minutes)
  access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
  return Token(access_token=access_token, token_type="bearer")

# READING/RETURNING CURRENTLY AUTHENTICATED USER
@router.get("/me", response_model=UserPublic)
async def get_current_user(user: CurrentUser):
  return user

# UPDATING A USER
@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int,
                 updated_user: UserUpdate,
                 current_user: CurrentUser,
                 db: Annotated[AsyncSession, Depends(get_db)]
                 ):
  
  # A user can only update themselves and not other random users
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="NOt allows to update this user"
    )
  
  # Checking if a user with the given id exists
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
  
  # Check if new email exists in database
  if updated_user.email and user.email.lower()!=updated_user.email.lower():
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == updated_user.email.lower())
        )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with new email already exists",
        )
  # Updating email
  if updated_user.email:
    user.email = updated_user.email

  await db.commit()
  await db.refresh(user)

  return user

# DELETING A USER
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
  user_id: int,
  current_user: CurrentUser,
  db: Annotated[AsyncSession, Depends(get_db)],
):
  
  # Checking if user to be deleted is current user (User can only delete themselves)
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail= "Not permitted to delete this user"
    )
  
  result = await db.execute(select(models.User).where(models.User.id == user_id))
  user = result.scalars().first()
  if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
  
  await db.delete(user) 
  await db.commit()
  
 




    
  
  

  






