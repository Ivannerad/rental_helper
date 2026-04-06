"""Shared domain entities used across services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class AccountStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    STOPPED = "stopped"


class ConversationStage(str, Enum):
    COLLECTING = "collecting"
    SEARCHING = "searching"
    VIEWING = "viewing"
    UPSELL = "upsell"


class ConversationStatus(str, Enum):
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELED = "canceled"


@dataclass(frozen=True)
class ManagedAccount:
    id: UUID
    telegram_phone: str
    display_name: str
    status: AccountStatus
    created_at: datetime


@dataclass(frozen=True)
class BoundGroup:
    id: UUID
    managed_account_id: UUID
    telegram_group_id: int
    telegram_group_title: str
    bound_at: datetime


@dataclass(frozen=True)
class LeadRequirements:
    district: str | None = None
    room_count: int | None = None
    max_budget: int | None = None

    def __post_init__(self) -> None:
        if self.room_count is not None and self.room_count <= 0:
            raise ValueError("room_count must be a positive integer")
        if self.max_budget is not None and self.max_budget <= 0:
            raise ValueError("max_budget must be a positive integer")


@dataclass(frozen=True)
class Conversation:
    id: UUID
    managed_account_id: UUID
    telegram_user_id: int
    stage: ConversationStage
    status: ConversationStatus
    requirements: LeadRequirements
    handoff_to_human: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Listing:
    id: UUID
    managed_account_id: UUID
    bound_group_id: UUID
    group_message_id: int
    district: str
    room_count: int
    price: int
    summary: str
    status: ListingStatus
    indexed_at: datetime

    def __post_init__(self) -> None:
        if self.room_count <= 0:
            raise ValueError("room_count must be a positive integer")
        if self.price <= 0:
            raise ValueError("price must be a positive integer")


@dataclass(frozen=True)
class ListingOffer:
    id: UUID
    conversation_id: UUID
    listing_id: UUID
    offered_at: datetime
    rejected: bool = False


@dataclass(frozen=True)
class ViewingAppointment:
    id: UUID
    managed_account_id: UUID
    conversation_id: UUID
    listing_id: UUID
    telegram_user_id: int
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    created_at: datetime

    def __post_init__(self) -> None:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
