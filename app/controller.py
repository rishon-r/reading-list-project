from fastapi import FastAPI
from routers import binders, reads, users # Importing all router modules
from fastapi import HTTPException, status, Request

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from contextlib import asynccontextmanager
from database import engine, Base

# For setup and teardown
@asynccontextmanager
async def lifespan(_app: FastAPI):
  # Creating all tables (SETUP)
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  yield

  # (TEARDOWN)
  await engine.dispose()



app = FastAPI(lifespan=lifespan) # App instance created

# Including routers
app.include_router(binders.router, prefix='/api/binders', tags=["binders"])
app.include_router(reads.router, prefix='/api/reads', tags=["reads"])
app.include_router(users.router, prefix='/api/users', tags=["users"])

# base route
@app.get("/")
def landing_page():
  return {"text": "landing page"}


# EXCEPTION HANDLERS (For now returns default behaviour but functions are placed in case we want to modify exception handling for particular routes)
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
  return await http_exception_handler(request, exception)
   
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
  return await request_validation_exception_handler(request, exception)