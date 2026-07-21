from fastapi import APIRouter
from fastapi import status, Depends, HTTPException
from database import get_db
import models
from schemas import BinderCreate, BinderResponse, BinderUpdate, ReadResponse
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binder does not exist"
        )
    
    # If aa binder with this id exists but it doesn't belong to the current user
    if binder_response.user_id!=user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Binder does not exist"
        )
    
    return binder_response

# Get all reads in a binder
@router.get("/{binder_id}/reads", response_model=list[ReadResponse])
async def get_reads_in_binder(user: CurrentUser,
                        db: Annotated[AsyncSession, Depends(get_db)], 
                        binder_id: int):
    # Checking if a binder with the same id exists
    result = await db.execute(
            select(models.Binder).where(
            models.Binder.user_id == user.id,
            models.Binder.id == binder_id,
            )
        )
    existing_binder = result.scalars().first()

    if not existing_binder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Binder not found"
        )
    
    # Getting reads from that binder
    result = await db.execute(
        select(models.Read)
        .where(models.Read.binder_id == binder_id)
    )
    read_response= result.scalars().all()

    return read_response

@router.patch("/{binder_id}", response_model=BinderResponse) # corresponds to "/api/binders/{binder_id}"
async def update_binder_by_id(user: CurrentUser,
                        updated_binder: BinderUpdate,
                        db:Annotated[AsyncSession, Depends(get_db)],
                        binder_id: int):
    
    # Checking if a binder with the same id exists
    result = await db.execute(
            select(models.Binder).where(
            models.Binder.user_id == user.id,
            models.Binder.id == binder_id,
            )
        )
    existing_binder = result.scalars().first()

    if not existing_binder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Binder to be updated not found"
        )
    
    update_data = updated_binder.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(existing_binder, field, value)

    await db.commit()
    await db.refresh(existing_binder)

    return existing_binder


@router.delete("/{binder_id}", status_code=status.HTTP_204_NO_CONTENT) # corresponds to "/api/binders/{binder_id}"
async def delete_binder_by_id(user: CurrentUser,    
                        db:Annotated[AsyncSession, Depends(get_db)],
                        binder_id: int):
    # Checking if a binder with the same id exists
    result = await db.execute(
            select(models.Binder).where(
            models.Binder.user_id == user.id,
            models.Binder.id == binder_id,
            )
        )
    existing_binder = result.scalars().first()

    if not existing_binder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Binder to be deleted not found"
        )

    await db.delete(existing_binder)
    await db.commit()

