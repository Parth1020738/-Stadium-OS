# Aegis Smart Stadium OS: Phase 10 - Security, Performance, & Risk Analysis

This document details the system safety boundaries, permission matrices, performance optimizations, and architectural risks for the Operations Command Center.

---

## 1. Security Architecture & Authorization

### 1.1 Permission Matrix (RBAC)

The command APIs require granular roles to prevent unauthorized actions:

| Action / Command | Required Scope / Role | Multi-Step Approval? | Audit Logged? |
| :--- | :--- | :--- | :--- |
| **View Live Telemetry** | `stadium:read` / Operator, Steward | No | No |
| **Assign / Redeploy Steward** | `volunteer:assign` / Shift Lead, Operator | No | Yes |
| **Dispatch Transit Shuttle** | `transit:dispatch` / Transit Dispatcher | No | Yes |
| **Override ADA Route Block** | `accessibility:override` / Accessibility Lead | Yes | Yes |
| **Escalate/Close Incident** | `incident:write` / Operator, Command Director | No | Yes |
| **Force Gate Rate Limits** | `command:gate_limit` / Command Director | Yes | Yes |
| **Evacuation Command** | `command:evacuate` / Command Director | Yes (Secondary Sign-off) | Yes (Immutable) |

### 1.2 Multi-Step Authorization for Critical Commands
For highly critical commands (e.g., `Evacuation Command`, `Force Gate Rate Limits`):
1. **Initiation**: The Command Director triggers the action.
2. **Pending State**: The system places the command in a `PENDING_APPROVAL` queue.
3. **Verification**: A secondary validation panel appears on the screen of the Deputy Commander.
4. **Approval**: Once the Deputy Commander enters their credentials/JWT verification, the command is released for execution.
5. **Logging**: The system writes a single JSON audit log entry containing both operators' signatures.

---

## 2. Performance & Scaling Strategy

To maintain sub-second response times under the load of 80,000 active fans and thousands of sensors:

### 2.1 API Optimization & Database Protection
- **N+1 Prevention**: All Django/SQLAlchemy database queries must utilize pre-fetching strategies (e.g., `.select_related()` and `.prefetch_related()` in Django) to resolve object relations in a single query.
- **Index Usage**: Primary lookup columns (`ZoneId`, `EventId`, `Status`, `IsActive`) are indexed using PostgreSQL B-Trees. Spatial coordinates (GPS) are indexed via GiST spatial indexing.
- **Pagination**: All list endpoints default to cursor-based pagination to prevent query timeouts on massive event tables.
- **Batch Writes**: Telemetry data (such as entry scans and GPS coordinates) is buffered in Redis streams and flushed to PostgreSQL in bulk chunks (e.g., every 500 rows or 2 seconds) via background workers.

---

## 3. Risk Assessment & Mitigations

| Risk Domain | Identified Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Performance** | Database lock contention during peak egress (simultaneous writes). | High | Buffer writes via Redis Streams; decouple read queries to denormalized Redis read models. |
| **Security** | Operator session hijacking or compromised Command API credentials. | Critical | Enforce JWT token expiration (15 mins), hardware IP pinning, and mandatory multi-step approvals for destructive commands. |
| **Operational** | Network latency / WAN disconnect to cloud LLM during critical triage. | High | Fall back to local rule-based matching models and edge inference cache if cloud latency exceeds `1000ms`. |
| **Scalability** | "Thundering Herd" of 80,000 spectator apps requesting routing updates simultaneously during transit failure. | High | Implement random jitter in refresh loops, rely on CDN-cached static route maps, and push updates in geofenced phases. |
| **AI Fallibility** | LLM Hallucinations in Emergency SOP retrieval. | Critical | Enforce a strict "Grounding Validator" that regex-checks RAG source documents before rendering recommendations; block raw text output. |
