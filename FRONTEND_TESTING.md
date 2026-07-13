# Frontend Testing Strategy

This document details the test runner configuration, mock strategies, and coverage goals for the Command Center.

---

## 1. Testing Framework Stack

Our test plan spans three levels:
1.  **Unit Tests (Vitest + React Testing Library)**: Tests basic React primitives, custom hooks (e.g. `useWebSocket`), state stores (Zustand), and layout utilities.
2.  **Integration Tests (Vitest + MSW)**: Mocks network traffic at the service boundary using Mock Service Worker (MSW) to verify dashboard telemetry, form submit states, and RBAC guards.
3.  **End-to-End Tests (Playwright)**: Asserts cross-component flows, auth redirects, real-time map interactions, and two-person approval workflows.

---

## 2. Test Execution Commands

Run configurations are defined in the workspace:
*   **Unit & Integration Tests**:
    ```bash
    pnpm run test
    ```
*   **Coverage Reports**:
    ```bash
    pnpm run test:coverage
    ```
*   **E2E Tests (Interactive)**:
    ```bash
    pnpm exec playwright test --ui
    ```
*   **E2E Tests (CI Mode)**:
    ```bash
    pnpm exec playwright test
    ```

---

## 3. Mocking Strategy

### Mock Service Worker (MSW)
MSW is used to intercept all Axios calls under `/api/v1/*`. Handlers return mock data representing the database schema:
*   `/api/v1/auth/login` (Success/Fail cases).
*   `/api/v1/incidents` (Paginated items).
*   `/api/v1/dashboard/metrics` (CPU/RAM telemetry).

### WebSocket Mocking
For testing real-time components, we use a custom server mock utility `MockWebSocketServer` that accepts a connection, validates the mock JWT query param, and sends simulated telemetry events periodically.
