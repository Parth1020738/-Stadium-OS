# Security Analysis Report

This report outlines the security measures implemented in the frontend.

---

## 1. Token Handling & Session Protection

*   **Silent Token Rotation**: The application rotated expired access tokens seamlessly by sending them to `/auth/refresh` without exposing refresh tokens to `localStorage` or page logs.
*   **Idle Timeout**: User activity is monitored via event listeners. If no activity occurs for 15 minutes, the user is automatically logged out. Tab synchronization is handled via browser `BroadcastChannel` messages.

---

## 2. Authorization (RBAC)

*   **Route Protection**: Guards redirect unauthenticated users to `/login` and unauthorized users to `/403`.
*   **Action Restriction**: Override actions (e.g. Turnstile egress pacing configuration and command approvals) are disabled and hidden for unauthorized roles (e.g. `Steward`).
