"""Business logic for task comments."""

from app.core.exceptions import NotFoundException, PermissionDenied
from app.core.messages import COMMENT_NOT_FOUND, TASK_NOT_FOUND
from app.models import Project, User
from app.models.enums import WorkspaceRole
from app.repositories.comment import CommentRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.schemas.pagination import Pagination
from app.services.workspace_access import (
    WorkspaceAccess,
    ensure_project_active,
    resolve_project_access,
)


class CommentService:
    """Coordinate comment persistence and workspace authorization."""

    def __init__(
        self,
        comment_repository: CommentRepository,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self.comment_repository = comment_repository
        self.task_repository = task_repository
        self.project_repository = project_repository
        self.workspace_repository = workspace_repository

    async def _get_task_and_authorize(
        self,
        task_id: int,
        current_user: User,
        require_editor: bool = False,
        inaccessible_message: str = TASK_NOT_FOUND,
    ) -> tuple[int, Project, WorkspaceAccess]:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise NotFoundException(inaccessible_message)

        project, access = await resolve_project_access(
            task.project_id,
            current_user,
            self.project_repository,
            self.workspace_repository,
            require_write=require_editor,
            not_found_message=inaccessible_message,
            inaccessible_message=inaccessible_message,
        )
        return task.id, project, access

    async def create_comment(
        self,
        task_id: int,
        data: CommentCreate,
        current_user: User,
    ) -> CommentResponse:
        authorized_task_id, project, _ = await self._get_task_and_authorize(
            task_id,
            current_user,
            require_editor=True,
        )
        ensure_project_active(project)
        comment = await self.comment_repository.create(
            {
                "task_id": authorized_task_id,
                "author_id": current_user.id,
                "content": data.content,
            }
        )
        return CommentResponse.model_validate(comment)

    async def get_comments(
        self,
        task_id: int,
        current_user: User,
        pagination: Pagination,
    ) -> CommentListResponse:
        authorized_task_id, _, _ = await self._get_task_and_authorize(
            task_id,
            current_user,
        )
        comments, total = await self.comment_repository.get_by_task(
            authorized_task_id,
            pagination,
        )
        return CommentListResponse(
            items=[CommentResponse.model_validate(item) for item in comments],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def update_comment(
        self,
        comment_id: int,
        data: CommentUpdate,
        current_user: User,
    ) -> CommentResponse:
        comment = await self.comment_repository.get_by_id(comment_id)
        if comment is None:
            raise NotFoundException(COMMENT_NOT_FOUND)

        _, project, _ = await self._get_task_and_authorize(
            comment.task_id,
            current_user,
            inaccessible_message=COMMENT_NOT_FOUND,
        )
        ensure_project_active(project)
        if comment.author_id != current_user.id:
            raise PermissionDenied()

        updated = await self.comment_repository.update_entity(
            comment,
            data.model_dump(exclude_unset=True),
        )
        return CommentResponse.model_validate(updated)

    async def delete_comment(
        self,
        comment_id: int,
        current_user: User,
    ) -> None:
        comment = await self.comment_repository.get_by_id(comment_id)
        if comment is None:
            raise NotFoundException(COMMENT_NOT_FOUND)

        _, project, access = await self._get_task_and_authorize(
            comment.task_id,
            current_user,
            inaccessible_message=COMMENT_NOT_FOUND,
        )
        if comment.author_id != current_user.id and access.role != WorkspaceRole.OWNER:
            raise PermissionDenied()
        ensure_project_active(project)
        await self.comment_repository.delete_entity(comment)
