# Frontend Security Architecture

This document describes authentication, authorization, session lifecycle, and data-protection protocols on the client application.

---

## 1. Authentication Flow & Lifecycle

The Aegis Smart Stadium OS frontend integrates with the existing JWT-based backend:

```
  Client (React App)                          FastAPI Backend Auth Service
  ──────────────────                          ────────────────────────────
          │                                                 │
          │ ─── POST /api/v1/auth/login (Credentials) ────► │
          │ ◄── Return (Access Token & Refresh Token) ────── │
          │                                                 │
  (Store Refresh Token                                      │
   in Secure Cookie or Storage)                             │
          │                                                 │
          │ ─── GET /api/v1/incidents (Access Token) ─────► │
          │ ◄── Return Status 401 Unauthorized (Expired) ── │
          │                                                 │
          │ ─── POST /api/v1/auth/refresh (Refresh Token) ─► │
          │ ◄── Return New (Access Token & Refresh Token) ── │
          │                                                 │
          │ ─── GET /api/v1/incidents (New Access Token) ──► │
          │ ◄── Return Data ──────────────────────────────── │
```

---

## 2. Token Storage & Protection

*   **Access Token**: Stored in in-memory client state (Zustand `authStore`). Since it is only held in runtime memory, it is protected from XSS persistence attacks.
*   **Refresh Token**: Saved in secure, HTTP-only, SameSite cookies or secure storage mapped to `/api/v1/auth/refresh` requests.
*   **Token Refresh Interceptor**: If any API query encounters a `401 Unauthorized` response code, a queued interceptor intercepts the request, calls `/api/v1/auth/refresh` to secure a fresh access token, updates the `authStore`, and automatically retries the original request.

---

## 3. Client-Side Role-Based Access Control (RBAC)

Authentication state resolves a list of matching user roles:
*   `Administrator`: Complete read/write access and approval override.
*   `OperationsManager`: Operations module write and command approvals.
*   `Operator`: Module write access, cannot approve queue commands.
*   `Steward`: Read-only views, incident reporting, and volunteer shift presence validation.

### UI Element Conditionals
*   Menus and sidebar items are conditionally rendered using user roles.
*   Interactive elements (buttons, forms) use a `<ProtectedElement>` component:
    ```tsx
    <ProtectedElement roles={['Administrator', 'OperationsManager']}>
      <Button onClick={handleCommandApproval}>Approve Command</Button>
    </ProtectedElement>
    ```

---

## 4. Route Security Guards

*   **Middleware Protection**: Dynamic routes check active sessions. Users navigating without valid tokens are redirected to the `/login` route.
*   **Role Authorization**: Routes check role constraints before rendering components (e.g. `/command-center` requires `Operator`, `Administrator`, or `OperationsManager`).
