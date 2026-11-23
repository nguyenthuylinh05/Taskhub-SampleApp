"""Business logic for project labels and task-label associations."""

from app.core.exceptions import (
    ConflictError,
    InvalidOperation,
    NotFoundException,
    PermissionDenied,
)
from app.core.messages import PROJECT_ARCHIVED, PROJECT_NOT_FOUND, TASK_NOT_FOUND
from app.models import Label, Project, User, Workspace, WorkspaceRole
from app.models.enums import ProjectStatus
from app.repositories.label import LabelRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.services.workspace_access import resolve_workspace_access


class LabelService:
    """Coordinate label persistence and workspace authorization."""

    def __init__(
        self,
        label_repository: LabelRepository,
        project_repository: ProjectRepository,
        task_repository: TaskRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self.label_repository = label_repository
        self.project_repository = project_repository
        self.task_repository = task_repository
        self.workspace_repository = workspace_repository

    async def _get_project_access(
        self,
        project_id: int,
        current_user: User,
        require_editor: bool = False,
    ) -> tuple[Project, Workspace]:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)

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
        return project, access.workspace

    @staticmethod
    def _ensure_project_active(project: Project) -> None:
        if project.status == ProjectStatus.ARCHIVED:
            raise InvalidOperation(PROJECT_ARCHIVED)

    async def _get_label(self, label_id: int) -> Label:
        label = await self.label_repository.get_by_id(label_id)
        if label is None:
            raise NotFoundException("Label not found")
        return label

    async def create_label(
        self,
        project_id: int,
        data: LabelCreate,
        current_user: User,
    ) -> LabelResponse:
        project, _ = await self._get_project_access(
            project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
        label = await self.label_repository.create(
            {**data.model_dump(), "project_id": project_id}
        )
        return LabelResponse.model_validate(label)

    async def get_labels(
        self,
        project_id: int,
        current_user: User,
    ) -> list[LabelResponse]:
        await self._get_project_access(project_id, current_user)
        labels = await self.label_repository.get_by_project(project_id)
        return [LabelResponse.model_validate(label) for label in labels]

    async def get_label(
        self,
        label_id: int,
        current_user: User,
    ) -> LabelResponse:
        label = await self._get_label(label_id)
        await self._get_project_access(label.project_id, current_user)
        return LabelResponse.model_validate(label)

    async def update_label(
        self,
        label_id: int,
        data: LabelUpdate,
        current_user: User,
    ) -> LabelResponse:
        label = await self._get_label(label_id)
        project, _ = await self._get_project_access(
            label.project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
        updated = await self.label_repository.update_entity(
            label,
            data.model_dump(exclude_unset=True),
        )
        return LabelResponse.model_validate(updated)

    async def delete_label(
        self,
        label_id: int,
        current_user: User,
    ) -> None:
        label = await self._get_label(label_id)
        project, _ = await self._get_project_access(
            label.project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
        await self.label_repository.delete_entity(label)

    async def _get_task_and_authorize_write(
        self,
        task_id: int,
        current_user: User,
    ) -> tuple[int, int]:
        task = await self.task_repository.get_by_id(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        project, _ = await self._get_project_access(
            task.project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)
        return task.project_id, task.id

    async def assign_label(
        self,
        task_id: int,
        label_id: int,
        current_user: User,
    ) -> None:
        task_project_id, _ = await self._get_task_and_authorize_write(
            task_id,
            current_user,
        )
        label = await self._get_label(label_id)
        if label.project_id != task_project_id:
            raise InvalidOperation(
                "Task and label must belong to the same project"
            )
        inserted = await self.label_repository.assign_to_task(task_id, label_id)
        if not inserted:
            raise ConflictError("Label is already assigned to this task")

    async def remove_label(
        self,
        task_id: int,
        label_id: int,
        current_user: User,
    ) -> None:
        task_project_id, _ = await self._get_task_and_authorize_write(
            task_id,
            current_user,
        )
        label = await self._get_label(label_id)
        if label.project_id != task_project_id:
            raise InvalidOperation(
                "Task and label must belong to the same project"
            )
        await self.label_repository.remove_from_task(task_id, label_id)
