"""Business logic for task comments."""

from app.core.exceptions import InvalidOperation, NotFoundException, PermissionDenied
from app.core.messages import PROJECT_ARCHIVED, TASK_NOT_FOUND
from app.models import Project, User, WorkspaceRole
from app.models.enums import ProjectStatus
from app.repositories.comment import CommentRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.workspace_access import resolve_workspace_access


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
    ) -> tuple[int, Project]:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        project = await self.project_repository.get_by_id(task.project_id)
        if project is None:
            raise NotFoundException("Project not found")

        access = await resolve_workspace_access(
            project.workspace_id,
            current_user,
            self.workspace_repository,
        )
        if require_editor and access.role not in (
            WorkspaceRole.OWNER,
            WorkspaceRole.EDITOR,
        ):
            raise PermissionDenied()
        return task.id, project

    @staticmethod
    def _ensure_project_active(project: Project) -> None:
        if project.status == ProjectStatus.ARCHIVED:
            raise InvalidOperation(PROJECT_ARCHIVED)

    async def create_comment(
        self,
        task_id: int,
        data: CommentCreate,
        current_user: User,
    ) -> CommentResponse:
        authorized_task_id, project = await self._get_task_and_authorize(
            task_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
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
    ) -> list[CommentResponse]:
        authorized_task_id, _ = await self._get_task_and_authorize(
            task_id,
            current_user,
        )
        comments = await self.comment_repository.get_by_task(authorized_task_id)
        return [CommentResponse.model_validate(item) for item in comments]

    async def delete_comment(
        self,
        comment_id: int,
        current_user: User,
    ) -> None:
        comment = await self.comment_repository.get_by_id(comment_id)
        if comment is None:
            raise NotFoundException("Comment not found")

        _, project = await self._get_task_and_authorize(
            comment.task_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
        await self.comment_repository.delete_entity(comment)
