"""Label API endpoints."""

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUserDep
from app.api.openapi import PROTECTED_API_RESPONSES
from app.core.dependencies import LabelServiceDep, PaginationDep
from app.schemas.label import (
    LabelCreate,
    LabelListResponse,
    LabelResponse,
    LabelUpdate,
)

router = APIRouter(tags=["Labels"], responses=PROTECTED_API_RESPONSES)


@router.post(
    "/projects/{project_id}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project",
    description="Create a label. Requires OWNER or EDITOR workspace access.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Project or workspace not found"},
        409: {"description": "A label with this name already exists in the project"},
    },
)
async def create_label(
    project_id: int,
    data: LabelCreate,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> LabelResponse:
    """Create a label in a project. Requires OWNER or EDITOR access."""
    return await service.create_label(project_id, data, current_user)


@router.get(
    "/projects/{project_id}/labels",
    response_model=LabelListResponse,
    summary="List labels in a project",
    description="List project labels for an accessible workspace member.",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Project or workspace not found"},
    },
)
async def get_labels(
    project_id: int,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
    pagination: PaginationDep,
) -> LabelListResponse:
    """List project labels with pagination."""
    return await service.get_labels(project_id, current_user, pagination)


@router.get(
    "/labels/{label_id}",
    response_model=LabelResponse,
    summary="Get a label",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Label, project, or workspace not found"},
    },
)
async def get_label(
    label_id: int,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> LabelResponse:
    """Get a label visible in an accessible workspace."""
    return await service.get_label(label_id, current_user)


@router.patch(
    "/labels/{label_id}",
    response_model=LabelResponse,
    summary="Update a label",
    description="Update a label. Requires OWNER or EDITOR workspace access.",
    responses={
        400: {"description": "Label cannot be changed in an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Label, project, or workspace not found"},
        409: {"description": "A label with this name already exists in the project"},
    },
)
async def update_label(
    label_id: int,
    data: LabelUpdate,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> LabelResponse:
    """Update a label. Requires OWNER or EDITOR access."""
    return await service.update_label(label_id, data, current_user)


@router.delete(
    "/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a label",
    description=("Delete a label and its task associations. Requires OWNER or EDITOR."),
    responses={
        400: {"description": "Label cannot be changed in an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Label, project, or workspace not found"},
    },
)
async def delete_label(
    label_id: int,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> Response:
    """Delete a label. Requires OWNER or EDITOR access."""
    await service.delete_label(label_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assign a label to a task",
    description=("Assign a same-project label. Requires OWNER or EDITOR access."),
    responses={
        400: {"description": "Project is archived"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Task or label not found"},
        409: {"description": "Label is already assigned to this task"},
    },
)
async def assign_label(
    task_id: int,
    label_id: int,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> Response:
    """Assign a same-project label to a task."""
    await service.assign_label(task_id, label_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/tasks/{task_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a label from a task",
    description=("Remove only the task association. Requires OWNER or EDITOR access."),
    responses={
        400: {"description": "Project is archived"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {
            "description": "Task or label not found, or label is not assigned",
        },
    },
)
async def remove_label(
    task_id: int,
    label_id: int,
    current_user: CurrentUserDep,
    service: LabelServiceDep,
) -> Response:
    """Remove a same-project label from a task."""
    await service.remove_label(task_id, label_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
