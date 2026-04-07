"""Repository for viewing appointments."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from shared.domain import AppointmentStatus, ViewingAppointment

from ._base import BaseRepository, Session
from ._mappers import VIEWING_APPOINTMENT_COLUMNS, viewing_appointment_from_row


class AppointmentRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create_appointment(self, appointment: ViewingAppointment) -> ViewingAppointment:
        row = self._fetch_one(
            f"""
            INSERT INTO viewing_appointments ({VIEWING_APPOINTMENT_COLUMNS})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {VIEWING_APPOINTMENT_COLUMNS}
            """,
            (
                appointment.id,
                appointment.managed_account_id,
                appointment.conversation_id,
                appointment.listing_id,
                appointment.telegram_user_id,
                appointment.starts_at,
                appointment.ends_at,
                appointment.status.value,
                appointment.created_at,
            ),
        )
        assert row is not None
        return viewing_appointment_from_row(tuple(row))

    def get_appointments_for_conversation(self, conversation_id: UUID) -> list[ViewingAppointment]:
        rows = self._fetch_all(
            f"""
            SELECT {VIEWING_APPOINTMENT_COLUMNS}
            FROM viewing_appointments
            WHERE conversation_id = %s
            ORDER BY starts_at ASC
            """,
            (conversation_id,),
        )
        return [viewing_appointment_from_row(tuple(row)) for row in rows]

    def get_appointments_by_conversation(self, conversation_id: UUID) -> list[ViewingAppointment]:
        return self.get_appointments_for_conversation(conversation_id)

    def list_by_conversation(self, conversation_id: UUID) -> list[ViewingAppointment]:
        return self.get_appointments_for_conversation(conversation_id)

    def get_upcoming_appointments_for_account(
        self,
        managed_account_id: UUID,
        *,
        as_of: datetime | None = None,
    ) -> list[ViewingAppointment]:
        boundary = as_of or datetime.now(timezone.utc)
        rows = self._fetch_all(
            f"""
            SELECT {VIEWING_APPOINTMENT_COLUMNS}
            FROM viewing_appointments
            WHERE managed_account_id = %s
              AND starts_at >= %s
              AND status IN (%s, %s)
            ORDER BY starts_at ASC
            """,
            (
                managed_account_id,
                boundary,
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ),
        )
        return [viewing_appointment_from_row(tuple(row)) for row in rows]

    def list_upcoming_for_account(
        self,
        managed_account_id: UUID,
        *,
        starts_from: datetime | None = None,
    ) -> list[ViewingAppointment]:
        return self.get_upcoming_appointments_for_account(
            managed_account_id,
            as_of=starts_from,
        )

    def update_status(
        self, appointment_id: UUID, status: AppointmentStatus
    ) -> ViewingAppointment | None:
        row = self._fetch_one(
            f"""
            UPDATE viewing_appointments
            SET status = %s
            WHERE id = %s
            RETURNING {VIEWING_APPOINTMENT_COLUMNS}
            """,
            (status.value, appointment_id),
        )
        return None if row is None else viewing_appointment_from_row(tuple(row))


class ViewingAppointmentRepository(AppointmentRepository):
    """Backward-compatible alias for older imports."""
