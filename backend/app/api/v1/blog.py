from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.models.blog import BlogPost
from app.schemas.blog import BlogListResponse, BlogPostCreate, BlogPostOut, BlogPostUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blog", tags=["blog"])


def _is_admin(user) -> bool:
    return user.email in settings.admin_email_list


def _require_admin(user):
    if not _is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required."
        )


async def _get_post_or_404(post_id: UUID, db: AsyncSession) -> BlogPost:
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return post


@router.get("/posts", response_model=BlogListResponse)
async def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(BlogPost).where(BlogPost.status == "published")

    count_result = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    total = count_result.scalar_one()

    stmt = stmt.order_by(BlogPost.published_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    posts = result.scalars().all()

    return BlogListResponse(
        items=[BlogPostOut.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/posts/{slug}", response_model=BlogPostOut)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BlogPost).where(BlogPost.slug == slug, BlogPost.status == "published")
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return BlogPostOut.model_validate(post)


@router.post("/posts", response_model=BlogPostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: BlogPostCreate,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)

    post_slug = payload.slug or slugify(payload.title)

    # Ensure slug uniqueness
    existing = await db.execute(select(BlogPost).where(BlogPost.slug == post_slug))
    if existing.scalar_one_or_none():
        post_slug = f"{post_slug}-{int(datetime.now(timezone.utc).timestamp())}"

    post = BlogPost(
        author_id=current_user.id,
        slug=post_slug,
        **{k: v for k, v in payload.model_dump().items() if k != "slug"},
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return BlogPostOut.model_validate(post)


@router.put("/posts/{post_id}", response_model=BlogPostOut)
async def update_post(
    post_id: UUID,
    payload: BlogPostUpdate,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    post = await _get_post_or_404(post_id, db)

    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    await db.flush()
    await db.refresh(post)
    return BlogPostOut.model_validate(post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    post = await _get_post_or_404(post_id, db)
    await db.delete(post)
    await db.flush()


@router.post("/posts/{post_id}/publish", response_model=BlogPostOut)
async def publish_post(
    post_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(current_user)
    post = await _get_post_or_404(post_id, db)
    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(post)
    return BlogPostOut.model_validate(post)


@router.get("/sitemap")
async def sitemap(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BlogPost.slug, BlogPost.updated_at).where(BlogPost.status == "published")
    )
    posts = result.all()

    base_url = settings.APP_URL.rstrip("/")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for post in posts:
        lines.append("  <url>")
        lines.append(f"    <loc>{base_url}/blog/{post.slug}</loc>")
        lines.append(f"    <lastmod>{post.updated_at.strftime('%Y-%m-%d')}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")

    return Response(
        content="\n".join(lines),
        media_type="application/xml",
    )
