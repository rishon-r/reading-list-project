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
from tasks import scrape_read_task

router = APIRouter()

# Create a read
@router.post("", response_model=ReadResponse) # corresponds to /api/reads
async def create_read(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    read_data: ReadCreate
):
    
    # Checking if the binder that this read should go into belongs to this user
    if read_data.binder_id is not None:
        result = await db.execute(
            select(models.Binder)
            .where(models.Binder.id == read_data.binder_id,
                   models.Binder.user_id == user.id)
        )
        existing_binder = result.scalars().first()

        if not existing_binder: # if the binder does not belong to the current user, raise an error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Binder not found"
            )


    new_read = models.Read(
        user_id=user.id,
        binder_id=read_data.binder_id,
        link=read_data.link,
    )

    try:
        db.add(new_read)
        await db.commit()
        await db.refresh(new_read)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You've already saved this link"
        )
    
    try:
        # Kick off the scrape asynchronously — returns instantly, doesn't block this request
        # Dispatches the Celery task (scrape_read_task — the one from your first snippet)
        #  to run on a worker process, passing just the new row's id. .delay() is non-blocking:
        #  it enqueues a message on the broker and returns immediately, without waiting for the 
        # scrape to actually happen.
        scrape_read_task.delay(new_read.id)

    except Exception:
        # Redis/broker unreachable. The read row already exists — rather than
        # leaving it stuck at "pending" forever with no worker to pick it up,
        # mark it failed immediately so the frontend can show something actionable
        # (and the user can hit /retry once the broker's back up).
        new_read.status = "failed"
        new_read.failure_reason = "Could not queue scrape job — please try again"
        await db.commit()
        await db.refresh(new_read)

    return new_read

# Re-attempting a scrape
@router.post("/{read_id}/retry", response_model=ReadResponse)
async def retry_scrape(
    read_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    results = await db.execute(
        select(models.Read)
        .where(models.Read.id == read_id, 
               models.Read.user_id == user.id)
    )
    read = results.scalars().first()

    # If the read to be rescraped doesn't belong to current user raise exception
    if not read: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Read not found"
        )
    
    if read.status!="failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scrape has not failed"
        )
    
    # Resetting read parameters before queueing it for a scrape again
    read.status="pending"
    read.failure_reason = None

    await db.commit()
    await db.refresh(read)

    try:
        scrape_read_task.delay(read.id)
    except Exception as e:
        read.status = "failed"
        read.failure_reason = f"Could not queue scrape job: {e}"
        await db.commit()
        await db.refresh(read)

    return read

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
    
# Get a particular read
@router.get("/{read_id}", response_model=ReadResponse) # corresponds to /api/reads/{read_id}
async def get_read_by_id(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    read_id: int
):
    
    result = await db.execute(
        select(models.Read)
        .where(models.Read.user_id == user.id,
               models.Read.id == read_id)
    )

    read = result.scalars().first()

    if not read:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Read doesn't exist"
        )
    
    return read

# Update a particular read
@router.patch("/{read_id}", response_model=ReadResponse) # corresponds to /api/reads/{read_id}
async def update_read_by_id(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    read_id: int,
    updated_read: ReadUpdate
):
    result = await db.execute(
        select(models.Read)
        .where(
            models.Read.user_id==user.id,
            models.Read.id == read_id
        )
    )
    existing_read = result.scalars().first()

    if not existing_read:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Read to be updated doesn't exist"
        )
    
    update_data = updated_read.model_dump(exclude_unset=True)

    # Check to see if binder_id in update data belongs to the same user
    # This is so that the user cannot move reads to binders that don't belong to them

    if "binder_id" in update_data and update_data["binder_id"] is not None:
        result = await db.execute(
            select(models.Binder).where(
                models.Binder.id == update_data["binder_id"],
                models.Binder.user_id == user.id,
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Binder not found"
            )
            
    # Updating
    for field, value in update_data.items():
        setattr(existing_read, field, value)

    await db.commit()
    await db.refresh(existing_read)

    return existing_read
    
@router.delete("/{read_id}", status_code=status.HTTP_204_NO_CONTENT) # corresponds to /api/reads/{read_id} 
async def delete_read_by_id(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    read_id: int,
):
    
    result = await db.execute(
        select(models.Read)
        .where(
            models.Read.user_id==user.id,
            models.Read.id == read_id
        )
    )
    existing_read = result.scalars().first()

    if not existing_read:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Read to be deleted doesn't exist"
        )
    
    await db.delete(existing_read)
    await db.commit()
    