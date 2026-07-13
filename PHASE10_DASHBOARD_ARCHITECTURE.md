# Aegis Smart Stadium OS: Phase 10 - Operations Dashboard & Gateway Architecture

This document describes the design of the main Operations Command Center (OCC) Dashboard, the Redis caching strategy, and the WebSocket server infrastructure.

---

## 1. Dashboard Widget Directory

The UI dashboard is divided into specialized widgets designed to provide immediate situational awareness.

| Widget | Data Source | Refresh Strategy | Update Mechanism | Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **Executive Summary** | Aggregated Read Model | Polling (1 min) | HTTP REST | Redis Summary Cache |
| **Live Crowd Map** | Crowd Intelligence | Real-time Stream | WebSocket Broadcast | Edge CCTV / YOLO11 |
| **Active Incidents** | Incident Management | Real-time Stream | WebSocket Room Push | PostgreSQL / Kafka |
| **Volunteer Status** | Volunteer Management | On-Demand / 10s | WebSocket Push | Volunteer App GPS |
| **Transit Status** | Transit Management | 15s | REST / HTTP | Municipal Transit APIs |
| **Accessibility Status** | Accessibility Mgmt | Real-time Stream | WebSocket Push | Elevator Sensors (BMS) |
| **AI Recommendations** | AI Orchestrator | Trigger-based | WebSocket Room Push | Knowledge RAG / Vector DB |
| **Operational Timeline** | Audit Log Service | Real-time Stream | WebSocket Room Push | PostgreSQL |
| **Alerts & Warnings** | Emergency Agent | Real-time Stream | WebSocket Broadcast | Fire Panel / Sensors |
| **Capacity Metrics** | Crowd Intelligence | Real-time Stream | WebSocket Push | Smart Turnstiles |
| **Risk Level (Venue)** | AI Orchestrator | Polling (30s) | HTTP REST | Historical Analytics |
| **Health Monitoring** | Infrastructure Agent | Polling (5s) | HTTP REST | Consul / Kubernetes API |
| **Kafka Status** | Infrastructure Agent | Polling (10s) | HTTP REST | Prometheus Exporter |
| **Database Status** | Infrastructure Agent | Polling (10s) | HTTP REST | Pgpool / PgBouncer metrics |

---

## 2. Redis Caching & Memory Architecture

Redis is deployed as a high-performance memory store to offload read strain from the main PostgreSQL databases:

```
[UI Dashboard / Client]
       │
       ▼ (REST / WebSockets)
[API / WebSocket Gateway]
       │
       ├───────(Check Cache)───────► [Redis Cluster]
       │                                  │
       │                              (Cache Hit: Return Data)
       │                                  │
       ├───────(Cache Miss)──────┐◄───────┘
       ▼                         ▼
[Microservice Engine] ───► [PostgreSQL Read Replica]
```

### 2.1 Caching Tiers
- **Session Store**: User sessions (JWT blocklist and tokens) cached with a 1-hour TTL.
- **Dashboard Cache**: Pre-built JSON states of slow widgets (e.g., Executive Summary, Transit Schedules) with a 5-second TTL.
- **Read Cache**: Common entity configurations (e.g., Stadium Gate list, shuttle routes) cached with a 1-hour TTL.

### 2.2 Distributed Locks & Rate Limiting
- **Distributed Locks**: Implemented via Redlock to prevent double-scheduling of volunteers or double-dispatching of transit shuttles.
- **Rate Limiting**: Sliding-window rate limiting on all API routes using Redis Sorted Sets. Limit: `100 requests / minute` per operator device.

---

## 3. WebSocket Architecture & Gateway

The WebSocket Gateway maintains long-lived TCP connections with active operator clients to push real-time events.

### 3.1 Connection Lifecycle
```
Client ──► Connects (WS://) ──► Gateway (JWT Auth validation)
  │                                  │
  │◄───── Connection Approved ───────┤
  │                                  │
  ├────── Subscribe (Room: Gate C) ──► (Validates Permissions)
  │                                  │
  ├◄───── Heartbeat (PING) ──────────┤
  ├────── Heartbeat Response (PONG) ─► (Resets Idle Timeout)
```

### 3.2 Scaling & Reconnect Strategy
- **Horizontal Scaling**: WebSockets are scaled horizontally behind a Layer 4 Load Balancer (HAProxy). Inter-node communication uses a Redis Pub/Sub adapter to sync broadcasts across multiple instances.
- **Reconnect Loop**: In case of disconnects, clients execute exponential backoff reconnect attempts (`1s`, `2s`, `4s`, `8s`, up to `30s max`) with jitter to avoid "thundering herd" issues.
- **Heartbeat (Keep-Alive)**: PING/PONG messages are exchanged every 15 seconds. If a client fails to reply within 30 seconds, the connection is closed and resources are reclaimed.
