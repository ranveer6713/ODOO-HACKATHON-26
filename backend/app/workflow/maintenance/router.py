"""Maintenance router — thin. All logic lives in ``MaintenanceService``.

Home for: maintenance request lifecycle and the status machine. Asset status
updates are applied through ``AssetGateway.set_status`` only.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
