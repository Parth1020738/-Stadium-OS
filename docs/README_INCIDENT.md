# Incident Management Service

This document provides specifications and deployment guidelines for the Aegis Smart Stadium OS **Incident Management Service**.

## Overview & Objectives

The Incident Management Service coordinates safety-critical events, security dispatches, and medical emergencies on matchdays. It is fully integrated with the event bus (Kafka) and enforces strict transition validations, optimistic concurrency checks, and role-based access controls.

## Environment Variables

Ensure the following variables are configured in your `.env` file:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aegis_db?sslmode=disable
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
JWT_SECRET=super-secure-jwt-secret-key-32-chars-long
```

## REST API Endpoint Catalog

All routes reside under `/api/v1/incidents`.

| Method | Path | Auth Scope | Description |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/incidents` | Steward, Operator, Admin | Create a security or medical incident. |
| **GET** | `/api/v1/incidents` | Steward, Operator, Admin | Search, filter, and paginate incidents. |
| **GET** | `/api/v1/incidents/{id}` | Steward, Operator, Admin | Get details of a single incident. |
| **PUT** | `/api/v1/incidents/{id}` | Steward, Operator, Admin | Update incident details (optimistic locking enforced). |
| **POST** | `/api/v1/incidents/{id}/assign` | Operator, Admin | Assign a steward/responder to the incident. |
| **POST** | `/api/v1/incidents/{id}/escalate` | Steward, Operator, Admin | Escalate incident status to 'Escalated' and priority to 'Critical'. |
| **POST** | `/api/v1/incidents/{id}/resolve` | Operator, Admin | Mark the incident as 'Resolved'. |
| **POST** | `/api/v1/incidents/{id}/close` | Operator, Admin | Mark the incident as 'Closed'. |
| **POST** | `/api/v1/incidents/{id}/reopen` | Operator, Admin | Reopen a resolved/closed incident back to 'Open'. |
| **POST** | `/api/v1/incidents/{id}/comments` | Steward, Operator, Admin | Add operational comments to the timeline. |
| **POST** | `/api/v1/incidents/{id}/evidence` | Steward, Operator, Admin | Upload and link evidence metadata. |
| **POST** | `/api/v1/incidents/{id}/attachments`| Steward, Operator, Admin | Link binary file attachments to the incident. |
| **GET** | `/api/v1/incidents/{id}/timeline` | Steward, Operator, Admin | Retrieve chronological history log of the incident. |
| **GET** | `/api/v1/incidents/statistics` | Steward, Operator, Admin | Retrieve summary stats of active/critical incidents. |

## Kafka Asynchronous Events

The service publishes events to Kafka for downstream ingestion:

- **incident.created**: Published when a new incident is registered.
- **incident.updated**: Published when details of an incident change.
- **incident.assigned**: Published when a responder is assigned.
- **incident.reassigned**: Published when a responder is changed or added.
- **incident.escalated**: Published when an incident is escalated.
- **incident.resolved**: Published when an incident is resolved.
- **incident.closed**: Published when an incident is closed.
- **incident.reopened**: Published when an incident is reopened.
- **incident.comment.created**: Published when a comment is added.
- **incident.evidence.uploaded**: Published when evidence is uploaded.

## Entity Relationship (ER) Summary

- **Incident** (Parent model)
  - One-to-Many with **IncidentTimeline**
  - One-to-Many with **IncidentEvidence**
  - One-to-Many with **IncidentAttachment**
  - One-to-Many with **IncidentComment**
  - One-to-Many with **IncidentAssignment**
  - One-to-Many with **IncidentResolution**
  - One-to-Many with **IncidentEscalation**
  - One-to-Many with **IncidentNotification**
  - One-to-Many with **IncidentAudit**
  - Many-to-Many with **User** (stewards/responders)
