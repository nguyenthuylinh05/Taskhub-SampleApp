"""Task API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentUserDep
from app.core.dependencies import PaginationDep, TaskServiceDep
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(tags=["Tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
    responses={
        400: {
            "description": ("Task assignment or project state violates business rules"),
        },
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Project or workspace not found"},
    },
)
async def create_task(
    project_id: int,
    data: TaskCreate,
    current_user: CurrentUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    return await service.create_task(project_id, data, current_user)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse,
    summary="List tasks in a project",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Project or workspace not found"},
    },
)
async def get_tasks(
    project_id: int,
    current_user: CurrentUserDep,
    service: TaskServiceDep,
    pagination: PaginationDep,
    task_status: Annotated[
        list[TaskStatus] | None,
        Query(alias="status"),
    ] = None,
    priority: Annotated[
        list[TaskPriority] | None,
        Query(),
    ] = None,
    assignee_id: Annotated[int | None, Query(ge=1)] = None,
) -> TaskListResponse:
    return await service.get_tasks(
        project_id=project_id,
        current_user=current_user,
        status=task_status,
        priority=priority,
        assignee_id=assignee_id,
        pagination=pagination,
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    responses={
        400: {"description": "Task update violates business rules"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Task, project, or workspace not found"},
    },
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: CurrentUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    return await service.update_task(task_id, data, current_user)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses={
        400: {"description": "Cannot modify resources in an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Task, project, or workspace not found"},
    },
)
async def delete_task(
    task_id: int,
    current_user: CurrentUserDep,
    service: TaskServiceDep,
) -> Response:
    await service.delete_task(task_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
