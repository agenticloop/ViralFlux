from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BlogPostCreate(BaseModel):
    title: str
    slug: str | None = None
    content: str
    excerpt: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    og_image_url: str | None = None
    featured_image_url: str | None = None
    tags: list[str] | None = None
    reading_time_min: int | None = None


class BlogPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    content: str | None = None
    excerpt: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    og_image_url: str | None = None
    featured_image_url: str | None = None
    tags: list[str] | None = None
    reading_time_min: int | None = None


class BlogPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID | None
    title: str
    slug: str
    content: str
    excerpt: str | None
    meta_title: str | None
    meta_description: str | None
    og_image_url: str | None
    featured_image_url: str | None
    status: str
    tags: list[str] | None
    reading_time_min: int | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BlogListResponse(BaseModel):
    items: list[BlogPostOut]
    total: int
    page: int
    page_size: int
