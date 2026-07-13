# Aegis Command Gateway & Command Bus

The Aegis Command Gateway is the centralized orchestration engine for the Aegis Smart Stadium OS. It aggregates, validates, and coordinates command execution across all core services (Incident, Volunteer, Transit, Accessibility, and Knowledge).

---

## 1. System Integration Architecture

All cross-service operations and destructive manual mutations flow through the Command Gateway to ensure transactional consistency, unified RBAC authorization, event streaming, and immutable audit logs.

```
                      [API clients / UI]
                             │
                             ▼
                    [Command REST APIs]
                             │
                             ▼
                 [CommandGatewayService]
                             │
            ┌────────────────┴────────────────┐
      (Is Critical?)                     (Is Normal?)
           /                                 \
          ▼                                   ▼
 [Status: Pending]                    [Status: Approved]
  (Requires Approval)                         │
          │                                   ▼
          │                        [CommandBus / Dispatch]
          ▼                                   │
[Operator Approve Cmd]                        ▼
          │                       [Execution (Target Services)]
          │                                   │
          └────────────────┬──────────────────┘
                           ▼
              [Audit Log & Kafka Events]
```

---

## 2. Command Execution Lifecycle

1. **Submit**: A user submits a command via the REST API.
2. **Duplicate Detection**: The system sets a 5-second Redis idempotency lock using the payload parameters to prevent duplicate executions.
3. **Authorization**: Validates user JWT and verifies role scopes via FastAPI's `RoleChecker`.
4. **Approval Routing**:
   - **Normal Commands**: Automatically marked `Approved` and queued for execution.
   - **Critical Commands** (`EMERGENCY_EVACUATION`, `GATE_RATE_OVERRIDE`, `ACCESSIBILITY_OVERRIDE`, `EMERGENCY_BROADCAST`): Marked `Pending` and await secondary verification. Expires in 10 minutes if unapproved.
5. **Execution**: Dynamic routing to the designated domain service (e.g., `IncidentService`, `AssignmentService`, `RouteService`).
6. **Persistence**: Writes states, execution outcomes, and immutable audit trails to PostgreSQL.
7. **Event Broadcast**: Publishes events (e.g., `command.created`, `command.executed`, `command.failed`) to Kafka.

---

## 3. Supported Commands Directory

| Command Type | Target Service | Parameters | Critical? |
| :--- | :--- | :--- | :--- |
| **Dispatch Volunteer** | `VolunteerService` | `shift_id`, `volunteer_id` | No |
| **Create Incident** | `IncidentService` | `title`, `description`, `severity`, `priority`, `category` | No |
| **Resolve Incident** | `IncidentService` | `incident_id`, `version_id` | No |
| **Accessibility Override** | `AccessibilityService` | `venue_id`, `barrier_type`, `severity`, `zone_id`, `location_label`, `latitude`, `longitude` | Yes |
| **Emergency Evacuation** | `CommandGateway` | `zone` | Yes |
