from fastapi import APIRouter
from fastapi import status, Depends, HTTPException
from database import get_db
import models
from schemas import BinderCreate, BinderResponse, BinderUpdate
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Annotated
from auth import CurrentUser

router = APIRouter()

@router.get("", response_model=list[BinderResponse]) # corresponds to "/api/binders"
async def display_all_binders(user: CurrentUser,
                        db:Annotated[AsyncSession, Depends(get_db)]):
    
    result = await db.execute(select(models.Binder).where(models.Binder.user_id == user.id))
    binders = result.scalars().all()

    return binders

@router.post("", response_model=BinderResponse) # corresponds to "/api/binders"
async def create_binder(new_binder: BinderCreate,
                  user: CurrentUser,
                   db:Annotated[AsyncSession, Depends(get_db)]):
    
    # Checking if a binder with the same name exists
    result = await db.execute(
            select(models.Binder).where(
            models.Binder.user_id == user.id,
            func.lower(models.Binder.name) == new_binder.name.lower(),
            )
        )
    existing_binder = result.scalars().first()

    if existing_binder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Binder with same name exists"
            )
    binder = models.Binder(
        **new_binder.model_dump(exclude_none=True),
        user_id=user.id,
    )

    db.add(binder)
    await db.commit()
    await db.refresh(binder)

    return binder


@router.get("/{binder_id}", response_model=BinderResponse) # corresponds to "/api/binders/{binder_id}"
async def diplay_binder_by_id(user: CurrentUser,
                        db:Annotated[AsyncSession, Depends(get_db)],
                        binder_id: int):
    
    result = await db.execute(
        select(models.Binder)
        .where(models.Binder.id == binder_id)
    )
    binder_response = result.scalars().first()

    # If no binder with this id exists
    if not binder_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Binder does not exist"
        )
    
    # If aa binder with this id exists but it doesn't belong to the current user
    if binder_response.user_id!=user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Binder does not exist"
        )
    
    return binder_response

@router.patch("/{binder_id}") # corresponds to "/api/binders/{binder_id}"
def update_binder_by_id(user: CurrentUser,
                        updated_binder: BinderUpdate,
                        db:Annotated[AsyncSession, Depends(get_db)],
                        binder_id: int):
    pass

@router.delete("/{binder_id}") # corresponds to "/api/binders/{binder_id}"
def delete_binder_by_id(user: CurrentUser,
                        db:Annotated[AsyncSession, Depends(get_db)],
                        binder_id: int):
    pass

