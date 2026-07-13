# Transit Management Service Audit Resolution Report

This document details the resolutions applied to the findings identified in the Independent QA Audit (`TRANSIT_MANAGEMENT_QA_AUDIT.md`) for the Transit Management Service (Phase 8).

---

## 1. Database & Migrations

### 1.1 Optimistic Locking & Soft Delete
* **Findings Resolved**: Added support for soft deletes and optimistic locking concurrency controls to the many-to-many relationship table `TransitRouteStop` (association between route and stops).
* **Telemetry Versioning**: Removed versioning and optimistic locking columns from `TransitTelemetry` since telemetry is append-only.
* **Alerts Schema**: Added the `TransitAlert` database table structure to allow persisting all ingested alerts before publishing them to downstream channels.
* **Alembic Migration**: Created the migration script `2026_07_12_0930-578a6f3b2d1c_add_indexes_and_locking.py` defining the required indexes and columns.

### 1.2 Composite Indexes
Added high-efficiency composite indexes for frequent search parameters:
* `ix_transit_telemetry_vehicle_timestamp` on `(vehicle_id, timestamp)`
* `ix_transit_etas_trip_stop` on `(trip_id, stop_id)`
* `ix_transit_occupancies_vehicle_stop` on `(vehicle_id, stop_id)`

---

## 2. Repository Layer

* **Findings Resolved**: Eliminated direct database context `self.db.add` / `self.db.flush` service bypasses in `AssignmentService` and elsewhere.
* **New Repositories**: Created and registered repository classes for all remaining Transit entities:
  * `OperatorRepository`
  * `HubRepository`
  * `ShuttleRepository`
  * `VehicleAssignmentRepository`
  * `DriverAssignmentRepository`
  * `DelayRepository`
  * `OccupancyRepository`
  * `QueueRepository`
  * `ETARepository`
  * `IncidentLinkRepository`
  * `AlertRepository`
* **Query Ordering**: Ensured all repositories returning list data apply explicit ordering (`order_by(Model.id)`) to enforce deterministic pagination.

---

## 3. Business Logic & Error Handling

### 3.1 Live Database Queries
* **Statistics**: Replaced the hardcoded stats dictionary in `TransitService.get_statistics()` with real database queries counting active routes, vehicles, completed trips, and calculating the average delay minutes dynamically.
* **Hub Occupancy**: Modified `get_hub_occupancy()` to fetch real density records from the `TransitOccupancy` table in the database and calculate levels dynamically based on passenger density thresholds.

### 3.2 Concurrency & Transaction Safety
* **Retry Loop**: Wrapped volatile parking occupancy updates in `ParkingService.update_occupancy()` in an exponential backoff retry loop (maximum 3 retries) catching `StaleDataError`.
* **Integrity Error Mapping**: Caught database-level `IntegrityError` in creation methods (such as routes, vehicles, and schedules) and returned clean FastAPI `HTTP_409_CONFLICT` or `HTTP_400_BAD_REQUEST` status codes instead of leaking database errors.
* **Alert Persistence**: Persisted alert payloads in the database using the new `AlertRepository` before publishing them downstream.

---

## 4. Kafka & Messaging

* **Correlation ID Propagation**: Propagated incoming request correlation IDs (`correlationId`) to Kafka events published via `publish_kafka_event()`.
* **Topic Isolation**: Separated the shared transit event topic into distinct, dedicated channels:
  * `transit.alerts` for system alerts
  * `transit.egress_pacing` for pacing commands

---

## 5. REST API & Security

### 5.1 Route Parameter Casing
* Normalized camelCase route parameter `{hubId}` to snake_case `{hub_id}` in `/api/v1/transit/hubs/{hub_id}/occupancy` to match the REST style guide.

### 5.2 Global Exception Handler
* Registered a global exception handler in `backend/app/main.py` that intercepts `SQLAlchemyError` exceptions, logs details securely, and returns a sanitized HTTP 500 error response to prevent leaking internal database schemas.

### 5.3 RBAC Scope Checking
* Updated `ScopeChecker` in endpoints to enforce explicit scope checks (e.g. `transit:pacing`) on `Staff` roles, removing the broad bypass while preserving `Admin` level capabilities.

---

## 6. Testing & Verification

* **Dynamic Assertions**: Removed hardcoded database primary key assertions in tests, replacing them with dynamic queries from the test database.
* **Integration Tests**: Added new unit tests covering concurrency retries, database `IntegrityError` mapping, and Kafka exception rollback safety.
* **Verification Status**: All 4 integration test groups run and pass successfully:
  ```bash
  tests/backend/test_transit_api.py ....
  ================== 4 passed in 65.43s ==================
  ```
