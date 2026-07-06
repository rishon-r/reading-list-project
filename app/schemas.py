from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime

# USER SCHEMAS
class UserBase(BaseModel):
  username: str = Field(min_length=6, max_length=50)
  email: EmailStr = Field(max_length=100) # EmailStr type will automatically perform a lot of the verification checks to see if it is valid email format

# For user creation requests
class UserCreate(UserBase):
  password: str = Field(min_length=8)

# For responses seen by general public (includes no security details)
class UserPublic(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  username: str

# For responses seen by the user alone (email is visible here)
class UserPrivate(UserPublic):
  email: EmailStr

# For PATCH tyle user updates, PUT updates will typically just use UserCreate as it involves updating all fields
class UserUpdate(BaseModel):
  username: str | None = Field(default=None, min_length=6, max_length=50)
  email: EmailStr | None = Field(default=None, max_length=100)

# READ SCHEMAS
class ReadBase(BaseModel):
  title: str = Field(min_length=1, max_length=100) # title of the article
  link: str = Field(min_length=1, max_length=2048) # url to the article
  description: str = Field(min_length=1, max_length=1500) # description of what the article contains
  binder_id: int  # describes which binder this read belongs in

# This is the schema for creating reads
class ReadCreate(ReadBase):
  pass 

# Note that this should be returned everytime a read is created as well
class ReadResponse(ReadBase):
  model_config = ConfigDict(from_attributes=True)

  read_id: int
  created_time: datetime


# PATCH style update
class ReadUpdate(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=100) # title of the article
  link: str | None = Field(default=None, min_length=1, max_length=2048) # url to the article
  description: str | None = Field(default=None, min_length=1, max_length=1500) # description of what the article contains
  binder_id: int | None = Field(default=None)# describes which binder this read belongs in

# BINDER SCHEMAS
class BinderBase(BaseModel):
  binder_name: str = Field(min_length=1, max_length=50)
  binder_desc: str = Field(min_length=1, max_length=1500)
  parent_id: int | None = Field(default=None)

class BinderCreate(BinderBase):
  pass 

class BinderResponse(BinderBase):
  model_config = ConfigDict(from_attributes=True)

  binder_id: int
  created_time: datetime

# PATCH style update
class BinderUpdate(BaseModel):
  binder_name: str | None = Field(default=None, min_length=1, max_length=50)
  binder_desc: str | None = Field(default=None, min_length=1, max_length=1500)
  parent_id: int | None = Field(default=None)


# TOKEN SCHEMA
class Token(BaseModel):
  access_token: str
  token_type: str
