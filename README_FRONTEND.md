# Aegis Operations Command Center Frontend

This is the official Next.js App Router frontend for the Aegis Smart Stadium OS Command Center.

---

## 1. Directory Structure

*   `src/app/`: Next.js static and dynamic page routing directories.
    *   `(auth)/`: Login, registration, password recoveries.
    *   `accessibility/`, `crowd/`, `incidents/`, `transit/`, `volunteers/`: Operations dashboard modules.
    *   `ai/`: AI recommendations, risk speedometers, and explainability.
    *   `command-center/`: Two-person authorization overrides queue.
*   `src/components/`: Reusable primitives, sidebar layout shells, and interactive maps.
*   `src/store/`: Zustand global client state containers (`authStore`, `telemetryStore`, `uiStore`).
*   `src/lib/`: Axios interceptor clients.

---

## 2. Getting Started

### Install Dependencies
```bash
npm install
```

### Dev Server Running
```bash
npm run dev
```

### Run Tests
```bash
npm run test
```

### Compile Production Build
```bash
npm run build
```
