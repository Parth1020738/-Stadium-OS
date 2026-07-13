# JWT Authentication Flow

This document details the token lifecycle, silent token rotation, and Axios interceptor queue mechanism.

---

## 1. Sequence Diagrams

```
User Action              Zustand Store          Axios Interceptor          FastAPI API
───────────              ─────────────          ─────────────────          ───────────
   │                           │                        │                       │
   │ ── Log in Credentials ──► │                        │                       │
   │                           │ ── POST /auth/login ──►│                       │
   │                           │                        │ ── Send Request ────► │
   │                           │                        │ ◄── Return 200 OK ─── │
   │                           │ ◄── Store JWT tokens ─ │                       │
   │                           │                        │                       │
   │ ── View dashboard ──────► │                        │                       │
   │                           │ ── GET /incidents ────►│                       │
   │                           │                        │ ── Send + Header ───► │
   │                           │                        │ ◄── Return 401 ────── │
   │                           │                        │                       │
   │                           │ ── Refresh Token ─────►│                       │
   │                           │                        │ ── POST /auth/refresh►│
   │                           │                        │ ◄── Return 200 OK ─── │
   │                           │ ◄── Update JWT tokens ─│                       │
   │                           │                        │                       │
   │                           │ ── Retry original ────►│                       │
   │                           │                        │ ── Send + New HDR ──► │
   │                           │                        │ ◄── Return 200 Data ─ │
```

---

## 2. Axios Request & Response Interceptors

To support this without duplicate requests:
1.  **Request Interceptor**: Evaluates the Zustand state (`accessToken`). If present, attaches the `Authorization: Bearer <token>` header to the request configuration.
2.  **Response Interceptor**: Listens for HTTP `401 Unauthorized` responses. If caught:
    *   Queues the pending request config in a `failedQueue`.
    *   Triggers a single `/auth/refresh` query to rotate keys.
    *   If key rotation succeeds, updates store headers, resolves all queued items, and retries the original requests.
    *   If rotation fails, clears all store variables, deletes localStorage tokens, and redirects the operator to `/session-expired`.
