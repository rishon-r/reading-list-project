from __future__ import annotations # Required for forward references on versions older than Python 3.14
from sqlalchemy import DateTime, ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import datetime, UTC


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
  email: Mapped[str]= mapped_column(String(100), unique=True, nullable=False)
  password_hash: Mapped[str] = mapped_column(String(100), nullable=False)

  reads: Mapped[list[Read]] = relationship(back_populates="author")
  binders: Mapped[list[Binder]] = relationship(back_populates="author")

class Read(Base):
  __tablename__ = "reads"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  title: Mapped[str]= mapped_column(String(100), nullable=False)
  link: Mapped[str] = mapped_column(String(2048), nullable=False)
  description: Mapped[str] = mapped_column(String(1500))
  time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  binder_id: Mapped[int] = mapped_column(ForeignKey("binders.id"), nullable=False, index=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

  author: Mapped[User] = relationship(back_populates="reads")

  binder: Mapped[Binder] = relationship(back_populates="reads")

class Binder(Base):
  __tablename__ = "binders"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  name: Mapped[str]= mapped_column(String(100), nullable=False)
  description: Mapped[str] = mapped_column(String(1500))
  time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
  parent_id: Mapped[int | None] = mapped_column(ForeignKey("binders.id"))

  author: Mapped[User] = relationship(back_populates="binders")

  reads: Mapped[list[Read]] = relationship(back_populates="binder")

  # remote_side is specifically needed for self-referential relationships — where a table has a foreign key pointing back to itself
  parent: Mapped[Binder | None] = relationship(back_populates="children", remote_side="Binder.id")
  children: Mapped[list[Binder]] = relationship(back_populates="parent")
