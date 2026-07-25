from fastapi import FastAPI
from routers import binders, reads, users # Importing all router modules from fastapi import HTTPException, status, Request

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from contextlib import asynccontextmanager
from database import engine, Base

from fastapi import Request

from fastapi.middleware.cors import CORSMiddleware # for CORS

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
app.include_router(users.router, prefix='/api/auth', tags=["users"])

# base route
@app.get("/")
def landing_page():
  return {"text": "landing page"}

# CORS
'''
Cross-Origin Resource Sharing. 
Browsers block JavaScript running on one origin 
(e.g. http://localhost:5173, your future Vite dev server) 
from making requests to a different origin (e.g. http://localhost:8000, your FastAPI server) 
unless the server explicitly says it's allowed to, via specific response headers. 
This is a browser security feature, not something Python/FastAPI does by default — 
without it, every fetch() call from your React app will fail with a CORS error
in the browser console, even though the request would work fine from curl or Swagger docs (/docs),
since those don't enforce the browser's same-origin policy.

Below code is essentially allowing the Vite server to explicitly make calls to the fastAPI app

allow_origins is a strict allowlist — 
only origins listed here can call your API from a browser. 
Using ["*"] (allow everything) is tempting for local dev but should never be combined
with allow_credentials=True (browsers will reject that combination outright for security reasons, 
and it's also just bad practice). Keep it to your exact dev URL for now,
and add your production frontend URL later once deployed

allow_credentials=True matters because the app uses JWT Bearer tokens — 
if you ever switch to httpOnly cookies instead of Authorization headers,
this becomes mandatory for cookies to be sent cross-origin.
With Bearer tokens in headers (your current setup) it's not strictly required,
but it's harmless to include and future-proofs you.

allow_methods=["*"] and allow_headers=["*"] are fine for a personal project; a production app
would typically restrict these to exactly
what's needed (GET, POST, PATCH, DELETE and Authorization, Content-Type
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# EXCEPTION HANDLERS (For now returns default behaviour but functions are placed in case we want to modify exception handling for particular routes)
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
  return await http_exception_handler(request, exception)
   
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
  return await request_validation_exception_handler(request, exception)