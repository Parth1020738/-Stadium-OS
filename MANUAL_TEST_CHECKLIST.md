# Aegis Smart Stadium OS — Manual Test Checklist

This checklist documents the manual/automated walkthrough verification of the Aegis Smart Stadium OS interface, components, and pages.

| Page / Component | Expected Result | Actual Result | PASS / FAIL | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **Login Page** | Redirects if unauthenticated. Renders clean login form. Successfully accepts operator credentials and logs user in. | Redirects successfully. Logged in using `operator@aegis.com` / `password`. | **PASS** | Authentication cookies/JWT token stored in local storage and auth state. |
| **Operations Dashboard** | Renders map widget, system health cards, and live ingestion event logs. Websocket connects. | Loaded map widget showing stadium layout. WebSockets connected to `metrics` and `alerts`. | **PASS** | Map renders SVG zones correctly. Health cards show active status. |
| **Crowd Heatmap** | Shows camera occupancy metrics, color-coded heat density levels, and charts. | Loaded camera telemetry cards. Heat maps render with appropriate gradient markers. | **PASS** | Live ingest tracking shown at the bottom. |
| **Incident Management** | Shows active incidents. Offers a form to raise incidents, input description, select priority, and submit. | Form is fully inputtable. Raised incident "Security Guard dispatch request" at Gate 3. | **PASS** | Incident appeared in the list instantly. |
| **Volunteer Scheduling** | Shows volunteers, their current status, shifts, and attendance logs. Enables interactive shift assignment. | Shift card list visible. Clicked on shift card details and triggered volunteer allocation. | **PASS** | Shift cards populate with color indicators based on status. |
| **Transit Module** | Shows fleet transit status, current dispatch locations, route barriers. Allows vehicle dispatch. | Dispatched mock vehicle. Dispatched route update shown on logs panel. | **PASS** | Ingestion status indicates mock telemetry updates. |
| **Accessibility Routing** | Renders route recommendations, barrier alerts, and re-routing indicators. | Renders interactive barrier list. Recalculated path updates are visible. | **PASS** | Correctly retrieves barrier information from the backend. |
| **AI Playbooks** | Shows recommended playbooks based on semantic matching. Generates confidence scores and risk analysis. | AI recommendation cards render. Displays confidence scores (e.g. 94%) and risk score (e.g. Medium). | **PASS** | Uses mock provider configured in environment. |
| **Command Center** | Multi-operator gateway page. Renders pending commands, approval queues, and command action logs. | Shows pending actions. Double approval workflow interactive controls render. | **PASS** | Clicked approval confirmers. |
| **Settings** | Allows customizing profile preferences, system parameters, toggling alerts, and saving. | Save configuration form is fully functional. Confirmed updates persist. | **PASS** | Triggers settings update API request. |
| **Logout** | Safely clears the session token and redirects the operator to `/login`. | Sessions cleared and immediately redirected to login page. | **PASS** | Tab sync logout broadcast worked. |
| **Knowledge Base** | View documents and emergency playbooks. | Returns 404 Page Not Found. | **FAIL (Missing page)** | Folder not present in Next.js project codebase. |
| **Reports Summary** | View stadium telemetry analytics and reports. | Returns 404 Page Not Found. | **FAIL (Missing page)** | Folder not present in Next.js project codebase. |
| **System Health** | View infrastructure health logs and metrics. | Returns 404 Page Not Found. | **FAIL (Missing page)** | Folder not present in Next.js project codebase. |
