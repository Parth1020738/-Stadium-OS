# Frontend Role-Based Access Control (RBAC)

This document describes how roles map to scopes and how route-level access is enforced in the user interface.

---

## 1. Role-to-Scope Definition Map

The frontend derives permission scopes dynamically from the user's active role context:

```typescript
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  Steward: [
    "transit:read",
    "accessibility:read",
    "incidents:read",
    "volunteers:read"
  ],
  Operator: [
    "transit:read", "transit:write",
    "accessibility:read", "accessibility:write",
    "incidents:read", "incidents:write",
    "volunteers:read", "volunteers:write"
  ],
  OperationsManager: [
    "transit:read", "transit:write",
    "accessibility:read", "accessibility:write",
    "incidents:read", "incidents:write",
    "volunteers:read", "volunteers:write",
    "commands:approve"
  ],
  Administrator: [
    "transit:read", "transit:write",
    "accessibility:read", "accessibility:write",
    "incidents:read", "incidents:write",
    "volunteers:read", "volunteers:write",
    "commands:approve",
    "admin:*"
  ]
};
```

---

## 2. Guard Component Declarations

We implement two types of security guards:

### `<RoleGuard allowedRoles={['Operator', 'OperationsManager']}>`
Hides or displays elements based on the exact roles matching the decoded JWT token.
```tsx
<RoleGuard allowedRoles={["Administrator"]} fallback={<div>Admin panel only</div>}>
  <SystemSettingsControl />
</RoleGuard>
```

### `<PermissionGuard permission="commands:approve">`
Hides or displays elements based on capability keys.
```tsx
<PermissionGuard permission="commands:approve">
  <button onClick={handleApprove}>Approve Command</button>
</PermissionGuard>
```
If a user is logged in as an Administrator, all permission guards automatically evaluate to true via the **Administrator Bypass** check.
