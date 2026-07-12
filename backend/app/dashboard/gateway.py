"""AssetGateway — read-only anti-corruption layer over the shared ``assets`` table.

The Dashboard never defines or imports an ``Asset`` ORM model; doing so would
couple the aggregation layer to another team's schema and pollute its metadata.
Every asset read goes through this narrow gateway using SQLAlchemy Core against
the documented contract only. Unlike the sibling gateways this one is strictly
**read-only** — the dashboard reports on assets, it never mutates them.

Expected ``assets`` table contract (owned by the Asset module):
    - ``id``            TEXT / VARCHAR  -- string primary key (string-FK contract)
    - ``name``          TEXT
    - ``status``        TEXT            -- lifecycle status string
    - ``department_id`` TEXT            -- OPTIONAL; read only when present

Only ``status`` is required. ``department_id`` is consumed for the department
distribution chart *if the Asset module exposes it* and silently skipped
otherwise, so the dashboard degrades gracefully instead of failing when an
optional column is absent. If the ``assets`` table itself is missing every read
returns empty rather than raising — an un-seeded estate simply shows zeros.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

# SQL errors that mean "the table/column isn't there" across SQLite / Postgres.
_MISSING_SCHEMA_ERRORS = (OperationalError, ProgrammingError)


class AssetGateway:
    """Read-only aggregate access to the shared ``assets`` table."""

    def _columns(self, db: Session) -> set:
        """Return the set of column names on the ``assets`` table (or empty).

        Introspection runs on the session's *own* connection (``db.connection()``)
        rather than a fresh checkout from the engine: a second connection over a
        shared/StaticPool DBAPI handle would, on close, roll back the session's
        in-flight transaction. Reusing the live connection also lets the inspector
        see schema created earlier in the same uncommitted transaction.
        """
        try:
            inspector = inspect(db.connection())
            if not inspector.has_table("assets"):
                return set()
            return {col["name"] for col in inspector.get_columns("assets")}
        except _MISSING_SCHEMA_ERRORS:  # pragma: no cover - defensive
            return set()

    def status_counts(self, db: Session) -> Dict[str, int]:
        """Count assets grouped by raw status in a single ``GROUP BY`` query.

        Returns a ``{raw_status: count}`` mapping. An absent ``assets`` table
        yields an empty mapping rather than raising.
        """
        try:
            rows = db.execute(
                text(
                    "SELECT status, COUNT(*) AS c FROM assets GROUP BY status"
                )
            ).all()
        except _MISSING_SCHEMA_ERRORS:
            return {}
        return {str(status): int(count) for status, count in rows}

    def department_distribution(self, db: Session) -> List[Tuple[str, int]]:
        """Count assets per department in one query (``[]`` if unsupported).

        Only runs when the optional ``department_id`` column is present. Assets
        with no department are grouped under ``"Unassigned"``. Ordered by count
        descending so the chart's largest slices come first.
        """
        if "department_id" not in self._columns(db):
            return []
        try:
            rows = db.execute(
                text(
                    "SELECT COALESCE(department_id, 'Unassigned') AS dept, "
                    "COUNT(*) AS c FROM assets GROUP BY dept ORDER BY c DESC, dept"
                )
            ).all()
        except _MISSING_SCHEMA_ERRORS:  # pragma: no cover - defensive
            return []
        return [(str(dept), int(count)) for dept, count in rows]


# Module-level singleton; stateless, so safe to share across requests.
asset_gateway = AssetGateway()
