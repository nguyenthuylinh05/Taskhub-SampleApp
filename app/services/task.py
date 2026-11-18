"""Business logic for task operations."""

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_LIMIT
from app.core.exceptions import (
    InvalidOperation,
    NotFoundException,
    PermissionDenied,
)
from app.core.messages import (
    PROJECT_NOT_FOUND,
    TASK_ASSIGNEE_NOT_IN_WORKSPACE,
    TASK_NOT_FOUND,
    USER_NOT_FOUND,
    WORKSPACE_NOT_FOUND,
)
from app.models.enums import (
    TaskPriority,
    TaskStatus,
    UserRole,
    WorkspaceRole,
)
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate


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
        """Get project and workspace after checking membership and permissions."""
        project = await self.project_repository.get_by_id(project_id)

        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)

        workspace = await self.workspace_repository.get_by_id(
            project.workspace_id
        )

        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

        role: WorkspaceRole | None

        if (
            current_user.role == UserRole.ADMIN
            or workspace.owner_id == current_user.id
        ):
            role = WorkspaceRole.OWNER
        else:
            role = await self.workspace_repository.get_member(
                workspace.id,
                current_user.id,
            )

        if role is None:
            raise NotFoundException()

        if require_editor and role == WorkspaceRole.VIEWER:
            raise PermissionDenied()

        return project, workspace

    async def _validate_assignee(
        self,
        workspace: Workspace,
        assignee_id: int,
    ) -> None:
        """Ensure the assignee exists and belongs to the workspace."""
        assignee = await self.user_repository.get_by_id(assignee_id)

        if assignee is None:
            raise NotFoundException(USER_NOT_FOUND)

        if assignee_id == workspace.owner_id:
            return

        role = await self.workspace_repository.get_member(
            workspace.id,
            assignee_id,
        )

        if role is None:
            raise InvalidOperation(TASK_ASSIGNEE_NOT_IN_WORKSPACE)

    async def create_task(
        self,
        project_id: int,
        data: TaskCreate,
        current_user: User,
    ) -> TaskResponse:
        """Create a task in a project."""
        _, workspace = await self._get_project_and_workspace(
            project_id,
            current_user,
            require_editor=True,
        )

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
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
        page: int = DEFAULT_PAGE,
        limit: int = DEFAULT_PAGE_LIMIT,
    ) -> TaskListResponse:
        """Get filtered and paginated tasks in a project."""

        await self._get_project_and_workspace(project_id, current_user)

        tasks, total = await self.task_repository.get_filtered_by_project(
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            page=page,
            limit=limit,
        )

        return TaskListResponse(
            items=[
                TaskResponse.model_validate(task)
                for task in tasks
            ],
            total=total,
            page=page,
            limit=limit,
        )

    async def update_task(
        self,
        task_id: int,
        data: TaskUpdate,
        current_user: User,
    ) -> TaskResponse:
        """Update a task."""
        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        _, workspace = await self._get_project_and_workspace(
            task.project_id,
            current_user,
            require_editor=True,
        )

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
        """Delete a task."""
        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        await self._get_project_and_workspace(
            task.project_id,
            current_user,
            require_editor=True,
        )

        await self.task_repository.delete_entity(task)
