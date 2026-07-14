# Phase 12C - GenAI Operational Intelligence & Autonomous Action Engine Implementation Plan

## 1. Current Architecture
- **Backend Infrastructure**: Python FastAPI backend with modular service layers, including `AIOrchestrator`, `ContextBuilder`, `GeminiService`, `PromptManager`, and database repositories.
- **Frontend Workspace**: Next.js client featuring a `/copilot` command panel that reads Server-Sent Event (SSE) streams and renders chat state.
- **Command Center**: Database-backed command dispatch queue (`commands.py` API endpoints) for submitting, approving, auditing, and executing system overrides.

## 2. Missing AI Capabilities
- **Explainable Structured Decisions**: The AI response must systematically separate decisions into Priority, Expected Outcome, Summary, Reasoning, Confidence, Supporting Evidence, Recommended Actions, Risks, and Alternatives.
- **Interactive Action Cards**: The front-end must transform recommendations into triggerable action cards (e.g., executing commands directly to the backend Command Center).
- **Multi-Step Workflows**: Chained command execution workflows (e.g., Step 1: Open Gate -> Step 2: Dispatch Volunteers) that the user can approve step-by-step.
- **Multilingual Support**: Real-time translation of responses into Spanish, French, Portuguese, and Arabic.
- **Incident & Crowd Intelligent Routing**: Real-time evaluation of severity, impact, response teams, and routing bypass recommendations.

## 3. Proposed Changes

### Backend Changes
- **[gemini_service.py](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/backend/app/ai/gemini_service.py)**:
  - Add standard structures for all 14 intelligence categories (Incident, Crowd, Volunteers, Transit, Accessibility, Executive Briefings, Workflows).
  - Support workflow generation responses in mock mode, yielding chained operations JSON/Markdown.
  - Integrate multilingual keyword detectors to auto-translate summaries, reasoning, and actions into requested languages.
- **[context_builder.py](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/backend/app/ai/context_builder.py)**:
  - Enrich context generation by pulling from active alerts list, shift logs, operator roles, and command history.

### Frontend Changes
- **[page.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/app/copilot/page.tsx)**:
  - Add language selector controls at the top of the interface.
  - Implement a collapsible Workflow Panel rendering chained actions step-by-step with individual [Approve] / [Skip] buttons.
- **[components.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/app/copilot/components.tsx)**:
  - Build the explainability sidebar displaying "Why?", "How?", supporting telemetry metrics, and rejected alternatives.
  - Enhance `ActionCards` to issue actual POST requests to `/api/v1/commands` to create system commands, triggering the Command Center approval logs.

## 4. Operational Impacts

- **Database Impact**: Zero database migrations or schema updates. All operations read through the read-only Context Builder and audit records write to the existing `ai_audits` or `commands` log tables.
- **API Impact**: Zero new API endpoints. We will extend the existing Copilot POST `/copilot` and GET `/stream` routes to support dynamic workflow outputs and translations.
- **Command Center Integration**: Clicked actions will execute standard Command Center dispatch pipelines (`CommandGatewayService`), keeping all audits, security role constraints, and pending approval workflows intact.
- **Security & RBAC Impact**: Role-based access checks (`write_checker`, `approve_checker`) are enforced on the backend commands API. If a steward tries to execute an action requiring operator privilege, the backend will return a 403, and the Copilot UI will gracefully display a permission denial toast.

## 5. Testing & Verification Strategy
- **Backend Tests**: Create `tests/backend/test_genai_operational_intelligence.py` covering workflow chaining, translation logic, and mock response validation.
- **Frontend Tests**: Run linter and next build to guarantee type safety and compilation.
- **Regression Checks**: Run `python tests/backend/run_tests.py` to confirm zero regressions across auth, transit, and crowds.

## 6. Execution Order
1. Extend `gemini_service.py` mock responses to support multilingual translation, 14 intelligence categories, and workflow builders.
2. Update the frontend `components.tsx` to handle workflow chains, explainability logs, and dispatch requests to the commands API.
3. Update frontend `page.tsx` with language selection and workflow steppers.
4. Write integration tests under `tests/backend/`.
5. Run lint, build, and test verification suite.
