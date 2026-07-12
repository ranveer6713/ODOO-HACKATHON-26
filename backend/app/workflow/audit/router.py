"""Audit router — thin. All logic lives in ``AuditService``.

Home for: AuditCycle / AuditItem endpoints, discrepancy report, and history.
Audited assets are read through ``AssetGateway``.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/audits", tags=["Audit"])
