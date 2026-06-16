from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    price_usd: Decimal
    price_yearly_usd: Decimal | None
    credits_per_month: int
    max_quota: int
    channels_limit: int | None
    features: dict | None
    stripe_price_id: str | None
    stripe_price_id_yearly: str | None


class UsageStats(BaseModel):
    credits_balance: int
    subscription_credits: int
    topup_credits: int
    credits_per_month: int
    max_quota: int
    max_quota_used: int
    channels_used: int
    channels_limit: int | None  # None = unlimited
    period_start: datetime | None
    period_end: datetime | None


class CurrentPlanOut(BaseModel):
    plan: PlanOut
    usage: UsageStats


class CreditLedgerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    amount: int
    balance_after: int
    bucket: str
    job_id: UUID | None
    note: str | None
    created_at: datetime


class TopupRequest(BaseModel):
    pack: str


class AddonRequest(BaseModel):
    addon: str


class UpgradeRequest(BaseModel):
    plan: str  # plan name: free/starter/pro/agency


class CustomPlanRequestIn(BaseModel):
    name: str
    email: str
    channels_needed: int | None = None
    videos_per_month: int | None = None
    max_duration: str | None = None
    team_seats: int | None = None
    genres: str | None = None
    notes: str | None = None
