# Phase 12E: Autonomous Multi-Agent Stadium Operations Platform - Implementation Plan

This implementation plan details the architectural and procedural changes required to implement the Phase 12E Multi-Agent AI system.

## Current Architecture
The current Aegis OS AI Copilot relies on a single-agent schema. The `AIOrchestrator` uses `GeminiService` directly or via a mock response mapper to answer queries based on a simple context loaded from `ContextBuilder`.

## Multi-Agent Architecture
We are transitioning to a collaborative multi-agent architecture composed of:
1. **Master AI Coordinator**: Receives operator queries, coordinates agent execution, aggregates inputs, performs conflict resolution, maps unified timelines, and generates briefings.
2. **Ten Specialized Agents**:
   - **Crowd Agent**: Dedicated to monitoring crowd flow, ticket validations, and bottlenecks.
   - **Incident Agent**: Focuses on live incidents, priority events, and response dispatch.
   - **Transit Agent**: Handles shuttle statuses, metro departures, and transit schedules.
   - **Volunteer Agent**: Handles shift structures, steward allocations, and volunteer locations.
   - **Accessibility Agent**: Focuses on accessibility barriers, elevators, escalators, and ADA routes.
   - **Sustainability Agent**: Focuses on energy conservation, waste management, and utility setups.
   - **Security Agent**: Manages security alerts, gates, and perimeter protection.
   - **Medical Agent**: Manages medical incidents and first aid locations.
   - **Weather Agent**: Evaluates weather changes and forecasts.
   - **Command Agent**: Prepares commands and triggers command logs.

## Agent Communication Flow
- **Broadcast**: Master Coordinator translates queries into instructions for relevant agents.
- **Evaluation**: Agents run concurrently using their specialized templates and scopes.
- **Coordination/Memory**: Agents can trigger downstream constraints (e.g. Crowd Agent bottleneck -> Transit Agent shuttles adjustment).
- **Synthesis**: The coordinator resolves conflicting recommendations and formats a single timeline output.

## Conflict Resolution Strategy
If two agents disagree (e.g., Gate C open vs. close):
1. **Weights Assignment**: Safety/Medical (9) > Security (8) > Crowd Flow (7) > Transit (6) > Sustainability (4).
2. **Impact Calculation**: Explanation logic outputs why a safety action overrides a resource optimization action, displaying both sides clearly.

## Testing Strategy
- Unit tests for each agent.
- Integration tests for the Master Coordinator.
- API endpoint validation tests.
- Playwright/E2E tests for the frontend page `/mission-control`.
