from __future__ import annotations

# Import all models here so Alembic autodiscovers them via Base.metadata
from app.models.analytics import Asset, VideoAnalytic  # noqa: F401
from app.models.blog import BlogPost, ContentFormat  # noqa: F401
from app.models.channel import ChannelSchedule, YoutubeChannel  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.video_job import VideoJob  # noqa: F401
