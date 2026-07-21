from fastapi import APIRouter
from fastapi import HTTPException, status, Depends
from schemas import ReadCreate, ReadResponse, ReadUpdate
from auth import CurrentUser
from database import get_db
import models
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

# Create a read
@router.post("", response_model=ReadResponse) # corresponds to /api/reads
async def create_read(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    read_data: ReadCreate
):
    if read_data.binder_id is not None:
        result = await db.execute(
            select(models.Binder)
            .where(models.Binder.id == read_data.binder_id, 
                   models.Binder.user_id==user.id)
            )
        existing_binder = result.scalars().first()


        if not existing_binder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Binder not found"
            )
        
    new_read = models.Read(
        user_id=user.id,
        binder_id=read_data.binder_id,
        link= read_data.link

    )

    try:
        db.add(new_read)
        await db.commit()
        await db.refresh(new_read)

        return new_read
    
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You've already saved this link"
        )   
    
# View all reads
@router.get("", response_model=list[ReadResponse]) # corresponds to /api/reads
async def display_all_reads(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Read)
        .where(models.Read.user_id == user.id)
    )
    reads = result.scalars().all()

    return reads
    

    