# AI Copilot Architecture & Data Flow

This document details the operational data flow for the Aegis Stadium Copilot.

## 1. End-To-End Sequence Flow

```
Frontend Copilot Page (/copilot)
       │
       ▼  (useAI React Hook -> startStream)
FastAPI Streaming Endpoint (/api/v1/ai/stream)
       │
       ▼  (AIOrchestrator -> execute_stream)
Context Builder (aggregates SQL telemetry context)
       │
       ▼  (Prompt Manager loading system.md and copilot.md)
Gemini Service (streams content token-by-token)
       │
       ▼  (Streaming Response yields SSE text/event-stream)
Frontend state (accumulates stream chunks into Message sections)
       │
       ▼  (React re-renders components & updates side panels)
Operator views Summary, Reasoning, Confidence, and Action buttons
```

## 2. Explainability Delimiter Parser
To support multi-panel rendering of streaming content, the assistant splits response text using markdown headers:
- `### Summary`
- `### Reasoning`
- `### Confidence`
- `### Data Sources`
- `### Recommended Actions`
- `### Alternative Actions`
- `### Potential Risks`

The client-side parser uses regular expressions to extract these subsections at render time, ensuring immediate populating of cards and sidebar details.
