# WebSocket Architecture

This document defines the WebSocket communication architecture, connection management, channel topologies, and error recovery policies for the Command Center.

---

## 1. WebSocket Endpoint Mapping

The Aegis Smart Stadium OS exposes distinct WebSocket routes requiring authentication via query parameters:

| Backend WebSocket Route | Active Channel | Payload Type | Description |
| :--- | :--- | :--- | :--- |
| `/ws/dashboard` | `overview` | System Overview | Broad operational summaries. |
| `/ws/dashboard/crowd` | `crowd` | Crowd Telemetry | Live counts, zone density level updates. |
| `/ws/dashboard/incidents` | `incidents` | Active Incidents | Updates on status, priority, and creation. |
| `/ws/dashboard/transit` | `transit` | Transit Telemetry | Fleet locations and ego PAC schedules. |
| `/ws/dashboard/volunteers` | `volunteers` | Shift updates | Active staff presence. |
| `/ws/dashboard/accessibility` | `accessibility` | Barrier Updates | Barriers and path alterations. |
| `/ws/dashboard/alerts` | `alerts` | System Alarms | High priority warnings. |
| `/ws/dashboard/metrics` | `metrics` | CPU / RAM / Kafka | System level resource usage. |

---

## 2. Client Connection Manager (`WebSocketService`)

To manage resources, we implement a centralized client-side service:
*   **Authentication**: Appends the active JWT token as a query parameter (e.g. `ws://localhost:8000/ws/dashboard/metrics?token=JWT_ACCESS_TOKEN`).
*   **Heartbeat / Keepalive**: Sends a `"ping"` payload every 30 seconds. If the backend fails to respond with `"pong"`, the client schedules a connection drop and restart.
*   **Reconnection Manager**: Implements an exponential backoff reconnect policy (initial delay: 1s, doubling up to a maximum of 30s) to prevent overwhelming the gateway during outages.
*   **Offline/Online Detection**: Uses window event listeners (`window.addEventListener('offline')`) to gracefully shift elements to static fallback states and alert users via status banners.
