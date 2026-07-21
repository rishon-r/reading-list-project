from __future__ import annotations # Required for forward references on versions older than Python 3.14
from sqlalchemy import DateTime, ForeignKey, String, Integer, Text, CheckConstraint, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import datetime, UTC


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
  email: Mapped[str]= mapped_column(String(100), unique=True, nullable=False)
  hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
  time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  reads: Mapped[list[Read]] = relationship(back_populates="user")
  binders: Mapped[list[Binder]] = relationship(back_populates="user")

class Read(Base):
  __tablename__ = "reads"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  binder_id: Mapped[int | None] = mapped_column(ForeignKey("binders.id"), nullable=True, index=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
  link: Mapped[str] = mapped_column(Text, nullable=False)
  status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
  title: Mapped[str | None]= mapped_column(String(500), nullable=True)
  description: Mapped[str | None] = mapped_column(Text, nullable=True)
  author: Mapped[str | None] = mapped_column(String(255), nullable=True)
  published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  hero_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
  content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
  reading_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
  is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
  failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
  time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
  scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

  user: Mapped[User] = relationship(back_populates="reads")
  binder: Mapped[Binder | None] = relationship(back_populates="reads")

  __table_args__ = (
    CheckConstraint("status IN ('pending','scraping','ready','failed')"),
    UniqueConstraint("user_id", "link", name="uq_user_link"),
  )

class Binder(Base):
  __tablename__ = "binders"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  name: Mapped[str]= mapped_column(String(100), nullable=False)
  description: Mapped[str] = mapped_column(String(1500), default="No description")
  time_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
  parent_id: Mapped[int | None] = mapped_column(ForeignKey("binders.id"))

  user: Mapped[User] = relationship(back_populates="binders")

  reads: Mapped[list[Read]] = relationship(back_populates="binder")

  # remote_side is specifically needed for self-referential relationships — where a table has a foreign key pointing back to itself
  parent: Mapped[Binder | None] = relationship(back_populates="children", remote_side="Binder.id")
  children: Mapped[list[Binder]] = relationship(back_populates="parent")

