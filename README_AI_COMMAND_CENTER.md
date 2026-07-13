# Aegis AI & Command Center Gateway Guide

This directory holds the AI decision recommendation dashboard and operations override command gates.

---

## 1. Workspaces

*   **AI Recommendations (`/ai`)**: Ingests risk estimation gauges (Crowd, Transit, Incidents ratios) and lists recommendations confidence metrics.
*   **Command Center Override Queue (`/command-center`)**: Displays pending operator command lines, approval buttons, cancellation overrides, and execution status logs.

---

## 2. Security Roles & Approvals

Command approvals use the **Two-Person Authentication Protocol**. Any Operator can *submit/queue* overrides, but only users with `approve_checker` clearance (e.g. `OperationsManager`, `Administrator`) can *approve/reject* execution.
