"""Comment API endpoints."""

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUserDep
from app.core.dependencies import CommentServiceDep, PaginationDep
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)

router = APIRouter(tags=["Comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
    description=("Add a comment as the authenticated user. Requires OWNER or EDITOR."),
    responses={
        400: {"description": "Task belongs to an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Task, project, or workspace not found"},
        422: {"description": "Comment content is invalid"},
    },
)
async def create_comment(
    task_id: int,
    data: CommentCreate,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
) -> CommentResponse:
    return await service.create_comment(task_id, data, current_user)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=CommentListResponse,
    summary="List comments for a task",
    description="List comments for a task in an accessible workspace.",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Task, project, or workspace not found"},
    },
)
async def get_comments(
    task_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
    pagination: PaginationDep,
) -> CommentListResponse:
    return await service.get_comments(task_id, current_user, pagination)


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Update a comment",
    description="Update a comment as its author in an accessible workspace.",
    responses={
        400: {"description": "Comment belongs to an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Only the comment author may update it"},
        404: {"description": "Comment, task, project, or workspace not found"},
        422: {"description": "Comment content is invalid"},
    },
)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
) -> CommentResponse:
    return await service.update_comment(comment_id, data, current_user)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description=("Delete a comment. Requires OWNER or EDITOR access to its workspace."),
    responses={
        400: {"description": "Comment belongs to an archived project"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Comment, task, project, or workspace not found"},
    },
)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUserDep,
    service: CommentServiceDep,
) -> Response:
    await service.delete_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
