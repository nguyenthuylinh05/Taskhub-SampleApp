from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import WorkspaceRole

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


workspace_members = Table(
    "workspace_members",
    Base.metadata,
    Column(
        "workspace_id",
        Integer,
        ForeignKey("workspaces.id"),
        primary_key=True,
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id"),
        primary_key=True,
    ),
    Column(
        "role",
        Enum(WorkspaceRole, name="workspace_role"),
        nullable=False,
    ),
)


class Workspace(Base):
    """Workspace model."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    owner: Mapped["User"] = relationship(
        back_populates="owned_workspaces",
        foreign_keys=[owner_id],
    )

    members: Mapped[list["User"]] = relationship(
        secondary=workspace_members,
        back_populates="member_workspaces",
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="workspace",
    )
