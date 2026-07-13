# Aegis Smart Stadium OS: Phase 10 - Sequence Diagrams

This document contains Mermaid sequence diagrams detailing the operational execution flow for all major event workflows.

---

## 1. Medical Incident Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Spectator as Fan App / Bystander
    participant CG as Command Gateway
    participant IM as Incident Service
    participant AI as AI Orchestrator
    participant VM as Volunteer Service
    participant OP as Operator Dashboard
    actor Medic as Steward / Mobile Client

    Spectator->>CG: Submit Distress Call (Block 104, Row E, Seat 12)
    CG->>IM: Create Incident (Status: Triage)
    IM-->>AI: Trigger RAG SOP Search & Medic Allocation
    AI-->>VM: Request nearest qualified Medic
    VM-->>AI: Return Medic 14 (Proximity: 30m, Skill: EMT)
    AI-->>IM: Attach SOP "Cardiac/Trauma" & Proposed Dispatch (Medic 14)
    IM-->>OP: Display Incident Dispatch Recommendation
    Note over OP: Operator Reviews & Approves Recommendation
    OP->>CG: Approve Dispatch Command
    CG->>VM: Assign Medic 14
    VM->>Medic: Push Notification (Haptic Route Guidance)
    Medic->>VM: Accept Dispatch
    Medic->>IM: Update Status "Arrived on Scene"
    Medic->>IM: Complete Treatment & Close Incident
    IM-->>OP: Update Dashboard (Resolved Status)
```

---

## 2. Transit Delay & Egress Pacing Workflow

```mermaid
sequenceDiagram
    autonumber
    participant TM as Transit Service
    participant AG as Event Aggregator
    participant AI as AI Orchestrator
    participant OP as Operator Dashboard
    participant CG as Command Gateway
    participant EG as Egress Gates (IoT)

    TM->>AG: Broadcast Transit Delay (Metro Line 1: 20-min delay)
    AG-->>AI: Send Delay Data
    AI-->>AI: Calculate Turnstile Pacing limits (Max 80 exits/min)
    AI-->>OP: Alert: "Metro Delay - Platform Overflow Risk. Slow Gates?"
    OP->>CG: Execute Gate Rate Limit Command (80 exits/min)
    CG->>EG: Throttle turnstile speed parameters
    EG-->>CG: Acknowledge execution
    CG-->>OP: Update Gate status indicators
```

---

## 3. Accessibility Blockage Workflow

```mermaid
sequenceDiagram
    autonumber
    participant BMS as Elevator Sensor (BMS)
    participant AM as Accessibility Service
    participant CG as Command Gateway
    participant NT as Notification Service
    actor MobUser as ADA Fan Mobile Client

    BMS->>AM: Report Fault (Elevator 3 Offline)
    AM->>AM: Identify affected ADA Routes
    AM->>CG: Trigger Path Recalculation
    CG->>NT: Retrieve registered wheelchair users in Zone 3
    NT->>MobUser: Push Audio Guidance: "Elevator 3 offline. Please reroute to Elevator 4"
    AM-->>AM: Mark Elevator 3 Blocked in spatial twins
```

---

## 4. Security Threat Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Steward as Steward Radio / App
    participant CG as Command Gateway
    participant IM as Incident Service
    participant AI as AI Orchestrator
    participant OP as Operator Dashboard
    participant NT as Notification Service

    Steward->>CG: Report Verbal Dispute / Intrusive Fan (Block 204)
    CG->>IM: Log Security Alert (Level 2)
    IM-->>AI: Analyze context & request support SOP
    AI-->>OP: Suggest: "Deploy Stewards 3 & 7, Alert police standby"
    OP->>CG: Approve Police Standby & Dispatch
    CG->>NT: Broadcast alert to security teams
```

---

## 5. Stadium Evacuation Workflow

```mermaid
sequenceDiagram
    autonumber
    participant Fire as Fire Panel Alarm
    participant IM as Incident Service
    participant OP as Operator Dashboard
    participant CG as Command Gateway
    participant NT as Notification Service
    participant Signage as Digital Signage (IoT)
    participant Gates as Turnstiles / Exit Gates

    Fire->>IM: Broadcast Fire Signal (Level 3 - Gate F Corridor)
    IM-->>OP: Emergency Event: Flashing Evacuation Required
    Note over OP: Operator confirms evacuation authorization
    OP->>CG: Authorize Full Evacuation Command
    CG->>Gates: Force Override: Unlocked Open (Free Flow)
    CG->>Signage: Override screens to "Evacuate via North Gate"
    CG->>NT: Broadcast emergency push to all Fan & Staff apps
```
