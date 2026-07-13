# Frontend Architecture Design Document

This document describes the high-level architecture, runtime execution model, and component layout for the Aegis Smart Stadium OS Operations Command Center.

---

## 1. Technical Architecture Summary

The frontend application uses a **Next.js App Router** framework layered with modular state containers and query caches to support real-time Operations Center requirements.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              NEXT.JS CLIENT                            │
├───────────────────┬───────────────────┬────────────────────────────────┤
│    UI LAYERS      │   STATE MANAGERS  │        DATA TRANSPORT          │
│                   │                   │                                │
│ ┌───────────────┐ │  ┌─────────────┐  │   ┌────────────────────────┐   │
│ │  App Router   │ │  │   Zustand   │  │   │  Axios HTTP Client     │   │
│ │  Pages/Views  │ │  │  (Telemetry │  │   │  (JWT Interceptors)    │   │
│ └───┬───────┬───┘ │  │  & Auth)    │  │   └───────────▲────────────┘   │
│     │       │     │  └──────▲──────┘  │               │                │
│ ┌───▼───┐ ┌─▼───┐ │         │         │   ┌───────────┴────────────┐   │
│ │Shadcn │ │Map  │ │  ┌──────┴──────┐  │   │  WebSockets Pub-Sub    │   │
│ │  UI   │ │GL/  │ │  │TanStack Query│  │   │  (Native WebSocket)    │   │
│ │       │ │D3   │ │  │(Server Sync)│  │   └────────────────────────┘   │
│ └───────┘ └─────┘ │  └─────────────┘  │                                │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

---

## 2. Key Technology Selections

*   **Next.js (App Router)**: Serves as the page routing and page layout system. Leveraging React Server Components (RSC) where possible for page containers, but relying heavily on `"use client"` for dynamic, real-time widgets in the Operations Center Dashboard.
*   **Tailwind CSS + Shadcn UI**: Tailwind CSS is used for flexible styling with a dark-mode-first aesthetic (NASA mission control theme). Shadcn UI supplies high-quality, accessible interactive primitives (radix-based).
*   **TanStack Query (React Query)**: Orchestrates server cache management, cache invalidation, pagination query key structures, and server mutation states.
*   **Zustand**: Manages client-only ephemeral states such as active dashboard settings, collapsible panels state, user preferences, and real-time WebSocket messaging buffers.
*   **Axios**: Performs HTTP requests with configured request/response interceptors to handle automatic silent token refreshing upon credential expiration.
*   **Native WebSockets**: Interfaces with the FastAPI WebSocket gateways to stream telemetry data for crowd counts, metrics, and alerts in real-time.

---

## 3. Rendering & Hydration Strategy

1.  **Server Layouts**: Page shell headers and structural layout elements are pre-rendered on the server to prevent layout shift and optimize initial loads.
2.  **Client-Side Hydration**: Core dashboard panels are client-side hydrated. Since the dashboard depends entirely on live telemetry databases, placeholders/skeletons are rendered during hydration, followed by TanStack Query pre-fetches and WebSocket connection setups.

---

## 4. Operational Styling & Design Guidelines

The interface mimics mission-critical dashboards:
*   **Color Theme**: Dark mode default (`#0B0F19` background, `#1E293B` card backgrounds, `#38BDF8` primary highlights). High contrast elements to distinguish warning levels (`#EF4444` for High Priority, `#F59E0B` for Medium, `#10B981` for Nominal).
*   **Layout Grid**: Dashboard widgets are arranged in a responsive grid using CSS grid or flexbox to scale across different display screens (HD displays, monitors, wallboards).
