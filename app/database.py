from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Temporarily creating an sqlite database, will make this PostgreSQL later
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./readinglist.db" 

# Creating the engine (connection to our database)
engine = create_async_engine(
  SQLALCHEMY_DATABASE_URL,
  connect_args={"check_same_thread": False}, # This is sqllite specific because sqlite allows only one thread while fastapi allows many (don't worry too much about this)
)

# Creating our session factory which creates sessions
# Call AsyncSessionLocal() to create an actual session from the session factory
AsyncSessionLocal = async_sessionmaker(
  engine,
  class_=AsyncSession,
  expire_on_commit=False
)

# DeclarativeBase is a base class that all our ORM models will inherit from
# This tells sqlalchemy that those classes are to be considered database tables
class Base(DeclarativeBase): # In SQLAlchemy 2 we inherit from DeclarativeBase directly instead of having to do base = declarative_base()
    pass

# This is the dependency function that we will inject into each of our route handlers that require database queries
# This function provides them each with a new database session in which to run queries on
# After they have completed, control will return back to this function where clean up and closing will be run by the asynchronous context manager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
