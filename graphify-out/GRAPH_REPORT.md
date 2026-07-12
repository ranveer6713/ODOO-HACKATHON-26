# Graph Report - ODOO-HACKATHON-26  (2026-07-12)

## Corpus Check
- 154 files · ~49,990 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1523 nodes · 2588 edges · 125 communities (113 shown, 12 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 391 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3da4dca4`
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
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 110|Community 110]]
- [[_COMMUNITY_Community 111|Community 111]]
- [[_COMMUNITY_Community 112|Community 112]]
- [[_COMMUNITY_Community 113|Community 113]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 115|Community 115]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 117|Community 117]]
- [[_COMMUNITY_Community 118|Community 118]]
- [[_COMMUNITY_Community 119|Community 119]]
- [[_COMMUNITY_Community 120|Community 120]]
- [[_COMMUNITY_Community 121|Community 121]]
- [[_COMMUNITY_Community 122|Community 122]]
- [[_COMMUNITY_Community 123|Community 123]]
- [[_COMMUNITY_Community 124|Community 124]]

## God Nodes (most connected - your core abstractions)
1. `auth()` - 40 edges
2. `AssetAuditService` - 38 edges
3. `MaintenanceService` - 31 edges
4. `AuditService` - 30 edges
5. `_create_cycle()` - 28 edges
6. `PermissionDeniedError` - 26 edges
7. `_add_item()` - 26 edges
8. `_create()` - 26 edges
9. `NotFoundError` - 25 edges
10. `BookingService` - 24 edges

## Surprising Connections (you probably didn't know these)
- `NotificationService` --uses--> `NotFoundError`  [INFERRED]
  backend/app/notifications/service.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/exceptions.py
- `NotificationService` --uses--> `ValidationError`  [INFERRED]
  backend/app/notifications/service.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/exceptions.py
- `AssetGateway` --uses--> `AssetStatus`  [INFERRED]
  backend/app/workflow/services/asset_gateway.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/enums.py
- `AssetGateway` --uses--> `NotFoundError`  [INFERRED]
  backend/app/workflow/services/asset_gateway.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/exceptions.py
- `AssetGateway` --uses--> `ValidationError`  [INFERRED]
  backend/app/workflow/services/asset_gateway.py → .claude/worktrees/strange-kowalevski-d77c9c/backend/app/core/exceptions.py

## Communities (125 total, 12 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.33
Nodes (12): BaseModel, AuditCycleStatus, AuditItemStatus, AuditCycleCreate, AuditCycleRead, AuditCycleUpdate, AuditItemCreate, AuditItemRead (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (47): auth(), _create_cycle(), test_auditor_only_records_own_items(), test_cannot_audit_before_active(), test_cannot_mark_lost_when_not_missing(), test_closed_cycle_is_locked(), test_create_cycle_requires_manager(), test_full_audit_flow_and_discrepancy() (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.19
Nodes (4): AssetGateway, AssetGateway — anti-corruption layer for the shared ``assets`` table.  The Workf, Maintenance transitions an asset's status through this method only., Read/write access to the shared ``assets`` table via SQLAlchemy Core.

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (4): NotificationService, Reusable notification service.  The single entry point is :meth:`NotificationSer, Creates and manages per-user in-app notifications., Core primitive: persist one notification for one user.          Flushed rather t

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (24): _enum_values(), MaintenancePriority, MaintenanceStatus, Maintenance request persistence model and workflow enumerations.  Owns exactly o, The maintenance workflow states.      Happy path::          PENDING -> APPROVED, Persist enums by their ``.value`` (readable lowercase) in both directions., MaintenanceCreate, MaintenanceRead (+16 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (16): Datetime helpers ensuring all timestamps are timezone-aware UTC., Normalize a datetime to timezone-aware UTC.      Naive datetimes are assumed to, to_utc(), utcnow(), Booking, Resource booking persistence model., A reservation of a bookable asset by an employee over a time window., BookingService (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (22): asset_status(), _create(), _drive_to_in_progress(), test_approve_moves_to_approved_and_takes_asset_out_of_service(), test_assign_after_approval(), test_can_edit_pending_request(), test_cannot_edit_rejected_request(), test_cannot_edit_resolved_request() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.26
Nodes (9): admin(), client(), employee(), make_principal(), manager(), _PrincipalHolder, Mutable holder so a test can switch the acting principal per request., Mutable holder so a test can switch the acting principal per request. (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (8): Audit router — thin. All logic lives in ``AuditService``.  Home for: AuditCycle, Booking router — thin. All logic lives in ``BookingService``.  Home for: calenda, Maintenance management REST endpoints.  Thin by design: every endpoint validates, get_router(), Workflow feature module (self-contained).  Owns: Resource Booking, Maintenance M, Return a single aggregated router for the whole Workflow module., Mount all Workflow routes onto the shared FastAPI application., register_routes()

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (25): AuditCycleStatus, AuditItemStatus, The audit-cycle lifecycle.      Happy path::          CREATED -> ACTIVE -> CLOSE, The auditor's verification verdict for an enrolled asset.      ``None`` (the col, AuditCycleCreate, AuditCycleRead, AuditCycleUpdate, AuditItemCreate (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (44): bucket_for_status(), Fold a raw ``assets.status`` value into its KPI bucket., AssetKpiCards, AuditSummary, BookingSummary, ChartDataPoint, ChartSeries, DashboardAnalytics (+36 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (11): _enable_sqlite_foreign_keys(), get_db(), init_db(), Shared database engine, session factory and declarative base.  Every module in t, SQLite ignores foreign keys unless explicitly enabled per connection., FastAPI dependency yielding a scoped session that is always closed., Create the tables owned by this team (idempotent).      Importing ``app.models``, get_db() (+3 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (10): AuthenticationError, ConflictError, MaintenanceError, NotFoundError, PermissionDeniedError, Domain exceptions for the Maintenance module and their FastAPI handlers.  Servic, Base class for every business-rule error raised by the Maintenance module., Attach the Maintenance error handler to a FastAPI application. (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (13): Maintenance workflow state-transition guards.  This is the single source of trut, Rule: a request may be approved once, and only from PENDING., Rule: only a still-pending request may be rejected., Rule: a technician cannot be assigned before approval.      Reassignment while a, Rule: work can only start once a technician has been assigned., Rule: a request cannot be resolved before it is In Progress., Rule: resolved (and rejected, i.e. terminal) requests cannot be edited., validate_can_approve() (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (3): Resource booking REST endpoints., Trigger due booking reminders (for schedulers / ops)., run_reminders()

### Community 18 - "Community 18"
Cohesion: 0.38
Nodes (5): _decode_token(), get_current_user(), _principal_from_claims(), Authentication primitives.  The Authentication module owns login/token issuance., FastAPI dependency resolving the authenticated principal or raising 401.

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (5): Audit lifecycle guards., Reject any mutation to a closed (locked) cycle., Auditing may only happen while a cycle is active., validate_cycle_active(), validate_cycle_open()

### Community 21 - "Community 21"
Cohesion: 0.36
Nodes (5): CurrentUser, get_current_user(), get_db(), Integration seam between the Workflow module and the shared foundation.  The Wor, Stand-in mirroring the JWT claim contract (sub, role, department_id).

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (5): ensure(), Role-based access control helpers.  Coarse-grained role gates are expressed as r, Build a dependency that admits only the given roles (admin always passes)., Raise a permission error unless ``condition`` holds., require_roles()

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (27): _enum_values(), Notification, NotificationSeverity, NotificationType, Notification persistence model and category enumeration.  Owns exactly one table, The originating domain of a notification., How much attention a notification warrants.      Mirrors the activity trail's se, Persist enums by their ``.value`` (readable lowercase) in both directions. (+19 more)

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
Cohesion: 0.60
Nodes (4): AssetFlow, Core Modules, Hackathon, Tech Stack

### Community 30 - "Community 30"
Cohesion: 0.50
Nodes (3): AssetFlow, Core Modules, Tech Stack

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (10): AuditError, AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError, Domain exceptions for the Audit module and their FastAPI handlers.  Framework-ag, Base class for every business-rule error raised by the Audit module., Attach the Audit error handler to a FastAPI application. (+2 more)

### Community 59 - "Community 59"
Cohesion: 0.11
Nodes (45): _add_item(), admin(), _api_create_cycle(), asset_status(), auditor_a(), auditor_b(), _create_cycle(), db() (+37 more)

### Community 60 - "Community 60"
Cohesion: 0.09
Nodes (41): asset_status(), client(), _create(), db(), _drive_to_checked_out(), employee(), _Holder, manager() (+33 more)

### Community 61 - "Community 61"
Cohesion: 0.07
Nodes (27): admin(), client(), db(), employee(), _Holder, _insert_activity(), _insert_asset(), _insert_booking() (+19 more)

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (6): BookingService, Booking management business logic and workflow orchestration.  The service is th, Active bookings for the asset whose window overlaps ``[start, end)``., Stateless orchestrator; the DB session is passed in per call., Non-managers only see bookings they raised., _utcnow()

### Community 63 - "Community 63"
Cohesion: 0.12
Nodes (15): AuditSeverity, _enum_values(), Activity-log persistence model and audit enumerations.  Owns exactly one table:, How much attention a logged action warrants., Persist enums by their ``.value`` (readable lowercase) in both directions., AuditService, _coerce_severity(), Audit business logic — the append-only activity trail.  Two responsibilities: (+7 more)

### Community 64 - "Community 64"
Cohesion: 0.18
Nodes (18): client(), db(), _Holder, principal(), Unit and API tests for the Audit (activity-log) module.  Exercised in isolation:, _record(), session_factory(), test_acknowledge_requires_flag_first() (+10 more)

### Community 65 - "Community 65"
Cohesion: 0.12
Nodes (28): RBAC roles, sourced from the JWT ``role`` claim by the foundation., Role, Principal, RBAC roles, sourced from the JWT ``role`` claim by the foundation., The authenticated caller, derived from JWT claims.          User identifiers are, Role, Principal, RBAC roles, sourced from the JWT ``role`` claim by the foundation. (+20 more)

### Community 66 - "Community 66"
Cohesion: 0.17
Nodes (16): client(), db(), _deliver(), _Holder, principal(), Unit and API tests for the Notifications module.  Exercised in complete isolatio, session_factory(), test_api_list_unread_and_mark() (+8 more)

### Community 67 - "Community 67"
Cohesion: 0.13
Nodes (17): AssetInfo, AssetStatus, AssetGateway — anti-corruption layer for the shared ``assets`` table.  The Booki, Lifecycle states of an asset (canonical column lives in ``assets``)., AssetFlowError, ConflictError, NotFoundError, Domain exceptions and their FastAPI handlers.  Services and validators raise the (+9 more)

### Community 68 - "Community 68"
Cohesion: 0.12
Nodes (17): _as_utc(), BookingCancel, BookingCreate, BookingRead, BookingReject, BookingUpdate, _normalise_tz(), Page (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.11
Nodes (11): mark_all_read(), Notifications REST endpoints.  Thin by design: every endpoint resolves the curre, MarkAllReadResult, NotificationRead, Page, PageMeta, Pydantic (v2) request/response schemas for the Notifications module., Generic paginated response envelope. (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (12): AuditCycle, AuditItem, Asset audit persistence models: audit cycles and their line items., A scoped stock-take of assets over a date range., A single asset audited within a cycle., MaintenanceRequest, Maintenance request persistence model., A repair/service request raised against an asset and worked through the     appr (+4 more)

### Community 71 - "Community 71"
Cohesion: 0.11
Nodes (17): Booking workflow state-transition and scheduling guards.  The single source of t, Rule: only a still-pending booking may have its details edited., Rule: a booking must span a positive window that does not end in the past., Rule: an asset cannot be double-booked for overlapping time windows., Rule: a booking may be approved once, and only from PENDING., Rule: only a still-pending booking may be rejected., Rule: an asset can only be checked out once the booking is approved., Rule: an asset can only be checked in once it has been checked out. (+9 more)

### Community 72 - "Community 72"
Cohesion: 0.12
Nodes (13): ActivityAction, AssetStatus, NotificationCategory, NotificationType, Domain enumerations shared across the modules owned by this team.  All enums inh, Lifecycle states of an asset (owned by the Asset module).      This team only re, Business event that triggered a notification., Auditable actions recorded in the activity log. (+5 more)

### Community 73 - "Community 73"
Cohesion: 0.08
Nodes (43): _add_activity(), _add_booking(), _add_cycle(), _add_item(), _add_maintenance(), _add_notification(), client(), db() (+35 more)

### Community 74 - "Community 74"
Cohesion: 0.17
Nodes (8): AssetGateway, AssetInfo, AssetGateway — anti-corruption layer for the shared ``assets`` table.  The Asset, Transition an asset's status. Asset Audit mutates assets only here., Flag a confirmed-missing asset as lost (audit close outcome)., Read/write access to the shared ``assets`` table via SQLAlchemy Core.      The A, Fetch one asset by id, or ``None`` if it does not exist., List assets, optionally filtered by status (read-only).

### Community 75 - "Community 75"
Cohesion: 0.12
Nodes (15): Asset Audit workflow state-transition and business-rule guards.  This is the sin, Rule: an audit window must not end before it begins., Rule: a closed audit is locked and can no longer be edited., Rule: only a freshly-created cycle can be started (once)., Rule: only a started, non-empty audit can be closed (once)., Rule: assets/auditors can only be enrolled while the audit is not closed., Enforce the two enrollment uniqueness rules.      * *Cannot duplicate auditor en, Rule: an item can be verified once, and only while the cycle is active. (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.29
Nodes (4): AssetGateway, Read/write access to the shared ``assets`` table via SQLAlchemy Core., Transition an asset's status. Maintenance mutates assets only here., Guarantee an asset can enter the maintenance workflow.          Enforces the rul

### Community 77 - "Community 77"
Cohesion: 0.09
Nodes (16): Describes a single report so a UI can build its filter/sort controls., One column in a report — a stable ``key`` and a human ``label``., ReportCatalogEntry, ReportColumn, Stateless orchestrator; the DB session and principal are passed per call., Describe every report so a UI can build its filter/sort controls., Render one paginated slice of a report., Render the full filtered report (capped) as CSV or PDF bytes.          Returns ` (+8 more)

### Community 78 - "Community 78"
Cohesion: 0.22
Nodes (10): AssetAuditError, AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError, Domain exceptions for the Asset Audit module and their FastAPI handlers.  Servic, Base class for every business-rule error raised by the Asset Audit module., Attach the Asset Audit error handler to a FastAPI application. (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.17
Nodes (9): get_current_user(), get_db(), Principal, Integration seam between the Asset Audit module and the shared foundation.  The, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., The authenticated caller, derived from JWT claims.          User identifiers are, Resolve the authenticated principal.          The real implementation lives in t (+1 more)

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (7): get_current_user(), get_db(), Integration seam between the Audit module and the shared foundation.  The Audit, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., Resolve the authenticated principal.          The real implementation lives in t, require_roles()

### Community 82 - "Community 82"
Cohesion: 0.22
Nodes (7): get_current_user(), get_db(), Integration seam between the Booking module and the shared foundation.  The Book, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., Resolve the authenticated principal.          The real implementation lives in t, require_roles()

### Community 83 - "Community 83"
Cohesion: 0.22
Nodes (7): get_current_user(), get_db(), Integration seam between the Dashboard module and the shared foundation.  The Da, Resolve the authenticated principal.          The real implementation lives in t, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., require_roles()

### Community 84 - "Community 84"
Cohesion: 0.20
Nodes (7): AssetGateway, AssetGateway — read-only anti-corruption layer over the shared ``assets`` table., Read-only aggregate access to the shared ``assets`` table., Return the set of column names on the ``assets`` table (or empty).          Intr, Count assets grouped by raw status in a single ``GROUP BY`` query.          Retu, Count assets per department in one query (``[]`` if unsupported).          Only, Count assets per category in one query (``[]`` if unsupported).

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (7): get_current_user(), get_db(), Integration seam between the Notifications module and the shared foundation.  Th, Build a FastAPI dependency admitting only the given roles (admin always)., Yield a scoped session that is always closed., Resolve the authenticated principal.          The real implementation lives in t, require_roles()

### Community 86 - "Community 86"
Cohesion: 0.26
Nodes (4): AssetGateway, Guarantee an asset can be reserved.          Enforces the rule *unavailable asse, Read/write access to the shared ``assets`` table via SQLAlchemy Core., Transition an asset's status. Booking mutates assets only here.

### Community 87 - "Community 87"
Cohesion: 0.22
Nodes (7): ActivityLog, Activity log persistence model., An immutable record of a state-changing action.      Activity logs are append-on, ActivityService, Reusable activity-logging service.  Every state-changing operation across Bookin, Append-only writer/reader for the activity log., Record an action. Flushed (not committed) so it shares the caller's         tran

### Community 88 - "Community 88"
Cohesion: 0.32
Nodes (10): MaintenancePriority, MaintenanceStatus, MaintenanceCreate, MaintenanceRead, MaintenanceReject, MaintenanceResolve, MaintenanceUpdate, Maintenance request API schemas. (+2 more)

### Community 90 - "Community 90"
Cohesion: 0.22
Nodes (8): ActivityLogFlag, ActivityLogRead, Page, PageMeta, Pydantic (v2) request/response schemas for the Audit module., Generic paginated response envelope., _require_non_blank(), _strip_reason()

### Community 91 - "Community 91"
Cohesion: 0.20
Nodes (7): Booking, BookingStatus, _enum_values(), Booking persistence model and workflow enumerations.  Owns exactly one table: ``, The booking workflow states.      Happy path::          PENDING -> APPROVED -> C, Persist enums by their ``.value`` (readable lowercase) in both directions., A time-bounded reservation of an asset, driven through the     approval -> check

### Community 92 - "Community 92"
Cohesion: 0.29
Nodes (5): get_current_user(), Integration seam between the Maintenance module and the shared foundation.  The, Build a FastAPI dependency admitting only the given roles (admin always)., Resolve the authenticated principal.          The real implementation lives in t, require_roles()

### Community 93 - "Community 93"
Cohesion: 0.16
Nodes (6): AssetAuditService, Asset Audit business logic and workflow orchestration.  The service is the only, Managers/admins see every cycle; others only cycles they audit., Assemble the discrepancy report from a cycle's items (pure function)., Stateless orchestrator; the DB session is passed in per call., _utcnow()

### Community 94 - "Community 94"
Cohesion: 0.25
Nodes (7): Activity-log business-rule guards.  The audit trail is append-only: recorded fac, Rule: an audit entry must fully identify actor, action and entity., Rule: an entry can only be flagged once, while still unflagged., Rule: only a flagged, not-yet-acknowledged entry can be acknowledged., validate_can_acknowledge(), validate_can_flag(), validate_record_fields()

### Community 95 - "Community 95"
Cohesion: 0.25
Nodes (7): Notification business-rule guards.  These framework-agnostic guards are the sing, Rule: a notification must be addressed to a concrete recipient., Rule: a notification must carry a non-blank title and message., Rule: only the recipient (or an admin) may read/mutate a notification., validate_can_access(), validate_content(), validate_recipient_id()

### Community 96 - "Community 96"
Cohesion: 0.29
Nodes (5): Page, PageMeta, Shared schema building blocks: pagination and sorting., A generic paginated response envelope., SortOrder

### Community 97 - "Community 97"
Cohesion: 0.25
Nodes (8): AssetStatus, Lifecycle states of an asset (canonical column lives in ``assets``)., AssetKpiBucket, QuickActionKey, Dashboard domain vocabulary — classification enums and mappings.  The Dashboard, The KPI buckets the dashboard reports asset counts in.      The canonical ``asse, Stable identifiers for the quick-action shortcuts the dashboard offers.      The, str

### Community 98 - "Community 98"
Cohesion: 0.17
Nodes (9): MaintenanceService, Maintenance management business logic and workflow orchestration.  The service i, Non-managers only see requests they raised or are assigned to., Only the assigned technician (or an admin) may progress the work., Stateless orchestrator; the DB session is passed in per call., Stateless orchestrator; the DB session is passed in per call., Non-managers only see requests they raised or are assigned to., Only the assigned technician (or an admin) may progress the work. (+1 more)

### Community 99 - "Community 99"
Cohesion: 0.50
Nodes (3): Asset Audit module (self-contained vertical slice).  Implements the ERP asset-au, Mount the Asset Audit router and error handlers onto a FastAPI app., register_routes()

### Community 100 - "Community 100"
Cohesion: 0.50
Nodes (3): Audit module (self-contained vertical slice).  Owns the ``activity_logs`` table, Mount the Audit router and error handlers onto a FastAPI app., register_routes()

### Community 101 - "Community 101"
Cohesion: 0.50
Nodes (3): Booking Management module (self-contained vertical slice).  Owns the asset-reser, Mount the Booking router and error handlers onto a FastAPI app., register_routes()

### Community 102 - "Community 102"
Cohesion: 0.50
Nodes (3): Dashboard module (presentation / aggregation layer).  Read-only. Owns **no** tab, Mount the Dashboard router and error handlers onto a FastAPI app., register_routes()

### Community 103 - "Community 103"
Cohesion: 0.50
Nodes (3): Notifications module (self-contained, reusable vertical slice).  Owns the ``noti, Mount the Notifications router and error handlers onto a FastAPI app., register_routes()

### Community 110 - "Community 110"
Cohesion: 0.13
Nodes (15): _assemble_pdf(), _build_orm_reports(), _enum_coercer(), _OrmReport, _pdf_cell(), _pdf_escape(), _primitive(), Reports aggregation, export, and UI-backend service.  Like the Dashboard, Report (+7 more)

### Community 111 - "Community 111"
Cohesion: 0.22
Nodes (10): AuthenticationError, BookingError, ConflictError, NotFoundError, PermissionDeniedError, Domain exceptions for the Booking module and their FastAPI handlers.  Framework-, Base class for every business-rule error raised by the Booking module., Attach the Booking error handler to a FastAPI application. (+2 more)

### Community 112 - "Community 112"
Cohesion: 0.15
Nodes (11): ExportFormat, NotificationView, Page, PageMeta, Pydantic (v2) schemas for the Reports module.  Reports is a read/aggregation lay, Generic paginated response envelope., The catalogue of reports this module can render and export., The notification inbox tabs the UI backend serves.      ``ALL`` / ``UNREAD`` / ` (+3 more)

### Community 113 - "Community 113"
Cohesion: 0.17
Nodes (7): AuditCycle, AuditItem, _enum_values(), Asset Audit persistence models and workflow enumerations.  Owns exactly two tabl, One asset enrolled in a cycle, assigned to an auditor, awaiting a verdict., Persist enums by their ``.value`` (readable lowercase) in both directions., An audit campaign over a department/location for a fixed date range.

### Community 114 - "Community 114"
Cohesion: 0.21
Nodes (9): AuthenticationError, DashboardError, PermissionDeniedError, Domain exceptions for the Dashboard module and their FastAPI handlers.  Framewor, Base class for every error raised by the Dashboard module., Attach the Dashboard error handler to a FastAPI application., register_exception_handlers(), ValidationError (+1 more)

### Community 115 - "Community 115"
Cohesion: 0.23
Nodes (9): AuthenticationError, NotFoundError, NotificationError, PermissionDeniedError, Domain exceptions for the Notifications module and their FastAPI handlers.  Mirr, Base class for every business-rule error raised by the Notifications module., Attach the Notifications error handler to a FastAPI application., register_exception_handlers() (+1 more)

### Community 116 - "Community 116"
Cohesion: 0.20
Nodes (5): _collect_filters(), export_report(), get_report(), Reports REST endpoints.  Thin by design: every endpoint resolves the current pri, Bundle the generic filter query params; a report picks the ones it honours.

### Community 117 - "Community 117"
Cohesion: 0.18
Nodes (8): ActivityLog, One immutable audit-trail entry describing a workflow action.      Entries are a, Base, MaintenanceRequest, A repair/service request raised against an asset and driven through the     appr, Notification, Notification persistence model., A message delivered to a single user's in-app inbox.

### Community 118 - "Community 118"
Cohesion: 0.33
Nodes (7): BookingStatus, BookingCancel, BookingCreate, BookingRead, BookingReschedule, BookingUpdate, Partial edit of a booking's descriptive fields and/or time window.

### Community 119 - "Community 119"
Cohesion: 0.25
Nodes (6): _clean_tables(), make_token(), Shared pytest fixtures for the Maintenance module.  The module is exercised in c, Factory fixture for inserting stub users/departments/assets., Reset all data between tests for isolation., seed()

### Community 120 - "Community 120"
Cohesion: 0.36
Nodes (3): _AssetReader, Read-only, schema-tolerant access to the shared ``assets`` table.      Mirrors t, ``{department: {status: count}}`` for assets, or ``{}`` if unsupported.

### Community 121 - "Community 121"
Cohesion: 0.29
Nodes (7): _post_create(), test_api_approve_requires_manager_role(), test_api_cannot_approve_twice(), test_api_create_returns_201(), test_api_disposed_asset_rejected(), test_api_full_lifecycle(), test_api_list_and_get_and_delete()

### Community 122 - "Community 122"
Cohesion: 0.47
Nodes (3): health_check(), lifespan(), root()

### Community 123 - "Community 123"
Cohesion: 0.50
Nodes (3): Reports module (presentation / aggregation + UI-backend layer).  Read-only aggre, Mount the Reports router (and the consumed modules' error handlers).      The No, register_routes()

## Knowledge Gaps
- **5 isolated node(s):** `allow`, `Tech Stack`, `Core Modules`, `Tech Stack`, `Core Modules`
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PermissionDeniedError` connect `Community 65` to `Community 64`, `Community 2`, `Community 67`, `Community 4`, `Community 98`, `Community 6`, `Community 66`, `Community 10`, `Community 79`, `Community 60`, `Community 93`, `Community 62`, `Community 63`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `NotFoundError` connect `Community 67` to `Community 97`, `Community 2`, `Community 3`, `Community 4`, `Community 98`, `Community 6`, `Community 66`, `Community 74`, `Community 10`, `Community 76`, `Community 86`, `Community 23`, `Community 60`, `Community 93`, `Community 62`, `Community 63`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `AssetAuditService` connect `Community 93` to `Community 65`, `Community 67`, `Community 10`, `Community 74`, `Community 113`, `Community 23`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `auth()` (e.g. with `_raise()` and `test_cannot_raise_for_disposed_asset()`) actually correct?**
  _`auth()` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AssetAuditService` (e.g. with `NotFoundError` and `PermissionDeniedError`) actually correct?**
  _`AssetAuditService` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `MaintenanceService` (e.g. with `NotFoundError` and `PermissionDeniedError`) actually correct?**
  _`MaintenanceService` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `allow`, `Stand-in mirroring the JWT claim contract (sub, role, department_id).`, `Return a single aggregated router for the whole Workflow module.` to the rest of the system?**
  _347 weakly-connected nodes found - possible documentation gaps or missing edges._