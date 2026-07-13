# Frontend Folder Structure

This document outlines the layout of the `frontend/` directory for the Operations Command Center.

---

## 1. Project Folder Tree

```
frontend/
├── .github/                  # Github actions and workflows
├── public/                   # Static assets (icons, stadium floorplans, SVGs)
├── src/
│   ├── app/                  # Next.js App Router root
│   │   ├── (auth)/           # Authentication layout and routing group
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/      # Protected dashboard layouts and pages
│   │   │   ├── crowd/
│   │   │   ├── incidents/
│   │   │   ├── volunteers/
│   │   │   ├── transit/
│   │   │   ├── accessibility/
│   │   │   ├── ai/
│   │   │   ├── command-center/
│   │   │   └── page.tsx      # Core Live Telemetry Dashboard view
│   │   ├── layout.tsx        # Shell layout, theme providers
│   │   ├── page.tsx          # Initial entry point / routing guard page
│   │   └── global-error.tsx  # Top-level global boundary catch
│   │
│   ├── components/           # Reusable UI component modules
│   │   ├── ui/               # Primitive Shadcn UI wrappers
│   │   ├── common/           # Shared layout containers (sidebar, topbar)
│   │   ├── dashboard/        # Dashboard telemetry card components
│   │   ├── map/              # Interactive stadium mapping modules
│   │   └── commands/         # Two-person verification controls
│   │
│   ├── hooks/                # Custom React Hooks
│   │   ├── useWebSocket.ts   # Subscriptions and ping-pong handlers
│   │   └── useDebounce.ts
│   │
│   ├── lib/                  # Library bindings and third-party setups
│   │   ├── api-client.ts     # Axios global configured instance
│   │   ├── utils.ts          # Classnames merges and formats
│   │   └── websocket.ts      # Core connection and messaging service
│   │
│   ├── store/                # Zustand client stores
│   │   ├── authStore.ts      # Active JWT state and roles
│   │   ├── uiStore.ts        # Sidebar visibility and layout preference
│   │   └── telemetryStore.ts # Telemetry data buffers
│   │
│   ├── schemas/              # Zod validation schemas
│   │   ├── auth.ts           # Login/Registration schema
│   │   └── incident.ts       # Ticket forms
│   │
│   └── styles/
│       └── globals.css       # Tailwind entry and design tokens
│
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── Dockerfile
```
