# UI Component Guide

This guide defines the aesthetic guidelines, component design primitives, and layout systems for the Aegis Command Center.

---

## 1. Visual Aesthetics & Design System

The layout is inspired by emergency operation rooms:
*   **Palette**: Dark-dominant.
    *   *Background*: Deep Blue-Gray (`#090D16` / `slate-950`)
    *   *Surfaces/Cards*: Midnight Blue (`#111827` / `slate-900`)
    *   *Borders*: Cool Gray (`#1F2937` / `slate-800`)
    *   *Text Primary*: Ice White (`#F9FAFB` / `slate-50`)
    *   *Text Secondary*: Silver Gray (`#9CA3AF` / `slate-400`)
*   **Accents & Semantics**:
    *   *Primary*: Cyan / Sky Blue (`#0EA5E9` / `sky-500`)
    *   *Critical Incident*: Fire Red (`#EF4444` / `red-500`)
    *   *Warning/Pending*: Amber Yellow (`#F59E0B` / `amber-500`)
    *   *Nominal/Active*: Emerald Green (`#10B981` / `emerald-500`)

---

## 2. Shared Component Primitives

All components are standard React components configured via Shadcn UI primitives:

### Button
*   Custom variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`.
*   Supports loading spinners and key shortcuts.

### Card
*   Used for telemetry widgets. Contains a header, title, description, body, and action footer.
*   Uses a subtle border glow in dark mode when active or triggered by alerts.

### StatusIndicator
*   A custom component displaying a pulse animation indicating state changes:
    *   `Green Pulse`: Connected / Nominal.
    *   `Yellow Pulse`: Connecting / Degraded.
    *   `Red Pulse`: Offline / Alert.

---

## 3. Feedback & Layout Shells

### Shell Navigation
A dual-tier structure:
1.  **Left Sidebar (Collapsible)**: Holds primary navigation links with icon representations (Lucide Icons) and role badge markers.
2.  **Top Navigation Bar**: Hosts global search, system alerts dropdown, user profile dropdown, and a live WebSocket connection widget.

### Loading Skeletons
Use custom CSS tailwind animation `animate-pulse` configured in Shadcn UI.
*   **CardSkeleton**: Grid-based placeholder blocks mimicking metrics dashboard widgets.
*   **TableSkeleton**: Placeholder rows mimicking lists of incidents, shifts, or shuttle routes.
