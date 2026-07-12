# Graph Report - ODOO-HACKATHON-26  (2026-07-12)

## Corpus Check
- 88 files · ~18,028 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 609 nodes · 1008 edges · 58 communities (51 shown, 7 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 212 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0e34aa33`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]

## God Nodes (most connected - your core abstractions)
1. `auth()` - 40 edges
2. `AuditService` - 30 edges
3. `BookingService` - 24 edges
4. `MaintenanceService` - 24 edges
5. `MaintenanceService` - 23 edges
6. `NotificationService` - 22 edges
7. `_create()` - 21 edges
8. `AssetGateway` - 15 edges
9. `AuditCycleStatus` - 14 edges
10. `AuditItemStatus` - 14 edges

## Surprising Connections (you probably didn't know these)
- `get_db()` --calls--> `SessionLocal()`  [INFERRED]
  .claude/worktrees/strange-kowalevski-d77c9c/backend/app/database.py → backend/tests/conftest.py
- `Principal` --uses--> `Role`  [INFERRED]
  backend/app/maintenance/deps.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/enums.py
- `Role` --uses--> `Principal`  [INFERRED]
  backend/app/maintenance/deps.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/security.py
- `Principal` --uses--> `Principal`  [INFERRED]
  backend/app/maintenance/deps.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/security.py
- `MaintenanceService` --uses--> `NotFoundError`  [INFERRED]
  backend/app/maintenance/service.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/exceptions.py

## Communities (58 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (44): BaseModel, ActivityAction, AssetStatus, AuditCycleStatus, AuditItemStatus, BookingStatus, MaintenancePriority, MaintenanceStatus (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (46): auth(), _create_cycle(), test_auditor_only_records_own_items(), test_cannot_audit_before_active(), test_cannot_mark_lost_when_not_missing(), test_closed_cycle_is_locked(), test_create_cycle_requires_manager(), test_full_audit_flow_and_discrepancy() (+38 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (22): Base, ActivityLog, Activity log persistence model., An immutable record of a state-changing action.      Activity logs are append-on, AuditCycle, AuditItem, Asset audit persistence models: audit cycles and their line items., A scoped stock-take of assets over a date range. (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (25): AssetFlowError, AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError, Domain exceptions and their FastAPI handlers.  Services and validators raise the, Base class for all business-rule errors raised by this team's modules., Attach handlers for every AssetFlow error subclass to the app. (+17 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (15): NotificationCategory, NotificationType, Business event that triggered a notification., Notification, Notification persistence model., A message delivered to a single user's in-app inbox., Notification REST endpoints (current user's inbox)., unread_count() (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (25): _enum_values(), MaintenancePriority, MaintenanceRequest, MaintenanceStatus, Maintenance request persistence model and workflow enumerations.  Owns exactly o, The maintenance workflow states.      Happy path::          PENDING -> APPROVED, Persist enums by their ``.value`` (readable lowercase) in both directions., A repair/service request raised against an asset and driven through the     appr (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (13): Datetime helpers ensuring all timestamps are timezone-aware UTC., Normalize a datetime to timezone-aware UTC.      Naive datetimes are assumed to, to_utc(), utcnow(), Booking, Resource booking persistence model., A reservation of a bookable asset by an employee over a time window., BookingService (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (29): asset_status(), _create(), _drive_to_in_progress(), _post_create(), test_api_approve_requires_manager_role(), test_api_cannot_approve_twice(), test_api_create_returns_201(), test_api_disposed_asset_rejected() (+21 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (23): get_current_user(), get_db(), Integration seam between the Maintenance module and the shared foundation.  The, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., Resolve the authenticated principal.          The real implementation lives in t, require_roles(), admin() (+15 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (8): Audit router — thin. All logic lives in ``AuditService``.  Home for: AuditCycle, Booking router — thin. All logic lives in ``BookingService``.  Home for: calenda, Maintenance management REST endpoints.  Thin by design: every endpoint validates, get_router(), Workflow feature module (self-contained).  Owns: Resource Booking, Maintenance M, Return a single aggregated router for the whole Workflow module., Mount all Workflow routes onto the shared FastAPI application., register_routes()

### Community 10 - "Community 10"
Cohesion: 0.19
Nodes (6): MaintenanceService, Maintenance management business logic and workflow orchestration.  The service i, Stateless orchestrator; the DB session is passed in per call., Non-managers only see requests they raised or are assigned to., Only the assigned technician (or an admin) may progress the work., _utcnow()

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (3): MaintenanceService, Maintenance management business logic and workflow orchestration., Only the assigned technician (or an admin) may progress the work.

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (10): _enable_sqlite_foreign_keys(), get_db(), init_db(), Shared database engine, session factory and declarative base.  Every module in t, SQLite ignores foreign keys unless explicitly enabled per connection., FastAPI dependency yielding a scoped session that is always closed., Create the tables owned by this team (idempotent).      Importing ``app.models``, health_check() (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.20
Nodes (11): Exception, AuthenticationError, ConflictError, MaintenanceError, NotFoundError, PermissionDeniedError, Domain exceptions for the Maintenance module and their FastAPI handlers.  Servic, Base class for every business-rule error raised by the Maintenance module. (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (13): Maintenance workflow state-transition guards.  This is the single source of trut, Rule: a request may be approved once, and only from PENDING., Rule: only a still-pending request may be rejected., Rule: a technician cannot be assigned before approval.      Reassignment while a, Rule: work can only start once a technician has been assigned., Rule: a request cannot be resolved before it is In Progress., Rule: resolved (and rejected, i.e. terminal) requests cannot be edited., validate_can_approve() (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (3): Resource booking REST endpoints., Trigger due booking reminders (for schedulers / ops)., run_reminders()

### Community 18 - "Community 18"
Cohesion: 0.27
Nodes (7): _decode_token(), get_current_user(), Principal, _principal_from_claims(), Authentication primitives.  The Authentication module owns login/token issuance., The authenticated caller, derived from JWT claims., FastAPI dependency resolving the authenticated principal or raising 401.

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (5): Audit lifecycle guards., Reject any mutation to a closed (locked) cycle., Auditing may only happen while a cycle is active., validate_cycle_active(), validate_cycle_open()

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (3): CurrentUser, Integration seam between the Workflow module and the shared foundation.  The Wor, Stand-in mirroring the JWT claim contract (sub, role, department_id).

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (5): ensure(), Role-based access control helpers.  Coarse-grained role gates are expressed as r, Build a dependency that admits only the given roles (admin always passes)., Raise a permission error unless ``condition`` holds., require_roles()

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (3): NotificationService, NotificationService — reusable business-event notification generation.  There is, Generate a notification for a business event.

### Community 24 - "Community 24"
Cohesion: 0.33
Nodes (5): Booking validation rules.  Pure, side-effect-free checks that raise :class:`Asse, End must be strictly after start., Reject a booking that overlaps an existing active booking of the resource., validate_no_overlap(), validate_time_range()

### Community 26 - "Community 26"
Cohesion: 0.40
Nodes (3): Application configuration.  Values are read from environment variables with prod, Central runtime configuration., Settings

### Community 27 - "Community 27"
Cohesion: 0.50
Nodes (3): AssetFlow, Core Modules, Tech Stack

### Community 28 - "Community 28"
Cohesion: 0.50
Nodes (3): Maintenance Management module (self-contained vertical slice).  Owns the mainten, Mount the Maintenance router and error handlers onto a FastAPI app., register_routes()

### Community 29 - "Community 29"
Cohesion: 0.50
Nodes (3): AssetFlow, Core Modules, Tech Stack

### Community 30 - "Community 30"
Cohesion: 0.50
Nodes (3): AssetFlow, Core Modules, Tech Stack

## Knowledge Gaps
- **7 isolated node(s):** `allow`, `Tech Stack`, `Core Modules`, `Tech Stack`, `Core Modules` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MaintenanceRequest` connect `Community 5` to `Community 8`, `Community 2`, `Community 10`?**
  _High betweenness centrality (0.177) - this node is a cross-community bridge._
- **Why does `_PrincipalHolder` connect `Community 8` to `Community 5`?**
  _High betweenness centrality (0.169) - this node is a cross-community bridge._
- **Why does `MaintenanceService` connect `Community 10` to `Community 3`, `Community 5`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `auth()` (e.g. with `_raise()` and `test_cannot_raise_for_disposed_asset()`) actually correct?**
  _`auth()` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AuditService` (e.g. with `ActivityAction` and `AssetStatus`) actually correct?**
  _`AuditService` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `BookingService` (e.g. with `ActivityAction` and `BookingStatus`) actually correct?**
  _`BookingService` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `MaintenanceService` (e.g. with `NotFoundError` and `PermissionDeniedError`) actually correct?**
  _`MaintenanceService` has 8 INFERRED edges - model-reasoned connections that need verification._