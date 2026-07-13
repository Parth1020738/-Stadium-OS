# Aegis Operations Dashboard & Live Feed

The Aegis Operations Dashboard is the real-time visualization layer of the Aegis Smart Stadium OS, coordinating feeds, safety alerts, transit systems, volunteer shifts, and safety metrics.

---

## 1. Real-Time Streaming Architecture

Live updates bypass expensive SQL database scans by checking **Redis Materialized Views** updated by the ingestion engine:

```
 [Kafka Events] ──> [AggregationService] ──> [Redis Materialized Views]
                                                      │
                                                      ▼
 [WebSocket Clients] <── [WebSocket Router] <── [MetricsService]
```

Clients subscribe to streaming updates via standard WebSockets.

---

## 2. WebSocket Channels & Subscription Topics

All WebSocket connections utilize sub-protocols for token auth and expect query parameter tokens:
`/ws/dashboard/[channel]?token=[JWT]`

| Endpoint | Channel Target | Description |
| :--- | :--- | :--- |
| `/ws/dashboard` | `overview` | Unified system state metrics & active commands |
| `/ws/dashboard/crowd` | `crowd` | Live crowd snapshot densities by zone |
| `/ws/dashboard/incidents` | `incidents` | Active security and safety incidents |
| `/ws/dashboard/transit` | `transit` | Shuttles delays, parking lots capacity |
| `/ws/dashboard/volunteers` | `volunteers` | Active volunteers shifts availability |
| `/ws/dashboard/accessibility` | `accessibility` | Real-time barriers elevator alerts |
| `/ws/dashboard/alerts` | `alerts` | Prioritized warning and evacuations flags |
| `/ws/dashboard/metrics` | `metrics` | Unified KPI updates (e.g. density) |

---

## 3. Redis Materialized Views Directory

The dashboard reads keys directly from Redis with auto-fallback to DB queries:
- `stadium:zone:{zone_id}:crowd` (hash: `estimated_count`, `density_level`)
- `stadium:zone:{zone_id}:occupancy` (string: count)
- `stadium:incidents:active` (set: active IDs)
- `stadium:incident:{inc_id}` (hash: incident properties)
- `dashboard:metrics:average_density` (string: overall average)
- `dashboard:metrics:active_incidents_count` (string: count)
