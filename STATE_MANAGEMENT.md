# State Management Architecture

This document describes how state is structured, managed, and synchronized between client modules and the backend.

---

## 1. State Division Strategy

We divide state into two categories:

```
┌────────────────────────────────────────────────────────┐
│                      CLIENT STATE                      │
├───────────────────────────┬────────────────────────────┤
│   ASYNCHRONOUS SERVER     │     EPHEMERAL CLIENT       │
│          STATE            │           STATE            │
│   (Managed by React Query)│    (Managed by Zustand)    │
│                           │                            │
│ ┌──────────────────────┐  │  ┌──────────────────────┐  │
│ │ - Rest API Responses │  │  │ - Auth Token Context │  │
│ │ - Incident Records   │  │  │ - Sidebar Toggle     │  │
│ │ - Volunteer Shifts   │  │  │ - User Preferences   │  │
│ │ - Transit Stop Data  │  │  │ - Socket Messaging   │  │
│ └──────────────────────┘  │  └──────────────────────┘  │
└───────────────────────────┴────────────────────────────┘
```

---

## 2. Server State (TanStack Query)

TanStack Query manages fetching, caching, and updating server-side data:
*   **Query Keys**: Structured hierarchically to allow targeted cache invalidation:
    *   `['incidents']` (all incidents)
    *   `['incidents', 'list', { status: 'Open' }]` (filtered incident lists)
    *   `['incidents', 'details', id]` (specific incident detail view)
    *   `['volunteers', 'statistics']` (volunteer KPIs)
*   **Mutations**: Post-mutations (creating comments, resolving incidents) trigger query cache invalidation via `queryClient.invalidateQueries`.

---

## 3. Ephemeral Client State (Zustand)

Zustand stores are used for light-weight client-side data:

### Auth Store (`useAuthStore`)
Stores the authenticated user profile, active JWT Access Token, and provides action handlers for login, session expiry, and logging out.

### UI Settings Store (`useUiStore`)
Manages structural dashboard configurations, collapsible side navigation bars, active map zoom scopes, active tabs, and layout configurations.

### WebSocket Telemetry Store (`useTelemetryStore`)
Buffers active WebSocket update events. This store captures telemetry events from stream packets and maintains the local state of system health and live dashboard widgets.
