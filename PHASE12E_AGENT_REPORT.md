# Phase 12E: Coordinated Agent Performance and Specifications

This document outlines the prompt parameters, confidence scores, and mock behaviors of the Aegis specialized AI agents.

## 1. Domain Prompts and Scopes

| Agent Name | Prompt Scope / File | Key Outputs | Confidence Index |
|---|---|---|---|
| **Crowd Agent** | `crowd.md` | Egress bypass rates, turnstile throughput | 94% - 96% |
| **Incident Agent** | `incident.md` | Hazard resolution timelines, repair schedules | 96% - 98% |
| **Transit Agent** | `transit.md` | Shuttle headways, metro loop allocations | 91% - 95% |
| **Volunteer Agent** | `volunteer.md` | Steward shift compliance, shortages | 89% - 97% |
| **Accessibility Agent** | `accessibility.md` | Lift faults redirects, wheelchair routes | 98% - 99% |
| **Sustainability Agent** | `executive.md` | Halftime energy setbacks, suite HVAC targets | 92% - 94% |
| **Security Agent** | `command_center.md` | Perimeter checks, gate lock states | 95% - 97% |
| **Medical Agent** | `incident.md` | First aid center ETA, paramedics standbys | 94% - 96% |
| **Weather Agent** | `system.md` | Precipitation alerts, slip warnings | 90% - 98% |
| **Command Agent** | `command_center.md` | Command approvals preparation | 95% - 97% |

## 2. Structured Outputs
Each agent returns a structured JSON payload:
- **`summary`**: Domain-specific summary.
- **`reasoning`**: Detailed reasoning explanation.
- **`confidence`**: Float value from 0 to 1.
- **`recommended_actions`**: Operational directives.
- **`potential_risks`**: Safety/operational risks.
- **`resource_allocations`**: Optimization values.
