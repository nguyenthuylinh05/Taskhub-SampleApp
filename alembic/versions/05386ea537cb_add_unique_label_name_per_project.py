"""add unique label name per project

Revision ID: 05386ea537cb
Revises: 8367cebbb3b8
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "05386ea537cb"
down_revision: str | Sequence[str] | None = "8367cebbb3b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LABEL_PROJECT_NAME_CONSTRAINT = "uq_labels_project_id_name"


def upgrade() -> None:
    """Add project-scoped label-name uniqueness without changing existing data."""
    bind = op.get_bind()
    duplicate_groups = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT project_id, name
                FROM labels
                GROUP BY project_id, name
                HAVING COUNT(*) > 1
            ) AS duplicate_labels
            """
        )
    ).scalar_one()

    if duplicate_groups:
        raise RuntimeError(
            "Cannot add uq_labels_project_id_name: "
            f"found {duplicate_groups} duplicate (project_id, name) groups. "
            "Resolve the duplicates manually before upgrading."
        )

    op.create_unique_constraint(
        LABEL_PROJECT_NAME_CONSTRAINT,
        "labels",
        ["project_id", "name"],
    )


def downgrade() -> None:
    """Remove project-scoped label-name uniqueness."""
    op.drop_constraint(
        LABEL_PROJECT_NAME_CONSTRAINT,
        "labels",
        type_="unique",
    )
