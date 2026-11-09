from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


task_labels = Table(
    "task_labels",
    Base.metadata,
    Column(
        "task_id",
        Integer,
        ForeignKey("tasks.id"),
        primary_key=True,
    ),
    Column(
        "label_id",
        Integer,
        ForeignKey("labels.id"),
        primary_key=True,
    ),
)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    color: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(
        back_populates="labels",
    )

    tasks: Mapped[list["Task"]] = relationship(
        secondary=task_labels,
        back_populates="labels",
    )
