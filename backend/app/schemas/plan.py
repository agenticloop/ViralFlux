from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    price_usd: Decimal
    shorts_per_month: int | None
    channels_limit: int | None
    features: dict | None
    stripe_price_id: str | None


class UsageStats(BaseModel):
    shorts_used: int
    shorts_limit: int | None  # None = unlimited
    channels_used: int
    channels_limit: int | None  # None = unlimited


class CurrentPlanOut(BaseModel):
    plan: PlanOut
    usage: UsageStats
