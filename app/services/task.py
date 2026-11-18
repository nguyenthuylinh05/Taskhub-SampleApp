"""Business logic for task operations."""

from app.core.exceptions import (
    InvalidOperation,
    NotFoundException,
    PermissionDenied,
)
from app.core.messages import (
    PROJECT_ARCHIVED,
    PROJECT_NOT_FOUND,
    TASK_ASSIGNEE_MUST_HAVE_WRITE_ACCESS,
    TASK_ASSIGNEE_NOT_IN_WORKSPACE,
    TASK_NOT_FOUND,
    USER_NOT_FOUND,
)
from app.models.enums import (
    ProjectStatus,
    TaskPriority,
    TaskStatus,
    WorkspaceRole,
)
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.pagination import Pagination
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.workspace_access import resolve_workspace_access


class TaskService:
    """Business logic for task operations."""

    def __init__(
        self,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        user_repository: UserRepository,
    ) -> None:
        self.task_repository = task_repository
        self.project_repository = project_repository
        self.workspace_repository = workspace_repository
        self.user_repository = user_repository

    async def _get_project_and_workspace(
        self,
        project_id: int,
        current_user: User,
        require_editor: bool = False,
    ) -> tuple[Project, Workspace]:
        """Get a project and resolve the current user's workspace access."""

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
        """Prevent task modifications in archived projects."""

        if project.status == ProjectStatus.ARCHIVED:
            raise InvalidOperation(PROJECT_ARCHIVED)

    async def _validate_assignee(
        self,
        workspace: Workspace,
        assignee_id: int,
    ) -> None:
        """Ensure the assignee is an eligible workspace member."""

        assignee = await self.user_repository.get_by_id(assignee_id)

        if assignee is None:
            raise NotFoundException(USER_NOT_FOUND)

        # Workspace owners do not need a membership record.
        if assignee_id == workspace.owner_id:
            return

        role = await self.workspace_repository.get_member(
            workspace.id,
            assignee_id,
        )

        if role is None:
            raise InvalidOperation(TASK_ASSIGNEE_NOT_IN_WORKSPACE)

        if role not in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR):
            raise InvalidOperation(TASK_ASSIGNEE_MUST_HAVE_WRITE_ACCESS)

    async def create_task(
        self,
        project_id: int,
        data: TaskCreate,
        current_user: User,
    ) -> TaskResponse:
        """Create a task in an active project."""

        project, workspace = await self._get_project_and_workspace(
            project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)

        if data.assignee_id is not None:
            await self._validate_assignee(workspace, data.assignee_id)

        task = await self.task_repository.create(
            {
                **data.model_dump(),
                "project_id": project_id,
                "created_by": current_user.id,
            }
        )

        return TaskResponse.model_validate(task)

    async def get_tasks(
        self,
        project_id: int,
        current_user: User,
        pagination: Pagination,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
    ) -> TaskListResponse:
        """Get filtered and paginated tasks in a project."""

        await self._get_project_and_workspace(project_id, current_user)

        tasks, total = await self.task_repository.get_filtered_by_project(
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            page=pagination.page,
            limit=pagination.limit,
        )

        return TaskListResponse(
            items=[
                TaskResponse.model_validate(task)
                for task in tasks
            ],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def update_task(
        self,
        task_id: int,
        data: TaskUpdate,
        current_user: User,
    ) -> TaskResponse:
        """Update a task in an active project."""

        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        project, workspace = await self._get_project_and_workspace(
            task.project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)

        update_data = data.model_dump(exclude_unset=True)

        if (
            "assignee_id" in update_data
            and update_data["assignee_id"] is not None
        ):
            await self._validate_assignee(
                workspace,
                update_data["assignee_id"],
            )

        updated_task = await self.task_repository.update_entity(
            task,
            update_data,
        )

        return TaskResponse.model_validate(updated_task)

    async def delete_task(
        self,
        task_id: int,
        current_user: User,
    ) -> None:
        """Delete a task from an active project."""

        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        project, _ = await self._get_project_and_workspace(
            task.project_id,
            current_user,
            require_editor=True,
        )
        self._ensure_project_active(project)

        await self.task_repository.delete_entity(task)