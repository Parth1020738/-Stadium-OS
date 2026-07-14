# Phase 12D - Predictive AI, FIFA Match Intelligence & Autonomous Stadium Planning Implementation Plan

## 1. Current Architecture
- **Backend Infrastructure**: Python FastAPI endpoints connecting to `AIOrchestrator`, `GeminiService` and database query schemas.
- **Frontend Workspace**: Next.js client with SSE stream support, chat logging, interactive workflow steppers, and multilingual options.
- **Command Center Integration**: Allows Action Cards to submit executed commands to `POST /api/v1/commands`.

## 2. Prediction Architecture & Pipeline
- **Context Builder Enhancements**: Automatic collection of active queues, turnstile logs, shift statuses, schedule tables, and weather APIs, compiling into a cohesive context payload.
- **Predictive Mock Engine**: In mock mode (`ENABLE_MOCK_AI=true`), the AI detects keyword queries relating to "predict", "forecast", "simulate", "briefing", or "sustainability" and outputs structured prediction fields:
  - Estimated Density, Risk Scores, Queue Timelines, and Recovery Forecasts.
  - Multilingual Public Announcement templates.
  - Lighting, HVAC, and Energy consumption reductions (Sustainability).

## 3. Proposed Changes

### Backend Changes
- **[gemini_service.py](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/backend/app/ai/gemini_service.py)**:
  - Add prediction scenario handlers in `_get_mock_response` matching "simulate", "predict", "briefing", and "sustainability".
  - Return detailed prediction telemetry and environmental savings estimations.
  - Return multilingual announcement copy in English, Spanish, French, Portuguese, and Arabic.

### Frontend Changes
- **[page.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/app/copilot/page.tsx)**:
  - Implement a collapsible **Scenario Simulation Engine Panel** in the sidebar containing quick buttons (e.g. "Simulate Kickoff", "Simulate Crowd Surge", "Simulate Power Outage") to trigger simulation flows.
  - Implement a **Sustainability & Operations Dashboard Panel** rendering lighting optimization recommendations, energy savings, and live risk gauges.
  - Build an **AI Public Announcement Generator Control** that copies multilingual templates to the clipboard with one click.
- **[components.tsx](file:///c:/Users/Asus/OneDrive/Desktop/hackthon%20challnge%204/frontend/src/app/copilot/components.tsx)**:
  - Build custom timeline rendering indicators for scenario forecasts.

## 4. Testing & Verification Strategy
- **Backend Tests**: Create `tests/backend/test_genai_predictions.py` verifying simulation engines, public announcements, and sustainability forecasts.
- **Sequential Regression Suite**: Execute `python tests/backend/run_tests.py` to confirm zero regressions.
- **Frontend Compile Checks**: Run linter and Next.js builds.

## 5. Execution Order
1. Extend `gemini_service.py` to support prediction/simulation keywords, sustainability savings, and announcement generators.
2. Update the frontend `page.tsx` and `components.tsx` with simulation, announcement copy controls, and sustainability panels.
3. Create backend tests in `tests/backend/test_genai_predictions.py`.
4. Run verification checklist (lint, build, tests).
