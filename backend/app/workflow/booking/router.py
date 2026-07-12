"""Booking router — thin. All logic lives in ``BookingService``.

Home for: calendar, overlap validation, cancel, reschedule, reminder endpoints.
Booking references ``users.id`` and ``assets.id`` via string ForeignKeys and
touches assets only through ``AssetGateway``.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["Booking"])
