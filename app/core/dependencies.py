from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.comment import CommentRepository
from app.repositories.label import LabelRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthService
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService

DatabaseSessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def get_project_repository(
    session: DatabaseSessionDep,
) -> ProjectRepository:
    """Get project repository."""

    return ProjectRepository(session)


ProjectRepositoryDep = Annotated[
    ProjectRepository,
    Depends(get_project_repository),
]


def get_project_service(
    repository: ProjectRepositoryDep,
) -> ProjectService:
    """Create project service with injected repository."""

    return ProjectService(repository)


ProjectServiceDep = Annotated[
    ProjectService,
    Depends(get_project_service),
]


def get_user_repository(
    session: DatabaseSessionDep,
) -> UserRepository:
    """Get user repository."""

    return UserRepository(session)


UserRepositoryDep = Annotated[
    UserRepository,
    Depends(get_user_repository),
]


def get_auth_service(
    repository: UserRepositoryDep,
) -> AuthService:
    """Get authentication service."""

    return AuthService(repository)


AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]


def get_workspace_repository(
    session: DatabaseSessionDep,
) -> WorkspaceRepository:
    """Get workspace repository."""

    return WorkspaceRepository(session)


WorkspaceRepositoryDep = Annotated[
    WorkspaceRepository,
    Depends(get_workspace_repository),
]


def get_workspace_service(
    workspace_repository: WorkspaceRepositoryDep,
    user_repository: UserRepositoryDep,
) -> WorkspaceService:
    """Create workspace service with injected repositories."""

    return WorkspaceService(
        workspace_repository=workspace_repository,
        user_repository=user_repository,
    )


WorkspaceServiceDep = Annotated[
    WorkspaceService,
    Depends(get_workspace_service),
]


def get_task_repository(
    session: DatabaseSessionDep,
) -> TaskRepository:
    """Get task repository."""

    return TaskRepository(session)


TaskRepositoryDep = Annotated[
    TaskRepository,
    Depends(get_task_repository),
]


def get_label_repository(
    session: DatabaseSessionDep,
) -> LabelRepository:
    """Get label repository."""

    return LabelRepository(session)


LabelRepositoryDep = Annotated[
    LabelRepository,
    Depends(get_label_repository),
]


def get_comment_repository(
    session: DatabaseSessionDep,
) -> CommentRepository:
    """Get comment repository."""

    return CommentRepository(session)


CommentRepositoryDep = Annotated[
    CommentRepository,
    Depends(get_comment_repository),
]
