# Frontend Authentication & Authorization Guide

This guide details how user authentication, page security, and role-based permissions are enforced.

---

## 1. Directory Layout

The core files responsible for user security are:
*   [authStore.ts](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/store/authStore.ts): State container mapping credentials to roles and capability sets.
*   [api-client.ts](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/lib/api-client.ts): Axios interceptors for JWT injection and silent token rotation.
*   [DashboardShell.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/components/common/DashboardShell.tsx): Client-side security wrapper checking login lifetimes, idle timeout warners, and visibility updates.
*   [Guards.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/components/common/Guards.tsx): Custom guards `<RoleGuard>` and `<PermissionGuard>`.

---

## 2. Testing Credentials

Use the registration panel at `/register` or login directly with the standard backend operator roles:
*   **Steward**: Read-only tracking.
*   **Operator**: Write access on shifts, incidents, transit logs.
*   **OperationsManager**: Operator access + command approvals.
*   **Administrator**: Full settings bypass and override.
