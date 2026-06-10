from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.blog import router as blog_router
from app.api.v1.channels import router as channels_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.plans import router as plans_router
from app.api.v1.videos import router as videos_router
from app.api.v1.webhooks import router as webhooks_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(channels_router)
v1_router.include_router(videos_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(plans_router)
v1_router.include_router(blog_router)
v1_router.include_router(webhooks_router)
