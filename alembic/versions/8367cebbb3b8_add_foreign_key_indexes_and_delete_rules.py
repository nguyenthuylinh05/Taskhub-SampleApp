"""add foreign key indexes and delete rules

Revision ID: 8367cebbb3b8
Revises: 6f44128e9f83
Create Date: 2026-11-10 23:17:49.010628
"""

from collections.abc import Sequence

from alembic import op

revision: str = "8367cebbb3b8"
down_revision: str | Sequence[str] | None = "6f44128e9f83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Comments
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_task_id", "comments", ["task_id"])

    op.drop_constraint("comments_task_id_fkey", "comments", type_="foreignkey")
    op.drop_constraint("comments_author_id_fkey", "comments", type_="foreignkey")

    op.create_foreign_key(
        "fk_comments_author_id_users",
        "comments", "users",
        ["author_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_comments_task_id_tasks",
        "comments", "tasks",
        ["task_id"], ["id"],
        ondelete="CASCADE",
    )

    # Labels
    op.create_index("ix_labels_project_id", "labels", ["project_id"])
    op.drop_constraint("labels_project_id_fkey", "labels", type_="foreignkey")

    op.create_foreign_key(
        "fk_labels_project_id_projects",
        "labels", "projects",
        ["project_id"], ["id"],
        ondelete="CASCADE",
    )

    # Projects
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.drop_constraint(
        "projects_workspace_id_fkey", "projects", type_="foreignkey"
    )

    op.create_foreign_key(
        "fk_projects_workspace_id_workspaces",
        "projects", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )

    # Task labels
    op.create_index("ix_task_labels_label_id", "task_labels", ["label_id"])

    op.drop_constraint(
        "task_labels_label_id_fkey", "task_labels", type_="foreignkey"
    )
    op.drop_constraint(
        "task_labels_task_id_fkey", "task_labels", type_="foreignkey"
    )

    op.create_foreign_key(
        "fk_task_labels_label_id_labels",
        "task_labels", "labels",
        ["label_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_task_labels_task_id_tasks",
        "task_labels", "tasks",
        ["task_id"], ["id"],
        ondelete="CASCADE",
    )

    # Tasks
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])

    op.drop_constraint("tasks_project_id_fkey", "tasks", type_="foreignkey")
    op.drop_constraint("tasks_assignee_id_fkey", "tasks", type_="foreignkey")
    op.drop_constraint("tasks_created_by_fkey", "tasks", type_="foreignkey")

    op.create_foreign_key(
        "fk_tasks_project_id_projects",
        "tasks", "projects",
        ["project_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_tasks_created_by_users",
        "tasks", "users",
        ["created_by"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_tasks_assignee_id_users",
        "tasks", "users",
        ["assignee_id"], ["id"],
        ondelete="SET NULL",
    )

    # Workspace members
    op.create_index(
        "ix_workspace_members_user_id", "workspace_members", ["user_id"]
    )

    op.drop_constraint(
        "workspace_members_user_id_fkey",
        "workspace_members",
        type_="foreignkey",
    )
    op.drop_constraint(
        "workspace_members_workspace_id_fkey",
        "workspace_members",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "fk_workspace_members_workspace_id_workspaces",
        "workspace_members", "workspaces",
        ["workspace_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_workspace_members_user_id_users",
        "workspace_members", "users",
        ["user_id"], ["id"],
        ondelete="CASCADE",
    )

    # Workspaces
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])
    op.drop_constraint(
        "workspaces_owner_id_fkey", "workspaces", type_="foreignkey"
    )

    op.create_foreign_key(
        "fk_workspaces_owner_id_users",
        "workspaces", "users",
        ["owner_id"], ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    # Workspaces
    op.drop_constraint(
        "fk_workspaces_owner_id_users", "workspaces", type_="foreignkey"
    )
    op.create_foreign_key(
        "workspaces_owner_id_fkey",
        "workspaces", "users",
        ["owner_id"], ["id"],
    )
    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")

    # Workspace members
    op.drop_constraint(
        "fk_workspace_members_user_id_users",
        "workspace_members",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_workspace_members_workspace_id_workspaces",
        "workspace_members",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "workspace_members_workspace_id_fkey",
        "workspace_members", "workspaces",
        ["workspace_id"], ["id"],
    )
    op.create_foreign_key(
        "workspace_members_user_id_fkey",
        "workspace_members", "users",
        ["user_id"], ["id"],
    )
    op.drop_index(
        "ix_workspace_members_user_id", table_name="workspace_members"
    )

    # Tasks
    op.drop_constraint(
        "fk_tasks_assignee_id_users", "tasks", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tasks_created_by_users", "tasks", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tasks_project_id_projects", "tasks", type_="foreignkey"
    )
    op.create_foreign_key(
        "tasks_project_id_fkey",
        "tasks", "projects",
        ["project_id"], ["id"],
    )
    op.create_foreign_key(
        "tasks_assignee_id_fkey",
        "tasks", "users",
        ["assignee_id"], ["id"],
    )
    op.create_foreign_key(
        "tasks_created_by_fkey",
        "tasks", "users",
        ["created_by"], ["id"],
    )
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_index("ix_tasks_assignee_id", table_name="tasks")

    # Task labels
    op.drop_constraint(
        "fk_task_labels_task_id_tasks", "task_labels", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_task_labels_label_id_labels", "task_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "task_labels_task_id_fkey",
        "task_labels", "tasks",
        ["task_id"], ["id"],
    )
    op.create_foreign_key(
        "task_labels_label_id_fkey",
        "task_labels", "labels",
        ["label_id"], ["id"],
    )
    op.drop_index("ix_task_labels_label_id", table_name="task_labels")

    # Projects
    op.drop_constraint(
        "fk_projects_workspace_id_workspaces",
        "projects",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "projects_workspace_id_fkey",
        "projects", "workspaces",
        ["workspace_id"], ["id"],
    )
    op.drop_index("ix_projects_workspace_id", table_name="projects")

    # Labels
    op.drop_constraint(
        "fk_labels_project_id_projects", "labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "labels_project_id_fkey",
        "labels", "projects",
        ["project_id"], ["id"],
    )
    op.drop_index("ix_labels_project_id", table_name="labels")

    # Comments
    op.drop_constraint(
        "fk_comments_task_id_tasks", "comments", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_comments_author_id_users", "comments", type_="foreignkey"
    )
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments", "users",
        ["author_id"], ["id"],
    )
    op.create_foreign_key(
        "comments_task_id_fkey",
        "comments", "tasks",
        ["task_id"], ["id"],
    )
    op.drop_index("ix_comments_task_id", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
