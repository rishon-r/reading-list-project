from fastapi import FastAPI
from routers import binders, reads, users # Importing all router modules

app = FastAPI() # App instance created

# Including routers
app.include_router(binders.router, prefix='/api/binders', tags=["binders"])
app.include_router(reads.router, prefix='api/reads', tags=["reads"])
app.include_router(users.router, prefix='api/users', tags=["users"])

