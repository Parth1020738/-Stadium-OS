# Aegis Command Center Operations Modules Guide

This directory holds the complete operational modules of the Aegis Smart Stadium OS Command Center frontend.

---

## 1. Modules List

*   **Crowd Operations (`/crowd`)**: Live stand occupancy tables, alert density thresholds, and flow rate cards.
*   **Incident Workspace (`/incidents`)**: Tickets management workspace, comment log timelines, and dispatcher forms.
*   **Volunteer Operations (`/volunteers`)**: Steward directory, skill competencies, and shift assignments.
*   **Transit Operations (`/transit`)**: Shuttle tracking grids, routes details, and turnstile egress pacing limits.
*   **Accessibility Dashboard (`/accessibility`)**: Obstacle alerts, path status checking, elevator outage trackers.

---

## 2. Shared Ingestion Architecture

Every page couples dynamic REST fetching (using **React Query** for caching and caching invalidation) with real-time **WebSocket updates** (consuming Zustand streams to update counts, coordinates, and health variables).
