# Session & Idle Inactivity Management

This document outlines session lifecycle control, idle tracking events, warning dialogs, and multi-tab synchronization logic.

---

## 1. Inactivity Tracking

To protect open command center screens, the client tracks operator interactions:
*   **Monitored Events**: `mousemove`, `keydown`, `click`, and `scroll`.
*   **Timeout Threshold**: 15 minutes (`900,000 ms`).
*   **Warning Warning Trigger**: Triggers a modal warning dialog 60 seconds before termination.
*   **Action**: If the user clicks "Keep Session Alive", the timers reset. If the 60-second countdown runs out, the user is logged out.

---

## 2. Multi-Tab Session Synchronization

To keep open tabs synchronized:
*   **Channel**: We use the native browser `BroadcastChannel` with key `aegis_session_sync`.
*   **Action Flow**:
    1.  Tab A times out due to inactivity or the user clicks logout.
    2.  Tab A logs out, clears local variables, and posts a `"logout"` message to the channel.
    3.  Tabs B and C listen to the channel, receive the `"logout"` message, clear their local state, and redirect users to `/session-expired`.

---

## 3. Page Visibility Lifecycle Support

When the tab shifts to the background, active JS intervals might throttle or sleep:
*   We attach a listener to the standard Page Visibility API (`visibilitychange`).
*   Upon shifting back to `visible`, the shell calculates `Date.now() - lastActivity`. If it exceeds the 15-minute timeout threshold, it logs the user out immediately.
