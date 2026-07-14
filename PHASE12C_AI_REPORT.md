# Phase 12C - GenAI Core Model & Prompt Management Report

## 1. Context Builder & Prompt Architecture
The AI Copilot uses `ContextBuilder` to aggregate active telemetry data:
- Turnstile counts, CCTV occupancy metrics, open incident reports, transit vehicles coordinates, active volunteer counts, and shift logs.
- It substitutes these into prompt templates (e.g. `copilot.md`) before submitting to the Gemini LLM.

## 2. Structured Delimiters
Responses are structured systematically using markdown delimiters:
- `### Summary`
- `### Reasoning`
- `### Confidence`
- `### Data Sources`
- `### Recommended Actions`
- `### Alternative Actions`
- `### Potential Risks`
- `### Workflow`

This enables client-side regex parsing for multi-pane layouts.
