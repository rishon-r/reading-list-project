from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime

# USER SCHEMAS
class UserBase(BaseModel):
  email: EmailStr = Field(max_length=100) # EmailStr type will automatically perform a lot of the verification checks to see if it is valid email format

# For user creation requests
class UserCreate(UserBase):
  password: str = Field(min_length=8)

# For responses seen by general public (includes no security details)
class UserPublic(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int

# For responses seen by the user alone (email is visible here)
class UserPrivate(UserPublic):
  email: EmailStr

# For PATCH tyle user updates, PUT updates will typically just use UserCreate as it involves updating all fields
class UserUpdate(BaseModel):
  email: EmailStr | None = Field(default=None, max_length=100)

# READ SCHEMAS

# Only the link is required at creation time — everything else
# (title, description, author, etc.) is filled in later by the scraper.
class ReadBase(BaseModel):
  link: str = Field(min_length=1, max_length=2048) # url to the article
  binder_id: int  # describes which binder this read belongs in

# This is the schema for creating reads
class ReadCreate(ReadBase):
  pass 

# Note that this should be returned everytime a read is created as well
class ReadResponse(ReadBase):
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: int
  status: str
  title: str | None
  description: str | None
  author: str | None
  published_at: datetime | None
  hero_image_url: str | None
  content_html: str | None
  reading_time_minutes: int | None
  is_read: bool
  failure_reason: str | None
  time_created: datetime
  scraped_at: datetime | None

# PATCH-style update — only user-controlled fields.
# title/description/author/etc. are scraper-owned and not user-editable.
class ReadUpdate(BaseModel):
  is_read: bool | None = Field(default=None)
  binder_id: int | None = Field(default=None)

# BINDER SCHEMAS
class BinderBase(BaseModel):
  name: str = Field(min_length=1, max_length=100)
  parent_id: int | None = Field(default=None)

class BinderCreate(BinderBase):
  description: str | None = Field(default=None, min_length=1, max_length=1500)

class BinderResponse(BinderBase):
  model_config = ConfigDict(from_attributes=True)

  id: int
  user_id: int
  description: str
  time_created: datetime

# PATCH style update
class BinderUpdate(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=100)
  description: str | None = Field(default=None, min_length=1, max_length=1500)
  parent_id: int | None = Field(default=None)


# TOKEN SCHEMA
class Token(BaseModel):
  access_token: str
  token_type: str
