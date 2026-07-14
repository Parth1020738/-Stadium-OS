# AI Stadium Copilot - Operations Assistant

The AI Stadium Copilot is a centralized, natural-language gateway designed for stadium operators to check live stadium telemetry, ask context-aware questions, and execute quick operational actions.

## Location
- Route: `/copilot`
- Page File: `frontend/src/app/copilot/page.tsx`
- Reusable Components: `frontend/src/app/copilot/components.tsx`

## Core Interface Sections
1. **AI Conversation Panel**: Displays chat bubbles for queries and streams replies token-by-token.
2. **Explainability Panel**: Breaks down the active response's Reasoning steps, potential risks, and alternative actions.
3. **Data Sources Panel**: Highlights exact telemetry APIs and databases scanned (e.g. CCTV feeds, transit schedules).
4. **Suggested Cards**: One-click prompt cards for quick operations scanning.
5. **Dynamic Action Buttons**: Integrated buttons to directly authorize commands like "Open Gate D" or "Delay Shuttle" based on recommendations.
