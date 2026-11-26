"""Business logic for task operations."""

from app.core.exceptions import (
    InvalidOperation,
    NotFoundException,
)
from app.core.messages import (
    PROJECT_NOT_FOUND,
    TASK_ASSIGNEE_MUST_HAVE_WRITE_ACCESS,
    TASK_ASSIGNEE_NOT_IN_WORKSPACE,
    TASK_NOT_FOUND,
    USER_NOT_FOUND,
)
from app.models.enums import (
    TaskPriority,
    TaskStatus,
)
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.pagination import Pagination
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.workspace_access import (
    ensure_project_active,
    has_workspace_write_access,
    resolve_project_access,
)


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

    async def _get_task_response(self, task_id: int) -> TaskResponse:
        task = await self.task_repository.get_by_id_with_labels(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)
        return TaskResponse.model_validate(task)

    async def _get_project_and_workspace(
        self,
        project_id: int,
        current_user: User,
        require_editor: bool = False,
    ) -> tuple[Project, Workspace]:
        """Get a project and resolve the current user's workspace access."""

        project, access = await resolve_project_access(
            project_id,
            current_user,
            self.project_repository,
            self.workspace_repository,
            require_write=require_editor,
            inaccessible_message=PROJECT_NOT_FOUND,
        )
        return project, access.workspace

    async def _validate_assignee(
        self,
        workspace: Workspace,
        assignee_id: int,
    ) -> None:
        """Ensure the assignee is an eligible workspace member."""

        assignee = await self.user_repository.get_by_id(assignee_id)

        if assignee is None:
            raise InvalidOperation(USER_NOT_FOUND)

        # Workspace owners do not need a membership record.
        if assignee_id == workspace.owner_id:
            return

        role = await self.workspace_repository.get_member(
            workspace.id,
            assignee_id,
        )

        if role is None:
            raise InvalidOperation(TASK_ASSIGNEE_NOT_IN_WORKSPACE)

        if not has_workspace_write_access(role):
            raise InvalidOperation(TASK_ASSIGNEE_MUST_HAVE_WRITE_ACCESS)

    async def _get_task_project_and_workspace(
        self,
        task: Task,
        current_user: User,
    ) -> tuple[Project, Workspace]:
        """Resolve a task's project without revealing cross-workspace IDs."""
        try:
            return await self._get_project_and_workspace(
                task.project_id,
                current_user,
                require_editor=True,
            )
        except NotFoundException:
            raise NotFoundException(TASK_NOT_FOUND) from None

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
        ensure_project_active(project)

        if data.assignee_id is not None:
            await self._validate_assignee(workspace, data.assignee_id)

        task = await self.task_repository.create(
            {
                **data.model_dump(),
                "project_id": project_id,
                "created_by": current_user.id,
            }
        )

        return await self._get_task_response(task.id)

    async def get_tasks(
        self,
        project_id: int,
        current_user: User,
        pagination: Pagination,
        status: list[TaskStatus] | None = None,
        priority: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> TaskListResponse:
        """Get filtered and paginated tasks in a project."""

        await self._get_project_and_workspace(project_id, current_user)

        tasks, total = await self.task_repository.get_filtered_by_project(
            project_id=project_id,
            pagination=pagination,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
        )

        return TaskListResponse(
            items=[TaskResponse.model_validate(task) for task in tasks],
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

        project, workspace = await self._get_task_project_and_workspace(
            task,
            current_user,
        )
        ensure_project_active(project)

        update_data = data.model_dump(exclude_unset=True)

        if "assignee_id" in update_data and update_data["assignee_id"] is not None:
            await self._validate_assignee(
                workspace,
                update_data["assignee_id"],
            )

        updated_task = await self.task_repository.update_entity(
            task,
            update_data,
        )

        return await self._get_task_response(updated_task.id)

    async def delete_task(
        self,
        task_id: int,
        current_user: User,
    ) -> None:
        """Delete a task from an active project."""

        task = await self.task_repository.get_by_id(task_id)

        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)

        project, _ = await self._get_task_project_and_workspace(
            task,
            current_user,
        )
        ensure_project_active(project)

        await self.task_repository.delete_entity(task)
