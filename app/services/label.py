"""Business logic for project labels and task-label associations."""

from typing import NoReturn

from sqlalchemy.exc import IntegrityError

from app.core.constants import LABEL_PROJECT_NAME_CONSTRAINT
from app.core.database import register_project_cache_invalidation
from app.core.exceptions import (
    ConflictError,
    NotFoundException,
)
from app.core.messages import (
    LABEL_ALREADY_ASSIGNED,
    LABEL_NAME_ALREADY_EXISTS,
    LABEL_NOT_ASSIGNED,
    LABEL_NOT_FOUND,
    PROJECT_NOT_FOUND,
    TASK_NOT_FOUND,
)
from app.models import Label, Project, User, Workspace
from app.repositories.label import LabelRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.label import (
    LabelCreate,
    LabelListResponse,
    LabelResponse,
    LabelUpdate,
)
from app.schemas.pagination import Pagination
from app.services.workspace_access import (
    ensure_project_active,
    resolve_project_access,
)


def _raise_label_name_conflict(exc: IntegrityError) -> NoReturn:
    """Translate only the project-scoped label-name unique violation."""

    sqlstate: str | None = None
    constraint_name: str | None = None
    original: object | None = exc.orig
    visited: set[int] = set()

    while original is not None and id(original) not in visited:
        visited.add(id(original))
        sqlstate = (
            sqlstate
            or getattr(original, "sqlstate", None)
            or getattr(
                original,
                "pgcode",
                None,
            )
        )
        constraint_name = constraint_name or getattr(
            original,
            "constraint_name",
            None,
        )
        diagnostic = getattr(original, "diag", None)
        constraint_name = constraint_name or getattr(
            diagnostic,
            "constraint_name",
            None,
        )
        nested = getattr(original, "orig", None)
        original = (
            nested if nested is not None else getattr(original, "__cause__", None)
        )

    if sqlstate != "23505" or constraint_name != LABEL_PROJECT_NAME_CONSTRAINT:
        raise exc
    raise ConflictError(LABEL_NAME_ALREADY_EXISTS) from exc


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
        not_found_message: str = PROJECT_NOT_FOUND,
        inaccessible_message: str | None = None,
    ) -> tuple[Project, Workspace]:
        project, access = await resolve_project_access(
            project_id,
            current_user,
            self.project_repository,
            self.workspace_repository,
            require_write=require_editor,
            not_found_message=not_found_message,
            inaccessible_message=inaccessible_message,
        )
        return project, access.workspace

    async def _get_label(self, label_id: int) -> Label:
        label = await self.label_repository.get_by_id(label_id)
        if label is None:
            raise NotFoundException(LABEL_NOT_FOUND)
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
        ensure_project_active(project)
        try:
            label = await self.label_repository.create(
                {**data.model_dump(), "project_id": project_id}
            )
        except IntegrityError as exc:
            _raise_label_name_conflict(exc)
        return LabelResponse.model_validate(label)

    async def get_labels(
        self,
        project_id: int,
        current_user: User,
        pagination: Pagination,
    ) -> LabelListResponse:
        await self._get_project_access(project_id, current_user)
        labels, total = await self.label_repository.get_by_project(
            project_id,
            pagination,
        )
        return LabelListResponse(
            items=[LabelResponse.model_validate(label) for label in labels],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )

    async def get_label(
        self,
        label_id: int,
        current_user: User,
    ) -> LabelResponse:
        label = await self._get_label(label_id)
        await self._get_project_access(
            label.project_id,
            current_user,
            not_found_message=LABEL_NOT_FOUND,
            inaccessible_message=LABEL_NOT_FOUND,
        )
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
            not_found_message=LABEL_NOT_FOUND,
            inaccessible_message=LABEL_NOT_FOUND,
        )
        ensure_project_active(project)
        try:
            updated = await self.label_repository.update_entity(
                label,
                data.model_dump(exclude_unset=True),
            )
            register_project_cache_invalidation(
                self.label_repository.session,
                label.project_id,
            )
        except IntegrityError as exc:
            _raise_label_name_conflict(exc)
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
            not_found_message=LABEL_NOT_FOUND,
            inaccessible_message=LABEL_NOT_FOUND,
        )
        ensure_project_active(project)
        await self.label_repository.delete_entity(label)
        register_project_cache_invalidation(
            self.label_repository.session,
            label.project_id,
        )

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
        ensure_project_active(project)
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
            raise NotFoundException(LABEL_NOT_FOUND)
        inserted = await self.label_repository.assign_to_task(task_id, label_id)
        if not inserted:
            raise ConflictError(LABEL_ALREADY_ASSIGNED)
        register_project_cache_invalidation(
            self.label_repository.session,
            task_project_id,
        )

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
            raise NotFoundException(LABEL_NOT_FOUND)
        removed = await self.label_repository.remove_from_task(task_id, label_id)
        if not removed:
            raise NotFoundException(LABEL_NOT_ASSIGNED)
        register_project_cache_invalidation(
            self.label_repository.session,
            task_project_id,
        )
