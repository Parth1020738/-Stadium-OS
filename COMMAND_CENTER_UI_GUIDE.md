# Operations Command Center Style Guide

This guide details the specifications of the overrides command console.

---

## 1. Approval and Actions Panel
The side panel handles dynamic command details and approvals:
*   **Payload formatting**: Pre-formatted inline JSON code blocks displaying exact parameters.
*   **Actions configuration**: Split green/red buttons to Approve/Reject with comments inputs.
*   **Permissions**: Restricts click events based on authentication headers.

---

## 2. Command Logs Table
Displays logs containing:
*   **Command Override Type** (e.g. `TurnstileUnlock`, `ShuttleDispatch`).
*   **Operator creator details** (Creator ID, correlation IDs).
*   **Execution statuses** (Pending, Approved, Rejected, Completed, Failed).
