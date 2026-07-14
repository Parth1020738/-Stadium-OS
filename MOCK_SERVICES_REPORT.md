# Mock Services Report

## Overview
Aegis Smart Stadium OS is equipped with full offline capability and mock service modes, allowing developers and QA engineers to test the dashboard, workflows, and integrations without external network calls.

## Verified Modules
- **AI Decision Support**: Forced to mock mode (`ENABLE_MOCK_AI=true`). Responses simulate AI risk mitigation recommendations.
- **Telemetry & Crowd Zones**: Simulated real-time sensor streams feed into dashboards through local databases and fallback routines.
- **Incident & Shift Tracking**: Handled via local SQLite state; if database endpoints fail, clean mock structures populate the tables immediately.
- **Knowledge & Documents**: Fallback to predefined lists of operating procedures if backend API query fails.
- **System Health**: System performance statistics simulate memory, database connection, and CPU load.
