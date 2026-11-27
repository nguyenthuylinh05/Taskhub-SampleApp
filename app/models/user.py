from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.MEMBER,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    owned_workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="owner",
        foreign_keys="Workspace.owner_id",
        passive_deletes="all",
    )

    member_workspaces: Mapped[list["Workspace"]] = relationship(
        secondary="workspace_members",
        back_populates="members",
        passive_deletes=True,
    )
