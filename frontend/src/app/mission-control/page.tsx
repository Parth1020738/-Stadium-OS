"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { apiClient } from "@/lib/api-client";
import {
  Brain,
  Shield,
  Activity,
  AlertTriangle,
  Bus,
  Users,
  Accessibility,
  CloudRain,
  Zap,
  Terminal,
  Clock,
  ArrowRight,
  CheckCircle,
  XCircle,
  Play,
  RotateCcw,
  Languages,
  ActivityIcon,
  HelpCircle,
  Check,
  TrendingUp,
  Flame,
  Globe,
  Settings,
  Sparkles,
  Info
} from "lucide-react";

interface AgentResult {
  name: string;
  summary: string;
  reasoning: string;
  confidence: number;
  recommended_actions: string[];
  alternative_actions?: string[];
  potential_risks?: string[];
  expected_impact?: string;
}

interface ConflictDetail {
  agent_a: string;
  recommendation_a: string;
  agent_b: string;
  recommendation_b: string;
  resolution: string;
}

interface TimelineItem {
  time: string;
  action: string;
  agent: string;
  status: "completed" | "pending" | "alert";
}

interface PlanResult {
  query: string;
  agents: Record<string, AgentResult>;
  collaboration_logs: string[];
  conflicts: ConflictDetail[];
  timeline: TimelineItem[];
  resource_optimizations: Record<string, string>;
  confidence: number;
  latency_ms: number;
}

interface MatchdayModeConfig {
  ai_priority?: string;
  expected_flow?: string;
}

// Scenarios configuration with matching telemetry & AI briefs
const MATCH_SCENARIOS = {
  "Pre-Match": {
    matchStatus: "Gates Open (Pre-Match)",
    attendance: 48500,
    crowdHeat: "LOW",
    securityStatus: "SECURE",
    medicalStatus: "STANDBY",
    transitStatus: "NOMINAL",
    volunteerReadiness: 100,
    accessibilityReadiness: 100,
    sustainabilityScore: 92,
    energyConsumption: 380,
    carbonSavings: 18,
    weather: "Clear, 24°C",
    predictedIncidents: "None",
    riskScore: 12.0,
    healthScore: 88,
    objectives: [
      "Process incoming pre-match guest ticketing validation.",
      "Monitor shuttle fleet headway times (target: 6 mins).",
      "Verify elevator diagnostic states near Gate C."
    ],
    brief: "Good Day. Gates are open and attendance has reached 60%. Transit shuttle headway remains stable at 6 minutes. Accessibility lanes are clear, and sustainability solar generation is satisfying 22% of stadium base load. Confidence: 98%.",
    timeline: [
      { time: "16:00", action: "Gates opened successfully", agent: "Crowd Agent", status: "completed" },
      { time: "16:15", action: "Shuttle fleet headway sync", agent: "Transit Agent", status: "completed" },
      { time: "16:30", action: "Ticketing checks nominal", agent: "Security Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Maintain regular ticketing gate scans",
        why: "To ensure stable flow rates before peak pre-match arrivals window.",
        evidence: "RFID validators reporting average scan latency of 38ms.",
        confidence: 0.98,
        alternatives: "Open secondary gate bypass lines.",
        risks: "None.",
        expectedImprovement: "Zero queue spikes.",
        depts: ["Security", "Crowd"],
        time: "Just now",
        requiresApproval: false
      }
    ],
    buses: [
      { id: 1, x: 80, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 220, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 120, y: 80, status: "active" },
      { id: 2, name: "V2", x: 380, y: 150, status: "active" }
    ],
    crowdPoints: [
      { x: 100, y: 90, density: 0.2 },
      { x: 390, y: 160, density: 0.3 }
    ],
    gateState: "open"
  },
  "Kickoff": {
    matchStatus: "Match Kickoff (1st Half)",
    attendance: 64200,
    crowdHeat: "MEDIUM",
    securityStatus: "SECURE",
    medicalStatus: "ACTIVE",
    transitStatus: "NOMINAL",
    volunteerReadiness: 98,
    accessibilityReadiness: 99,
    sustainabilityScore: 89,
    energyConsumption: 420,
    carbonSavings: 15,
    weather: "Clear, 23°C",
    predictedIncidents: "Minor entry congestion",
    riskScore: 24.0,
    healthScore: 76,
    objectives: [
      "Stagger late ingress arrivals.",
      "Track outer concourse pedestrian flow density.",
      "Standby emergency dispatch coordination."
    ],
    brief: "Good Day. Kickoff is active. Attendance is at 80% capacity. Low-priority queues are clearing at East Gate. Volunteer coverage is optimal across all stands. Energy consumption matches expected matchday lighting setback guidelines. Confidence: 95%.",
    timeline: [
      { time: "16:45", action: "Late arrivals wave processed", agent: "Crowd Agent", status: "completed" },
      { time: "17:00", action: "Match kickoff confirmed", agent: "System Agent", status: "completed" },
      { time: "17:05", action: "Concourse density verification", agent: "Security Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Stagger transit departures",
        why: "To balance post-kickoff concourse security patrol rates.",
        evidence: "Arrival telemetry has reached 140 entries/min.",
        confidence: 0.94,
        alternatives: "Manual routing override.",
        risks: "Minor passenger wait times at stations.",
        expectedImprovement: "15% lower queue buildup.",
        depts: ["Transit", "Security"],
        time: "1 min ago",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 110, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 260, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 140, y: 80, status: "active" },
      { id: 2, name: "V2", x: 350, y: 150, status: "active" }
    ],
    crowdPoints: [
      { x: 140, y: 90, density: 0.4 },
      { x: 350, y: 160, density: 0.5 }
    ],
    gateState: "open"
  },
  "Goal": {
    matchStatus: "GOAL! (1-0)",
    attendance: 64500,
    crowdHeat: "HIGH",
    securityStatus: "SECURE",
    medicalStatus: "ACTIVE",
    transitStatus: "NOMINAL",
    volunteerReadiness: 96,
    accessibilityReadiness: 99,
    sustainabilityScore: 85,
    energyConsumption: 440,
    carbonSavings: 14,
    weather: "Clear, 23°C",
    predictedIncidents: "None",
    riskScore: 28.0,
    healthScore: 72,
    objectives: [
      "Monitor structural stand vibration indicators.",
      "Track volunteer deployments at South stand.",
      "Check exit path ADA ramp clearances."
    ],
    brief: "Goal scored! Stadium cheering has created a temporary stand vibration spike, which is within safe tolerances. Concourse exit gates are clear. All stewards are at high-vigilance positions. Confidence: 96%.",
    timeline: [
      { time: "17:15", action: "Goal scored by home team", agent: "System Agent", status: "completed" },
      { time: "17:16", action: "Stand structural vibration analyzed", agent: "Crowd Agent", status: "completed" },
      { time: "17:18", action: "Corridor patrol check clear", agent: "Security Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Maintain stand vibration monitoring",
        why: "To verify structural integrity during peak celebration waves.",
        evidence: "Telemetry registered 1.2G vibration peak, safely below 2.5G threshold.",
        confidence: 0.97,
        alternatives: "Reroute exit paths.",
        risks: "None.",
        expectedImprovement: "Zero hazard reports.",
        depts: ["Crowd", "Security"],
        time: "Just now",
        requiresApproval: false
      }
    ],
    buses: [
      { id: 1, x: 130, y: 180, status: "stopped", label: "Shuttle A" },
      { id: 2, x: 290, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 160, y: 90, status: "active" },
      { id: 2, name: "V2", x: 320, y: 150, status: "active" }
    ],
    crowdPoints: [
      { x: 160, y: 110, density: 0.7 },
      { x: 320, y: 160, density: 0.6 }
    ],
    gateState: "open"
  },
  "Halftime": {
    matchStatus: "Halftime Interval",
    attendance: 64500,
    crowdHeat: "VERY HIGH",
    securityStatus: "SECURE",
    medicalStatus: "STANDBY",
    transitStatus: "NOMINAL",
    volunteerReadiness: 100,
    accessibilityReadiness: 100,
    sustainabilityScore: 95,
    energyConsumption: 320,
    carbonSavings: 25,
    weather: "Clear, 22°C",
    predictedIncidents: "Concourse concession lineups",
    riskScore: 20.0,
    healthScore: 80,
    objectives: [
      "Manage concourse pedestrian flows.",
      "Implement main field lighting setback (15% drop).",
      "Stagger suite HVAC setbacks to 23C."
    ],
    brief: "Halftime in progress. Crowds are migrating to concourses and restroom zones. Energy saving setbacks activated: HVAC suite temperature set to 23C, base lighting output reduced by 15% to save 184 kWh grid loads. Confidence: 94%.",
    timeline: [
      { time: "17:45", action: "First half ends", agent: "System Agent", status: "completed" },
      { time: "17:46", action: "Halftime energy setback activated", agent: "Sustainability Agent", status: "completed" },
      { time: "17:48", action: "Concourse crowd flow guided", agent: "Volunteer Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Deploy concourse waste collectors",
        why: "To maintain hygiene and optimize waste diversion during halftime migration.",
        evidence: "Concession stands garbage load spikes detected on weight bins.",
        confidence: 0.91,
        alternatives: "Postpone cleaning until full-time.",
        risks: "Minor passenger flow slowdown near bin points.",
        expectedImprovement: "30% reduction in corridor littering.",
        depts: ["Volunteer", "Sustainability"],
        time: "2 mins ago",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 150, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 310, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 200, y: 100, status: "active" },
      { id: 2, name: "V2", x: 280, y: 140, status: "active" }
    ],
    crowdPoints: [
      { x: 200, y: 120, density: 0.8 },
      { x: 280, y: 150, density: 0.8 }
    ],
    gateState: "open"
  },
  "Crowd Surge": {
    matchStatus: "Egress In-Progress",
    attendance: 63800,
    crowdHeat: "CRITICAL",
    securityStatus: "WARNING",
    medicalStatus: "ACTIVE",
    transitStatus: "DELAYED",
    volunteerReadiness: 94,
    accessibilityReadiness: 95,
    sustainabilityScore: 82,
    energyConsumption: 460,
    carbonSavings: 12,
    weather: "Clear, 22°C",
    predictedIncidents: "Gate D turnstile bottleneck",
    riskScore: 68.0,
    healthScore: 42,
    objectives: [
      "Relieve Gate D turnstile scanning congestion.",
      "Deploy secondary volunteer stewards to South Stand.",
      "Manage Metro Shuttle outer ring delays."
    ],
    brief: "WARNING: Gate D turnstiles are experiencing a 42% bottleneck, increasing local queue wait times to 15 minutes. Ingress rate (68/min) exceeds validation scanner rate (48/min). AI recommends executing secondary gate override. Confidence: 94%.",
    timeline: [
      { time: "18:15", action: "Gate D crowd bottleneck detected", agent: "Crowd Agent", status: "alert" },
      { time: "18:16", action: "AI gate rate override generated", agent: "Brain Agent", status: "completed" },
      { time: "18:18", action: "Volunteer team dispatch queued", agent: "Volunteer Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Open Gate D secondary bypass gates",
        why: "To relieve turnstile backlog and reduce crowd density in Zone 2 corridor.",
        evidence: "Crowd density reached 4.2 people/sqm (critical threshold: 3.5).",
        confidence: 0.94,
        alternatives: "Reroute all arrivals to Gate E.",
        risks: "Steward patrols must secure outer perimeter zones.",
        expectedImprovement: "Reduces gate queue length by 25% in 6 minutes.",
        depts: ["Crowd", "Security", "Volunteer"],
        time: "Just now",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 180, y: 180, status: "stopped", label: "Shuttle A" },
      { id: 2, x: 350, y: 220, status: "stopped", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 220, y: 90, status: "active" },
      { id: 2, name: "V2", x: 260, y: 150, status: "active" }
    ],
    crowdPoints: [
      { x: 220, y: 100, density: 0.95 },
      { x: 260, y: 140, density: 0.9 }
    ],
    gateState: "congested"
  },
  "Medical Emergency": {
    matchStatus: "Active Incident",
    attendance: 64100,
    crowdHeat: "MEDIUM",
    securityStatus: "SECURE",
    medicalStatus: "CRITICAL",
    transitStatus: "NOMINAL",
    volunteerReadiness: 97,
    accessibilityReadiness: 98,
    sustainabilityScore: 88,
    energyConsumption: 410,
    carbonSavings: 16,
    weather: "Overcast, 21°C",
    predictedIncidents: "Sector B visitor dizziness",
    riskScore: 45.0,
    healthScore: 58,
    objectives: [
      "Dispatch First Aid Squad 4 to Sector B.",
      "Clear medical response priority lanes.",
      "Provide cold water and ice pack escorts."
    ],
    brief: "ALERT: Minor medical issue reported at Sector B (visitor suffering heat exhaustion). Telemetry indicates paramedic ETA is 180 seconds. AI recommends clearing wheelchair bypass corridor to allow medic access. Confidence: 94%.",
    timeline: [
      { time: "18:30", action: "Steward logs heat dizziness at Row 14", agent: "Volunteer Agent", status: "alert" },
      { time: "18:32", action: "First Aid Squad 4 dispatched", agent: "Medical Agent", status: "completed" },
      { time: "18:34", action: "ADA pathway clearance verified", agent: "Accessibility Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Dispatch First Aid Squad 4 to Sector B",
        why: "To stabilize dizziness case and escort visitor to cooling room.",
        evidence: "Steward radio dispatch logged heat exhaustion symptoms.",
        confidence: 0.94,
        alternatives: "Use general security guards for basic first aid.",
        risks: "Corridor crowd congestion could delay paramedic carts.",
        expectedImprovement: "Ensures medical care within 3-minute SLA.",
        depts: ["Medical", "Volunteer"],
        time: "Just now",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 200, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 380, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 240, y: 80, status: "active" },
      { id: 2, name: "V2", x: 230, y: 160, status: "active" }
    ],
    crowdPoints: [
      { x: 240, y: 80, density: 0.5 },
      { x: 230, y: 160, density: 0.5 }
    ],
    gateState: "open"
  },
  "Power Failure": {
    matchStatus: "Partial Outage",
    attendance: 64200,
    crowdHeat: "HIGH",
    securityStatus: "CRITICAL",
    medicalStatus: "ACTIVE",
    transitStatus: "NOMINAL",
    volunteerReadiness: 90,
    accessibilityReadiness: 80,
    sustainabilityScore: 60,
    energyConsumption: 120,
    carbonSavings: 60,
    weather: "Dark, 20°C",
    predictedIncidents: "North Stand grid backup failure",
    riskScore: 78.0,
    healthScore: 32,
    objectives: [
      "Engage auxiliary diesel generator backups.",
      "Dispatch security patrols to North Concourse corridors.",
      "Check elevator backup battery statuses."
    ],
    brief: "CRITICAL ALERT: Partial power outage detected in North Stand sector. Auxiliary generators are online. Elevator 2 near Gate C door lock system failed; tech team has been notified. Deploying stewards for manual guidance. Confidence: 98%.",
    timeline: [
      { time: "18:45", action: "North Stand power drop registered", agent: "System Agent", status: "alert" },
      { time: "18:46", action: "Auxiliary generators engaged", agent: "Sustainability Agent", status: "completed" },
      { time: "18:48", action: "Elevator 2 door lock fault flagged", agent: "Accessibility Agent", status: "alert" }
    ],
    recommendations: [
      {
        title: "Redirect wheelchair guests to Elevator 1",
        why: "To maintain ADA compliance and vertical egress pathways during Elevator 2 failure.",
        evidence: "Elevator telemetry logged fault code E-204 at 18:46.",
        confidence: 0.98,
        alternatives: "Use ADA Ramp B with steward push assistance.",
        risks: "Ramp B bottleneck if wheelchair count exceeds 15.",
        expectedImprovement: "Continuous vertical mobility achieved.",
        depts: ["Accessibility", "Volunteer"],
        time: "1 min ago",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 220, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 410, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 260, y: 80, status: "alert" },
      { id: 2, name: "V2", x: 210, y: 160, status: "alert" }
    ],
    crowdPoints: [
      { x: 260, y: 80, density: 0.75 },
      { x: 210, y: 160, density: 0.6 }
    ],
    gateState: "open"
  },
  "Heavy Rain": {
    matchStatus: "Weather Delay Alert",
    attendance: 62400,
    crowdHeat: "MEDIUM",
    securityStatus: "SECURE",
    medicalStatus: "ACTIVE",
    transitStatus: "SLOWDOWN",
    volunteerReadiness: 95,
    accessibilityReadiness: 96,
    sustainabilityScore: 86,
    energyConsumption: 450,
    carbonSavings: 10,
    weather: "Heavy Rain, 18°C",
    predictedIncidents: "Wet ramp slip hazards",
    riskScore: 50.0,
    healthScore: 50,
    objectives: [
      "Deploy canopy extensions over Gate D queue lines.",
      "Post wet flooring warning notices on digital boards.",
      "Coordinate public transit delay notifications."
    ],
    brief: "ALERT: Doppler radar shows precipitation band approaching. Heavy rain has started. AI predicts sudden crowd migration from open stands to covered concourses. Wet flooring hazard warnings active. Confidence: 90%.",
    timeline: [
      { time: "19:00", action: "Precipitation warning received", agent: "Weather Agent", status: "completed" },
      { time: "19:02", action: "Concourse canopy deployed", agent: "Crowd Agent", status: "completed" },
      { time: "19:05", action: "Wet ramp warning signs active", agent: "Volunteer Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Deploy canopy extensions over Gate D",
        why: "To shield waiting visitors and prevent stampede waves into entry gates.",
        evidence: "Rain volume reached 15mm/hour; visitors congregating at entry bottlenecks.",
        confidence: 0.90,
        alternatives: "Suggest visitors hold in parking structures.",
        risks: "Minor canopy wind-load warnings.",
        expectedImprovement: "Maintains orderly queue line flows.",
        depts: ["Crowd", "Volunteer"],
        time: "Just now",
        requiresApproval: false
      }
    ],
    buses: [
      { id: 1, x: 240, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 440, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 280, y: 80, status: "active" },
      { id: 2, name: "V2", x: 190, y: 160, status: "active" }
    ],
    crowdPoints: [
      { x: 280, y: 80, density: 0.5 },
      { x: 190, y: 160, density: 0.55 }
    ],
    gateState: "open"
  },
  "Security Alert": {
    matchStatus: "Security Threat",
    attendance: 64200,
    crowdHeat: "HIGH",
    securityStatus: "CRITICAL",
    medicalStatus: "ACTIVE",
    transitStatus: "NOMINAL",
    volunteerReadiness: 92,
    accessibilityReadiness: 94,
    sustainabilityScore: 84,
    energyConsumption: 470,
    carbonSavings: 10,
    weather: "Clear, 21°C",
    predictedIncidents: "Intrusion alert Gate 3 corridor",
    riskScore: 72.0,
    healthScore: 35,
    objectives: [
      "Verify CCTV feed intrusion detection at Zone 3.",
      "Deploy security containment teams.",
      "Restrict Zone 3 corridor access."
    ],
    brief: "ALERT: Security intrusion alarm triggered in Zone 3 player tunnel. CCTV feed indicates unauthorized spectator bypass. Paramedics and stewards are redirecting concourse exit crowds to safety corridors. Confidence: 94%.",
    timeline: [
      { time: "19:15", action: "CCTV Sensor 12 intrusion flag", agent: "Security Agent", status: "alert" },
      { time: "19:16", action: "Containment team deployed to corridor", agent: "Security Agent", status: "completed" },
      { time: "19:18", action: "Zone 3 doors locked down", agent: "System Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Lock down Zone 3 corridor access doors",
        why: "To restrict intruder movement and secure player lock-rooms.",
        evidence: "Intrusion telemetry confirmed by security RFID bypass logs.",
        confidence: 0.94,
        alternatives: "Perform manual steward blockades.",
        risks: "Traps exiting visitors inside concourse corridors.",
        expectedImprovement: "Perimeter containment completed in 4 minutes.",
        depts: ["Security"],
        time: "2 mins ago",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 260, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 420, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 300, y: 80, status: "alert" },
      { id: 2, name: "V2", x: 170, y: 160, status: "alert" }
    ],
    crowdPoints: [
      { x: 300, y: 80, density: 0.6 },
      { x: 170, y: 160, density: 0.6 }
    ],
    gateState: "congested"
  },
  "Evacuation": {
    matchStatus: "Stadium Evacuation Mode",
    attendance: 64200,
    crowdHeat: "CRITICAL",
    securityStatus: "CRITICAL",
    medicalStatus: "CRITICAL",
    transitStatus: "NOMINAL",
    volunteerReadiness: 85,
    accessibilityReadiness: 70,
    sustainabilityScore: 50,
    energyConsumption: 520,
    carbonSavings: 5,
    weather: "Clear, 21°C",
    predictedIncidents: "Total stadium clearance hazards",
    riskScore: 92.0,
    healthScore: 8,
    objectives: [
      "Unlock all perimeter gates immediately.",
      "Publish evacuation broadcasts in 5 languages.",
      "Maximize shuttle fleet exit capacities."
    ],
    brief: "CRITICAL EVACUATION BROADCAST: Safety override active. Evacuation warning initiated for South Concourse. All exit pathways unlocked. English, Spanish, French, Portuguese, Arabic PA broadcasts dispatched. Confidence: 98%.",
    timeline: [
      { time: "19:30", action: "Evacuation alarm triggered", agent: "System Agent", status: "alert" },
      { time: "19:31", action: "Safety override unlocked all gates", agent: "Security Agent", status: "completed" },
      { time: "19:33", action: "Emergency shuttle dispatch active", agent: "Transit Agent", status: "completed" }
    ],
    recommendations: [
      {
        title: "Initiate emergency evacuation warning",
        why: "To coordinate orderly guest evacuation and prevent crowding stampedes.",
        evidence: "Stadium-wide risk score reached 92% (critical evacuation limit).",
        confidence: 0.98,
        alternatives: "Perform staged stand evacuations.",
        risks: "High passenger panic increases queue density near exits.",
        expectedImprovement: "Ensures complete stadium clearance in under 12 minutes.",
        depts: ["Security", "Transit", "Medical", "Volunteer"],
        time: "Just now",
        requiresApproval: true
      }
    ],
    buses: [
      { id: 1, x: 280, y: 180, status: "moving", label: "Shuttle A" },
      { id: 2, x: 450, y: 220, status: "moving", label: "Shuttle B" }
    ],
    volunteers: [
      { id: 1, name: "V1", x: 320, y: 80, status: "alert" },
      { id: 2, name: "V2", x: 150, y: 160, status: "alert" }
    ],
    crowdPoints: [
      { x: 320, y: 80, density: 0.99 },
      { x: 150, y: 160, density: 0.99 }
    ],
    gateState: "open"
  }
};

export default function MissionControlPage() {
  const [activeScenarioName, setActiveScenarioName] = useState<string>("Pre-Match");
  const [demoRunning, setDemoRunning] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<"SYNCED" | "SYNCING" | "ALERT">("SYNCED");
  const [approvedCommands, setApprovedCommands] = useState<Record<string, boolean>>({});
  const [executedCommands, setExecutedCommands] = useState<string[]>([]);
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);
  
  const demoIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const scenarioNames = useMemo(() => Object.keys(MATCH_SCENARIOS), []);

  const scenarioData = (MATCH_SCENARIOS as Record<string, any>)[activeScenarioName] || MATCH_SCENARIOS["Pre-Match"];

  // Fluctuate telemetry values dynamically to show "live digital twin"
  const [liveTelemetry, setLiveTelemetry] = useState(scenarioData);

  useEffect(() => {
    setLiveTelemetry(scenarioData);
  }, [activeScenarioName, scenarioData]);

  // Telemetry fluctuation effect
  useEffect(() => {
    const timer = setInterval(() => {
      setSyncStatus("SYNCING");
      setLiveTelemetry((prev: any) => {
        const attendanceOffset = Math.floor(Math.random() * 20) - 10;
        const energyOffset = Math.floor(Math.random() * 6) - 3;
        const riskOffset = parseFloat((Math.random() * 2 - 1).toFixed(1));
        const newRisk = Math.min(100, Math.max(5, prev.riskScore + riskOffset));
        
        // Randomly update digital twin vehicle positions
        const nextBuses = prev.buses.map((bus: any) => {
          if (bus.status === "moving") {
            const nextX = bus.x >= 450 ? 50 : bus.x + Math.floor(Math.random() * 15) + 5;
            return { ...bus, x: nextX };
          }
          return bus;
        });

        // Randomly nudge volunteer stewards coordinates
        const nextVolunteers = prev.volunteers.map((v: any) => ({
          ...v,
          x: v.x + (Math.floor(Math.random() * 6) - 3),
          y: v.y + (Math.floor(Math.random() * 6) - 3)
        }));

        return {
          ...prev,
          attendance: Math.max(1000, prev.attendance + attendanceOffset),
          energyConsumption: Math.max(50, prev.energyConsumption + energyOffset),
          riskScore: parseFloat(newRisk.toFixed(1)),
          healthScore: Math.round(100 - newRisk),
          buses: nextBuses,
          volunteers: nextVolunteers
        };
      });
      setTimeout(() => setSyncStatus("SYNCED"), 600);
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  // START FIFA DEMO Sequence Automator
  const handleStartDemo = () => {
    if (demoRunning) {
      if (demoIntervalRef.current) clearInterval(demoIntervalRef.current);
      setDemoRunning(false);
      return;
    }

    setDemoRunning(true);
    let scenarioIdx = 0;
    
    // Cycle every 8 seconds
    demoIntervalRef.current = setInterval(() => {
      scenarioIdx = (scenarioIdx + 1) % scenarioNames.length;
      const nextScenarioName = scenarioNames[scenarioIdx];
      setActiveScenarioName(nextScenarioName);
    }, 8000);
  };

  useEffect(() => {
    return () => {
      if (demoIntervalRef.current) clearInterval(demoIntervalRef.current);
    };
  }, []);

  const handleCommandApproval = (commandTitle: string, isApproved: boolean) => {
    setApprovedCommands((prev) => ({ ...prev, [commandTitle]: isApproved }));
    if (isApproved) {
      setExecutedCommands((prev) => [commandTitle, ...prev]);
      setCommandFeedback(`Command "${commandTitle}" approved & dispatched successfully via Two-Person Auth.`);
    } else {
      setCommandFeedback(`Command "${commandTitle}" rejected by operator constraint override.`);
    }
    setTimeout(() => setCommandFeedback(null), 4000);
  };

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Top Header Row */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-red-600 text-white font-bold text-[9px] px-2 py-0.5 rounded tracking-widest uppercase">
              FIFA OPERATIONS
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-[10px] text-zinc-400 font-mono">Digital Twin Synced: {syncStatus}</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white mt-1 uppercase flex items-center gap-2">
            <Brain className="text-primary animate-pulse" size={24} /> Aegis Smart Stadium OS — Executive Commander Dashboard
          </h1>
        </div>

        {/* Demo Controller Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleStartDemo}
            className={`px-5 py-3 rounded-lg text-xs font-black tracking-widest uppercase transition-all shadow flex items-center gap-2 ${
              demoRunning
                ? "bg-red-600 hover:bg-red-700 text-white animate-pulse"
                : "bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-black font-black"
            }`}
          >
            <Sparkles size={14} className={demoRunning ? "animate-spin" : ""} />
            {demoRunning ? "Stop FIFA Demo" : "Start FIFA Demo"}
          </button>
        </div>
      </div>

      {commandFeedback && (
        <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs flex items-center gap-2 animate-fadeIn">
          <CheckCircle size={14} />
          <span>{commandFeedback}</span>
        </div>
      )}

      {/* Scenarios Picker Grid */}
      <div className="bg-zinc-950/80 border border-zinc-850 p-4 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">
            FIFA Match Simulation Controller
          </span>
          {demoRunning && (
            <span className="text-[9px] text-yellow-500 font-bold animate-pulse font-mono uppercase">
              Autopilot Mode Active — Cycling scenarios
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {scenarioNames.map((name) => (
            <button
              key={name}
              onClick={() => {
                if (demoRunning) handleStartDemo(); // pause autopilot on manual click
                setActiveScenarioName(name);
              }}
              className={`px-3 py-2 rounded text-xs font-bold transition border ${
                activeScenarioName === name
                  ? "bg-primary text-primary-foreground border-primary shadow"
                  : "bg-zinc-900 text-zinc-400 border-zinc-850 hover:bg-zinc-800"
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {/* Dashboard KPI and Gauges Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {/* Stadium Health Circular Gauge */}
        <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Overall Health</span>
            <span className="text-3xl font-black block text-emerald-400 font-mono">{liveTelemetry.healthScore}%</span>
            <span className="text-[9px] text-zinc-400 block">Ingestion telemetry nominal</span>
          </div>
          <div className="relative h-14 w-14 flex items-center justify-center">
            <svg className="absolute w-full h-full transform -rotate-90">
              <circle cx="28" cy="28" r="24" className="stroke-zinc-800" strokeWidth="4" fill="transparent" />
              <circle cx="28" cy="28" r="24" className="stroke-emerald-500" strokeWidth="4" fill="transparent"
                strokeDasharray={150} strokeDashoffset={150 - (150 * liveTelemetry.healthScore) / 100} />
            </svg>
            <Brain size={18} className="text-emerald-400" />
          </div>
        </div>

        {/* Operational Risk Gauge */}
        <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Risk Index</span>
            <span className={`text-3xl font-black block font-mono ${liveTelemetry.riskScore > 50 ? "text-red-400" : "text-yellow-400"}`}>
              {liveTelemetry.riskScore}%
            </span>
            <span className="text-[9px] text-zinc-400 block uppercase font-semibold">Status: {liveTelemetry.riskScore > 50 ? "CRITICAL" : "NOMINAL"}</span>
          </div>
          <div className="relative h-14 w-14 flex items-center justify-center">
            <svg className="absolute w-full h-full transform -rotate-90">
              <circle cx="28" cy="28" r="24" className="stroke-zinc-800" strokeWidth="4" fill="transparent" />
              <circle cx="28" cy="28" r="24" className={liveTelemetry.riskScore > 50 ? "stroke-red-500" : "stroke-yellow-500"} strokeWidth="4" fill="transparent"
                strokeDasharray={150} strokeDashoffset={150 - (150 * liveTelemetry.riskScore) / 100} />
            </svg>
            <AlertTriangle size={18} className={liveTelemetry.riskScore > 50 ? "text-red-400" : "text-yellow-400"} />
          </div>
        </div>

        {/* Attendance Counter */}
        <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Attendance</span>
            <span className="text-3xl font-black block font-mono">{liveTelemetry.attendance.toLocaleString()}</span>
            <span className="text-[9px] text-zinc-400 block">Stands Capacity: 65,000 max</span>
          </div>
          <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            <Users size={22} />
          </div>
        </div>

        {/* Sustainability Carbon metrics */}
        <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Carbon Offset</span>
            <span className="text-3xl font-black block text-emerald-400 font-mono">-{liveTelemetry.carbonSavings}%</span>
            <span className="text-[9px] text-zinc-400 block">Energy Load: {liveTelemetry.energyConsumption} kW</span>
          </div>
          <div className="h-12 w-12 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <Zap size={22} />
          </div>
        </div>

        {/* Matchday Details */}
        <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between hover:border-primary/40 transition-all md:col-span-2 lg:col-span-4 xl:col-span-1">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Match Status</span>
            <span className="text-sm font-black block text-primary uppercase leading-tight truncate">
              {liveTelemetry.matchStatus}
            </span>
            <span className="text-[9px] text-zinc-400 block">{liveTelemetry.weather}</span>
          </div>
          <div className="h-12 w-12 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-400">
            <Globe size={22} />
          </div>
        </div>
      </div>

      {/* Middle Layout Grid: Digital Twin & Executive Briefing */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Live Digital Twin Viewport (Col span 2) */}
        <div className="xl:col-span-2 bg-card border border-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
              <Activity className="text-emerald-400 animate-pulse" size={16} />
              Stadium Live Digital Twin Telemetry Viewport
            </h2>
            <span className="text-[9px] bg-zinc-900 border border-zinc-850 px-2 py-0.5 rounded text-zinc-400 font-mono">
              REAL-TIME MAP SYNC ACTIVE
            </span>
          </div>

          {/* SVG Map representing stadium lanes and telemetry */}
          <div className="relative w-full h-[360px] bg-zinc-950 border border-zinc-850 rounded-lg overflow-hidden flex items-center justify-center">
            {/* Grid overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:24px_24px] opacity-10"></div>
            
            {/* Visual Stadium Ring Representation */}
            <svg width="100%" height="100%" viewBox="0 0 500 300" className="absolute">
              {/* Outer boundary Ring */}
              <ellipse cx="250" cy="150" rx="200" ry="110" className="stroke-zinc-800" strokeWidth="2" strokeDasharray="5" fill="none" />
              
              {/* Stadium Bowl outer perimeter */}
              <ellipse cx="250" cy="150" rx="160" ry="85" className="stroke-zinc-700" strokeWidth="4" fill="none" />

              {/* Pitch */}
              <rect x="190" y="115" width="120" height="70" className="stroke-emerald-600/60 fill-emerald-950/20" strokeWidth="2" />
              <line x1="250" y1="115" x2="250" y2="185" className="stroke-emerald-600/60" strokeWidth="2" />
              <circle cx="250" cy="150" r="15" className="stroke-emerald-600/60" strokeWidth="2" fill="none" />

              {/* Dynamic Crowd Heat points */}
              {liveTelemetry.crowdPoints.map((pt: any, idx: number) => (
                <circle
                  key={idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={30 * pt.density}
                  className={liveTelemetry.riskScore > 50 ? "fill-red-500/20 stroke-red-500/30 animate-pulse" : "fill-primary/20 stroke-primary/30 animate-pulse"}
                  strokeWidth="2"
                />
              ))}

              {/* Active Shuttle Bus movement representation */}
              {liveTelemetry.buses.map((bus: any) => (
                <g key={bus.id} transform={`translate(${bus.x}, ${bus.y})`} className="transition-all duration-1000">
                  <rect x="-8" y="-6" width="16" height="12" rx="2" className="fill-yellow-500 stroke-zinc-950" strokeWidth="1.5" />
                  <circle cx="-5" cy="8" r="2.5" className="fill-zinc-800" />
                  <circle cx="5" cy="8" r="2.5" className="fill-zinc-800" />
                  <text x="-7" y="1" className="fill-black font-black text-[5px] font-mono">{bus.id}</text>
                </g>
              ))}

              {/* Active Volunteer location markers */}
              {liveTelemetry.volunteers.map((v: any) => (
                <g key={v.id} transform={`translate(${v.x}, ${v.y})`}>
                  <circle cx="0" cy="0" r="5" className="fill-indigo-500 stroke-white" strokeWidth="1" />
                  <text x="-3" y="11" className="fill-zinc-400 font-mono text-[7px]">{v.name}</text>
                </g>
              ))}

              {/* Gate indicators */}
              <g transform="translate(90, 150)">
                <circle cx="0" cy="0" r="8" className={liveTelemetry.gateState === "congested" ? "fill-red-500/20 stroke-red-500 animate-pulse" : "fill-emerald-500/20 stroke-emerald-500 animate-pulse"} strokeWidth="2" />
                <text x="-25" y="-12" className="fill-zinc-300 font-mono text-[8px] font-bold">Gate D</text>
              </g>

              <g transform="translate(410, 150)">
                <circle cx="0" cy="0" r="8" className="fill-emerald-500/20 stroke-emerald-500 animate-pulse" strokeWidth="2" />
                <text x="5" y="-12" className="fill-zinc-300 font-mono text-[8px] font-bold">Gate E</text>
              </g>
            </svg>

            {/* Labels overlay */}
            <div className="absolute bottom-4 left-4 bg-zinc-900/90 border border-zinc-800 p-3 rounded-lg text-[10px] space-y-1.5 font-mono">
              <span className="font-bold text-zinc-400 block mb-1">LEGEND</span>
              <div className="flex items-center gap-2 text-zinc-300">
                <span className="h-2 w-2 rounded bg-yellow-500"></span>
                <span>Active Shuttles</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <span className="h-2.5 w-2.5 rounded-full bg-indigo-500"></span>
                <span>Volunteer Stewards</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                <span>Gate Status: NOMINAL</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-300">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
                <span>Gate Status: BOTTLENECK</span>
              </div>
            </div>

            {/* Live Camera Feed Simulated Overlay */}
            <div className="absolute top-4 right-4 bg-zinc-950/80 border border-zinc-850 p-2.5 rounded-md text-[9px] font-mono space-y-1">
              <span className="text-zinc-400 block font-bold">CCTV BROADCAST STREAM</span>
              <div className="h-14 w-28 bg-zinc-900 border border-zinc-800 rounded flex items-center justify-center text-[7px] text-zinc-500 relative">
                <span className="absolute top-1 left-1 text-red-500 animate-pulse font-bold">● LIVE</span>
                <span>CAM-04 (GATE D)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Premium Executive AI Briefing Panel */}
        <div className="bg-card border border-border rounded-xl p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
              <Brain className="text-primary animate-pulse" size={18} />
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                Executive AI Briefing Card
              </h2>
            </div>
            
            <div className="bg-zinc-950/80 border border-zinc-850 p-4 rounded-lg space-y-3 text-xs leading-relaxed">
              <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                <span>COMPILED FOR FIFA COMMANDER</span>
                <span>AUTO-REFRESH: ACTIVE</span>
              </div>
              <p className="text-zinc-200 italic font-semibold">
                "{liveTelemetry.brief}"
              </p>
            </div>

            {/* Sub-system operational readiness states */}
            <div className="space-y-2 pt-2 text-xs">
              <div className="flex justify-between items-center py-1.5 border-b border-zinc-900">
                <span className="text-zinc-400">Security Patrol Status:</span>
                <span className={`font-mono font-bold ${liveTelemetry.securityStatus === "SECURE" ? "text-emerald-400" : "text-red-400"}`}>
                  {liveTelemetry.securityStatus}
                </span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-zinc-900">
                <span className="text-zinc-400">Medical SLA Response:</span>
                <span className={`font-mono font-bold ${liveTelemetry.medicalStatus === "CRITICAL" ? "text-red-400 animate-pulse" : "text-emerald-400"}`}>
                  {liveTelemetry.medicalStatus} (under 3m)
                </span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-zinc-900">
                <span className="text-zinc-400">Volunteer Readiness:</span>
                <span className="text-zinc-250 font-bold font-mono">{liveTelemetry.volunteerReadiness}%</span>
              </div>
              <div className="flex justify-between items-center py-1.5">
                <span className="text-zinc-400">ADA Path Accessibility:</span>
                <span className="text-zinc-250 font-bold font-mono">{liveTelemetry.accessibilityReadiness}%</span>
              </div>
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/20 p-3 rounded-lg text-[10px] text-zinc-400 flex items-center gap-2">
            <Info size={14} className="text-primary flex-shrink-0" />
            <span>Updates automatically upon scenario ingestion or telemetry shifts.</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Explainable recommendations, Timeline & Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Explainable AI Recommendations (Col span 2) */}
        <div className="xl:col-span-2 space-y-6">
          
          <div className="bg-card border border-border p-5 rounded-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <Terminal size={18} className="text-primary" />
                Coordinated AI Recommendations & Command Explainability
              </h2>
              <span className="text-[10px] bg-primary/10 border border-primary/20 px-2 py-0.5 rounded text-primary font-bold">
                {liveTelemetry.recommendations.length} SUGGESTED OVERRIDES
              </span>
            </div>

            <div className="space-y-4">
              {liveTelemetry.recommendations.map((rec: any, idx: number) => (
                <div key={idx} className="bg-zinc-950/80 border border-zinc-850 p-5 rounded-lg space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-900 pb-3">
                    <div>
                      <h3 className="text-xs font-bold text-primary flex items-center gap-2">
                        {rec.title}
                        {rec.requiresApproval && (
                          <span className="bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 text-[9px] px-2 py-0.5 rounded uppercase">
                            APPROVAL REQUIRED
                          </span>
                        )}
                      </h3>
                      <span className="text-[9px] text-zinc-500 font-mono">Generated: {rec.time} | Confidence: {Math.round(rec.confidence * 100)}%</span>
                    </div>

                    {rec.requiresApproval && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleCommandApproval(rec.title, true)}
                          disabled={approvedCommands[rec.title] !== undefined}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded text-[10px] transition disabled:opacity-50"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleCommandApproval(rec.title, false)}
                          disabled={approvedCommands[rec.title] !== undefined}
                          className="bg-red-600 hover:bg-red-700 text-white font-bold px-3 py-1.5 rounded text-[10px] transition disabled:opacity-50"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-2.5">
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Why:</strong>
                        <span className="text-zinc-300">{rec.why}</span>
                      </div>
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Evidence:</strong>
                        <span className="text-zinc-300">{rec.evidence}</span>
                      </div>
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Alternative Actions:</strong>
                        <span className="text-zinc-300">{rec.alternatives}</span>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Potential Risks:</strong>
                        <span className="text-zinc-300">{rec.risks}</span>
                      </div>
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Expected Improvement:</strong>
                        <span className="text-zinc-300">{rec.expectedImprovement}</span>
                      </div>
                      <div>
                        <strong className="text-zinc-500 uppercase tracking-widest text-[9px] block">Affected Departments:</strong>
                        <span className="text-zinc-300">{rec.depts.join(", ")}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive SVG Inline Charts */}
          <div className="bg-card border border-border p-5 rounded-xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              Operational Performance Trend Charts (Live Ingest)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Crowd arrivals trend SVG chart */}
              <div className="bg-zinc-950/80 border border-zinc-850 p-4 rounded-lg space-y-2">
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">
                  Crowd arrivals flow rate (entries/min)
                </span>
                <div className="h-28 w-full flex items-end">
                  <svg className="w-full h-full">
                    {/* Grid line */}
                    <line x1="0" y1="80" x2="500" y2="80" stroke="#27272a" strokeWidth="1" strokeDasharray="3" />
                    {/* Dynamic line representation */}
                    <path
                      d={
                        activeScenarioName === "Pre-Match"
                          ? "M 0 90 Q 100 80 200 60 T 400 30"
                          : activeScenarioName === "Crowd Surge"
                          ? "M 0 90 Q 100 80 200 30 T 400 10"
                          : "M 0 90 Q 100 70 200 50 T 400 40"
                      }
                      fill="none"
                      stroke="#818cf8"
                      strokeWidth="2.5"
                    />
                  </svg>
                </div>
                <div className="flex justify-between text-[8px] text-zinc-500 font-mono">
                  <span>-30 MINS</span>
                  <span>CURRENT (KICKOFF)</span>
                </div>
              </div>

              {/* Transit vehicle fleet utilization SVG */}
              <div className="bg-zinc-950/80 border border-zinc-850 p-4 rounded-lg space-y-2">
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider block">
                  Transit Shuttles capacity utilization (%)
                </span>
                <div className="h-28 w-full flex items-end">
                  <svg className="w-full h-full">
                    <line x1="0" y1="50" x2="500" y2="50" stroke="#27272a" strokeWidth="1" strokeDasharray="3" />
                    <path
                      d={
                        activeScenarioName === "Pre-Match"
                          ? "M 0 80 Q 150 40 300 60 T 500 50"
                          : activeScenarioName === "Halftime"
                          ? "M 0 60 Q 150 30 300 20 T 500 10"
                          : "M 0 70 Q 150 50 300 40 T 500 30"
                      }
                      fill="none"
                      stroke="#34d399"
                      strokeWidth="2.5"
                    />
                  </svg>
                </div>
                <div className="flex justify-between text-[8px] text-zinc-500 font-mono">
                  <span>-30 MINS</span>
                  <span>CURRENT</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Live AI Timeline & Command Audit Ledger */}
        <div className="space-y-6">
          
          {/* Animated timeline */}
          <div className="bg-card border border-border p-5 rounded-xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2 border-b border-zinc-800 pb-2">
              <Clock size={16} className="text-primary animate-pulse" />
              Live AI Operational Reasoning Timeline
            </h2>
            
            <div className="relative pl-6 border-l border-zinc-800 space-y-5 py-2">
              {liveTelemetry.timeline.map((item: any, idx: number) => (
                <div key={idx} className="relative flex flex-col gap-1 text-xs">
                  {/* Timeline dot */}
                  <span className={`absolute -left-[30px] top-1 h-3.5 w-3.5 rounded-full border-2 border-zinc-950 ${
                    item.status === "alert" ? "bg-red-500 animate-ping" : "bg-emerald-500"
                  }`}></span>
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-[9px] text-zinc-500">{item.time}</span>
                    <span className="text-[9px] bg-zinc-900 border border-zinc-850 px-1.5 py-0.5 rounded text-zinc-400 font-bold uppercase">
                      {item.agent}
                    </span>
                  </div>
                  <p className="text-zinc-200 font-semibold leading-relaxed">{item.action}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recently Executed Commands Audit trail */}
          <div className="bg-card border border-border p-5 rounded-xl space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
              Recently Executed Commands Ledger
            </h2>
            {executedCommands.length === 0 ? (
              <div className="text-center py-8 text-xs text-zinc-500">
                No commands approved yet. Approve a recommendation to execute.
              </div>
            ) : (
              <div className="space-y-2">
                {executedCommands.map((cmd, idx) => (
                  <div key={idx} className="bg-zinc-950/70 border border-zinc-850 p-3 rounded-lg flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <CheckCircle size={14} className="text-emerald-500" />
                      <div>
                        <span className="font-semibold text-zinc-200 block">{cmd}</span>
                        <span className="text-[9px] text-zinc-500 font-mono">RBAC Override Signed</span>
                      </div>
                    </div>
                    <span className="text-[9px] text-zinc-400 bg-zinc-900 px-2 py-1 rounded">
                      EXECUTED
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
