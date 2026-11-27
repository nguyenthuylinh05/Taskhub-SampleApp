from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class IntegerPrimaryKeyMixin:
    """Mixin providing an auto-incrementing integer primary key."""

    @declared_attr
    def id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
