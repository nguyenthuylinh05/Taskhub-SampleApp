from fastapi import APIRouter

from app.api.v1.endpoints import projects

api_router = APIRouter()

api_router.include_router(projects.router)
