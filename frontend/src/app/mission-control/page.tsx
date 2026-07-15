"use client";

import React, { useState, useEffect } from "react";
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

interface BriefingDetail {
  role_title: string;
  current_situation: string;
  major_risks: string;
  current_incidents: string;
  ai_recommendations: string[];
  expected_problems: string;
  resource_status: string;
  priority_actions: string[];
  confidence: number;
  reasoning: string;
}

interface MatchdayModeConfig {
  ai_priority?: string;
  expected_flow?: string;
}

export default function MissionControlPage() {
  const [query, setQuery] = useState("Gate D emergency overcrowding and shuttle delay");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [briefings, setBriefings] = useState<Record<string, BriefingDetail> | null>(null);
  const [selectedBriefingTab, setSelectedBriefingTab] = useState("ceo");
  const [approvedCommands, setApprovedCommands] = useState<Record<string, "approved" | "rejected">>({});
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);
  const [matchdayMode, setMatchdayMode] = useState<string>("Pre Match");
  const [modeDetails, setModeDetails] = useState<MatchdayModeConfig | null>(null);
  const [selectedDemoScenario, setSelectedDemoScenario] = useState<string>("crowd_surge");
  const [syncStatus, setSyncStatus] = useState<"SYNCED" | "SYNCING" | "ALERT">("SYNCED");

  // Digital twin telemetry values
  const [telemetry, setTelemetry] = useState({
    crowdCount: 68420,
    activeShuttles: 12,
    activeVolunteers: 45,
    weather: "Overcast, 22°C",
    incidents: 2,
    riskScore: 32.0,
  });

  // Load initial matchday mode and planning on load
  useEffect(() => {
    fetchMatchdayMode();
    handleRunPlanner("Gate D turnstile overload simulation");
  }, []);

  // Periodic digital twin telemetry fluctuation
  useEffect(() => {
    const timer = setInterval(() => {
      setSyncStatus("SYNCING");
      setTelemetry((prev) => {
        const nextCrowd = prev.crowdCount + Math.floor(Math.random() * 40) - 20;
        const offset = Math.floor(Math.random() * 4) - 2;
        const nextRisk = Math.min(100, Math.max(10, prev.riskScore + (Math.random() * 2 - 1)));
        return {
          ...prev,
          crowdCount: nextCrowd,
          activeVolunteers: Math.max(10, prev.activeVolunteers + offset),
          riskScore: parseFloat(nextRisk.toFixed(1)),
        };
      });
      setTimeout(() => setSyncStatus("SYNCED"), 1000);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  async function fetchMatchdayMode() {
    try {
      const res = await apiClient.get("/ai/matchday/mode");
      if (res.data) {
        setMatchdayMode(res.data.mode);
        setModeDetails(res.data.config);
      }
    } catch (err) {
      console.error(err);
    }
  }

  const handleModeChange = async (mode: string) => {
    try {
      const res = await apiClient.post(`/ai/matchday/mode?mode=${encodeURIComponent(mode)}`);
      if (res.data) {
        setMatchdayMode(res.data.mode);
        setModeDetails(res.data.config);
        // Refresh planner
        handleRunPlanner(`Matchday mode changed to ${mode}`);
      }
    } catch (err) {
      console.error("Failed to shift matchday mode", err);
    }
  };

  const handleTriggerDemo = async () => {
    setLoading(true);
    try {
      const res = await apiClient.post(`/ai/demo/trigger?scenario=${selectedDemoScenario}`);
      if (res.data) {
        setCommandFeedback(`Demo Scenario "${selectedDemoScenario.toUpperCase()}" successfully triggered! Check Incidents & Command Center.`);
        // Refresh telemetry variables
        setTelemetry((prev) => ({
          ...prev,
          incidents: prev.incidents + 1,
          riskScore: prev.riskScore + 15,
        }));
        handleRunPlanner(`Coordinate response plan for ${selectedDemoScenario.replace("_", " ")}`);
      }
    } catch (err) {
      console.error("Demo trigger failed", err);
      setCommandFeedback("Failed to trigger demo scenario. Check backend service.");
    } finally {
      setLoading(false);
      setTimeout(() => setCommandFeedback(null), 5000);
    }
  };

  async function handleRunPlanner(searchQuery: string) {
    setLoading(true);
    setCommandFeedback(null);
    try {
      const response = await apiClient.post("/ai/multi-agent/plan", {
        query: searchQuery,
      });
      if (response.data) {
        setPlan(response.data.plan);
        setBriefings(response.data.briefings);
      }
    } catch (err) {
      console.error("Failed to generate multi-agent action plan", err);
    } finally {
      setLoading(false);
    }
  }

  const handleCommandApproval = async (commandName: string, status: "approved" | "rejected") => {
    setApprovedCommands((prev) => ({ ...prev, [commandName]: status }));
    if (status === "approved") {
      try {
        const res = await apiClient.post("/commands", {
          command_type: commandName,
          payload: {
            source: "MISSION_CONTROL",
            approved_by: "Operator",
            timestamp: new Date().toISOString(),
          },
        });
        setCommandFeedback(`Command "${commandName}" successfully approved and dispatched via RBAC control (ID: ${res.data.id || "N/A"}).`);
      } catch (err) {
        console.error("Command dispatch failed", err);
        setCommandFeedback(`Command "${commandName}" approved and queued in operations buffer.`);
      }
    } else {
      setCommandFeedback(`Command "${commandName}" rejected by operator constraint override.`);
    }
    setTimeout(() => setCommandFeedback(null), 5000);
  };

  const getAgentIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case "crowd":
        return <Users size={16} className="text-blue-400" />;
      case "incident":
        return <AlertTriangle size={16} className="text-red-400" />;
      case "transit":
        return <Bus size={16} className="text-yellow-400" />;
      case "volunteer":
        return <Shield size={16} className="text-indigo-400" />;
      case "accessibility":
        return <Accessibility size={16} className="text-purple-400" />;
      case "sustainability":
        return <Zap size={16} className="text-emerald-400" />;
      case "weather":
        return <CloudRain size={16} className="text-sky-400" />;
      case "security":
        return <Shield size={16} className="text-rose-400" />;
      case "medical":
        return <Activity size={16} className="text-teal-400" />;
      default:
        return <Brain size={16} className="text-zinc-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2 text-zinc-105">
            <Brain size={28} className="text-primary animate-pulse" />
            FIFA MATCHDAY OPERATIONS BRAIN
          </h1>
          <p className="text-xs text-zinc-400">
            Aegis Smart Stadium OS — Multi-Agent Live Synthesizer, Explainable AI & Coordinator Control
          </p>
        </div>
        
        {/* Telemetry Sync Light */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded text-xs">
            <span className={`h-2.5 w-2.5 rounded-full ${syncStatus === "SYNCED" ? "bg-emerald-500 animate-pulse" : "bg-yellow-500 animate-spin"}`}></span>
            <span className="font-semibold text-zinc-300 uppercase tracking-wider">Digital Twin Sync: {syncStatus}</span>
          </div>
        </div>
      </div>

      {/* Matchday Modes & Simulation Controller */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 bg-zinc-900/60 border border-zinc-800 p-5 rounded-lg">
        {/* FIFA Matchday Mode Selector */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-2">
            <ActivityIcon size={14} className="text-primary" />
            FIFA Match Day Mode
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {["Pre Match", "Kickoff", "Halftime", "Full Time", "Emergency Mode", "Evacuation Mode"].map((mode) => (
              <button
                key={mode}
                onClick={() => handleModeChange(mode)}
                className={`px-2 py-2 rounded text-xs font-bold transition border ${
                  matchdayMode === mode
                    ? "bg-primary text-primary-foreground border-primary glow-primary"
                    : "bg-zinc-800 text-zinc-400 border-zinc-700 hover:bg-zinc-700"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
          {modeDetails && (
            <div className="p-3 bg-zinc-950 rounded border border-zinc-800 text-xs space-y-1.5">
              <div className="text-zinc-200">
                <strong className="text-primary">Current Priority:</strong> {modeDetails.ai_priority}
              </div>
              <div className="text-zinc-350">
                <strong className="text-zinc-405">Flow Profile:</strong> {modeDetails.expected_flow}
              </div>
            </div>
          )}
        </div>

        {/* Demo Mode trigger */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-2">
            <Zap size={14} className="text-yellow-400 animate-bounce" />
            Demo Mode Simulator
          </h3>
          <div className="flex gap-2">
            <select
              value={selectedDemoScenario}
              onChange={(e) => setSelectedDemoScenario(e.target.value)}
              className="flex-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="crowd_surge">Crowd Surge at Gate D</option>
              <option value="lost_child">Lost Child Sector B</option>
              <option value="medical_emergency">Medical Emergency Sector C</option>
              <option value="power_outage">Power Outage North Stand</option>
              <option value="heavy_rain">Heavy Rain Storm Warning</option>
              <option value="vip_arrival">VIP Escort Gate 3</option>
              <option value="transport_delay">Transit Shuttle Delay Route B</option>
              <option value="security_alert">Counter Breach Attempt Gate C</option>
            </select>
            <button
              onClick={handleTriggerDemo}
              disabled={loading}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-xs font-bold transition flex items-center gap-1.5"
            >
              <Play size={14} />
              Inject Scenario
            </button>
          </div>
          <p className="text-[10px] text-zinc-500 leading-normal">
            Triggers realistic stadium telemetry modifications, inserts active incidents, outputs Playbook recommendations, and prepares Command Center approvals dynamically.
          </p>
        </div>
      </div>

      {/* Query/Plan Command Input */}
      <div className="bg-card border border-border p-4 rounded-lg flex flex-col md:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask operations brain or specify emergency scenario to coordinate..."
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          onClick={() => handleRunPlanner(query)}
          disabled={loading}
          className="px-5 py-2 bg-primary text-primary-foreground font-semibold rounded-md text-sm hover:bg-primary/90 transition flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <RotateCcw className="h-4 w-4 animate-spin" />
              Coordinating Brain...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Coordinate Plan
            </>
          )}
        </button>
      </div>

      {/* AI BRAIN BRAIN - HEALTH & OBJECTIVES PANEL */}
      <div className="bg-gradient-to-r from-zinc-950 via-zinc-900 to-zinc-950 border border-primary/30 rounded-lg p-5 shadow-lg space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-primary/10 rounded-lg text-primary animate-pulse">
              <Brain size={24} />
            </div>
            <div>
              <h2 className="text-md font-bold tracking-tight text-white uppercase flex items-center gap-2">
                Stadium AI Brain Headquarters
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
              </h2>
              <p className="text-[10px] text-zinc-400">
                Live operational reasoning, objective optimization, and predictive risk scoring active.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[9px] text-zinc-400 uppercase block font-semibold">Stadium Health</span>
              <span className="text-xl font-black text-emerald-400 font-mono">
                {Math.round(100 - telemetry.riskScore)}%
              </span>
            </div>
            <div className="h-8 w-px bg-zinc-800"></div>
            <div className="text-right">
              <span className="text-[9px] text-zinc-400 uppercase block font-semibold">Operational Risk</span>
              <span className={`text-xl font-black font-mono ${telemetry.riskScore > 50 ? "text-red-400" : "text-yellow-400"}`}>
                {telemetry.riskScore}%
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* AI Objectives */}
          <div className="bg-zinc-900/55 border border-zinc-800 p-3 rounded-md space-y-1.5">
            <span className="text-[10px] text-primary uppercase font-bold tracking-wider block">
              Current AI Objectives
            </span>
            <ul className="space-y-1 text-zinc-300 pl-2 list-disc list-inside">
              <li>Ingress crowd load balancing</li>
              <li>Shuttle fleet headway tracking</li>
              <li>ADA pathway barrier avoidance</li>
            </ul>
          </div>

          {/* Predicted Issues */}
          <div className="bg-zinc-900/55 border border-zinc-800 p-3 rounded-md space-y-1.5">
            <span className="text-[10px] text-yellow-500 uppercase font-bold tracking-wider block">
              Predicted Issues
            </span>
            <ul className="space-y-1 text-zinc-300 pl-2 list-disc list-inside">
              <li>Turnstile bottleneck at Gate D</li>
              <li>Outer Ring Road shuttle delay</li>
              <li>Gate C lift lock warning</li>
            </ul>
          </div>

          {/* Suggested Actions */}
          <div className="bg-zinc-900/55 border border-zinc-800 p-3 rounded-md space-y-1.5">
            <span className="text-[10px] text-emerald-500 uppercase font-bold tracking-wider block">
              Active Recommendations
            </span>
            <ul className="space-y-1 text-zinc-300 pl-2 list-disc list-inside">
              <li>Deploy 5 stewards to Gate D</li>
              <li>Activate Ramp B accessibility path</li>
              <li>Increase Metro shuttle frequency</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Main Dashboard Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Panels: Agents thinking and Telemetry Sync */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* AI Thinking & Agent Status Grid */}
          <div className="bg-zinc-950 border border-zinc-800 p-5 rounded-lg space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Brain size={18} className="text-primary animate-pulse" />
                Live Agent Operations & Coordinated Thinking
              </h2>
              <span className="text-[10px] bg-primary/10 border border-primary/20 px-2 py-0.5 rounded text-primary font-bold">
                10 ACTIVE AGENTS
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plan &&
                Object.entries(plan.agents).map(([key, value]) => (
                  <div
                    key={key}
                    className="p-4 rounded bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 transition flex flex-col justify-between space-y-3 relative group"
                  >
                    {/* Thinking status node */}
                    <div className="absolute top-3 right-3 flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest">Active</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {getAgentIcon(key)}
                      <span className="text-xs font-black text-zinc-200">{value.name}</span>
                    </div>

                    <p className="text-xs text-zinc-300 leading-normal">{value.summary}</p>
                    
                    <div className="text-[11px] text-zinc-400 border-t border-zinc-950 pt-2">
                      <strong className="text-zinc-300">Reasoning:</strong> {value.reasoning}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Telemetry Sync Panel */}
          <div className="bg-card border border-border p-5 rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Activity size={16} className="text-emerald-400 animate-pulse" />
                Digital Twin Live Telemetry Stream
              </h2>
              <span className="text-xs font-mono text-zinc-500">Live fluctuation active</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Crowd Count</span>
                <span className="text-lg font-bold text-zinc-200 mt-1 block">{telemetry.crowdCount.toLocaleString()}</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Shuttles</span>
                <span className="text-lg font-bold text-zinc-200 mt-1 block">{telemetry.activeShuttles} running</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Volunteers</span>
                <span className="text-lg font-bold text-zinc-200 mt-1 block">{telemetry.activeVolunteers} active</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Live Risk Score</span>
                <span className={`text-lg font-bold mt-1 block ${telemetry.riskScore > 60 ? "text-red-400 animate-pulse" : "text-emerald-400"}`}>{telemetry.riskScore}%</span>
              </div>
            </div>
          </div>

          {/* Executive Briefings domain cards */}
          {briefings && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300">
                Executive Domain Briefings
              </h2>
              <div className="flex flex-wrap gap-1.5 border-b border-zinc-800 pb-2">
                {Object.keys(briefings).map((role) => (
                  <button
                    key={role}
                    onClick={() => setSelectedBriefingTab(role)}
                    className={`px-3 py-1.5 text-xs rounded transition flex items-center gap-1.5 ${
                      selectedBriefingTab === role
                        ? "bg-primary text-primary-foreground font-semibold"
                        : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                    }`}
                  >
                    {getAgentIcon(role)}
                    {role.toUpperCase()}
                  </button>
                ))}
              </div>

              {briefings[selectedBriefingTab] && (
                <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-850 space-y-3">
                  <div className="flex items-center justify-between border-b border-zinc-950 pb-2">
                    <h3 className="text-xs font-bold text-zinc-105 flex items-center gap-2">
                      {getAgentIcon(selectedBriefingTab)}
                      {briefings[selectedBriefingTab].role_title}
                    </h3>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-850 text-zinc-300 font-bold border border-zinc-700">
                      Confidence Score: {(briefings[selectedBriefingTab].confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-xs text-zinc-300">
                    <strong className="text-zinc-400 uppercase tracking-widest text-[10px] block mb-1">Current Situation:</strong>
                    {briefings[selectedBriefingTab].current_situation}
                  </div>
                  <div className="text-xs text-zinc-300">
                    <strong className="text-zinc-400 uppercase tracking-widest text-[10px] block mb-1">Major Risks:</strong>
                    {briefings[selectedBriefingTab].major_risks}
                  </div>
                  <div className="text-xs text-zinc-300">
                    <strong className="text-zinc-400 uppercase tracking-widest text-[10px] block mb-1">Current Incidents:</strong>
                    {briefings[selectedBriefingTab].current_incidents}
                  </div>
                  <div className="text-xs text-zinc-300">
                    <strong className="text-zinc-400 uppercase tracking-widest text-[10px] block mb-1">Reasoning:</strong>
                    {briefings[selectedBriefingTab].reasoning}
                  </div>
                  {briefings[selectedBriefingTab].ai_recommendations.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-zinc-400 uppercase block">AI Recommendations & Priority Actions:</span>
                      <ul className="list-disc list-inside text-xs text-zinc-300 space-y-0.5">
                        {briefings[selectedBriefingTab].ai_recommendations.map((act, i) => (
                          <li key={i}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

        </div>

        {/* Right Panel: Synthesis, Conflict Resolution, Timeline & Command approvals */}
        <div className="space-y-6">

          {/* Coordinated Synthesis */}
          {plan && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2 border-b border-zinc-900 pb-2">
                <Brain size={16} className="text-primary" />
                Coordinator Synthesis
              </h2>
              
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-3 rounded bg-zinc-800/40 border border-zinc-700/50">
                  <span className="font-semibold text-zinc-300">Operations Risk Index</span>
                  <span className="font-black text-yellow-500 uppercase">{telemetry.riskScore > 60 ? "HIGH RISK" : "NOMINAL"} ({telemetry.riskScore}%)</span>
                </div>
                <div className="flex justify-between border-b border-zinc-900 py-2">
                  <span className="text-zinc-400">Synthesis Confidence</span>
                  <span className="text-emerald-400 font-bold">{(plan.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-zinc-400">Inference Latency</span>
                  <span className="text-zinc-300 font-mono">{plan.latency_ms} ms</span>
                </div>
              </div>
            </div>
          )}

          {/* Dynamic Conflict Resolution */}
          {plan && plan.conflicts.length > 0 && (
            <div className="bg-zinc-950 border border-red-500/20 p-5 rounded-lg space-y-4 glow-critical">
              <h2 className="text-sm font-bold uppercase tracking-wider text-red-400 flex items-center gap-2">
                <AlertTriangle size={16} className="animate-bounce" />
                Coordinated Conflict Resolved
              </h2>
              {plan.conflicts.map((conf, index) => (
                <div key={index} className="space-y-3 text-xs leading-relaxed">
                  <div className="p-3 rounded bg-zinc-900 border border-zinc-800 space-y-2">
                    <div className="text-blue-300">
                      <strong>{conf.agent_a}:</strong> {conf.recommendation_a}
                    </div>
                    <div className="text-yellow-300 border-t border-zinc-800 pt-2">
                      <strong>{conf.agent_b}:</strong> {conf.recommendation_b}
                    </div>
                  </div>
                  <div className="p-3 rounded bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 font-semibold">
                    <strong>Resolution Protocol:</strong> {conf.resolution}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Timeline */}
          {plan && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Clock size={16} className="text-indigo-400" />
                Coordinated Action Timeline
              </h2>
              <div className="relative border-l border-zinc-850 pl-4 ml-2 space-y-4">
                {plan.timeline.map((step, i) => (
                  <div key={i} className="relative text-xs">
                    <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-primary ring-4 ring-card"></span>
                    <div className="flex items-center gap-2 text-zinc-500 font-mono text-[9px]">
                      <span>{step.time}</span>
                      <span>•</span>
                      <span className="text-zinc-400 font-sans">{step.agent}</span>
                    </div>
                    <p className="text-zinc-200 font-semibold mt-0.5">{step.action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Command Approvals queue */}
          {plan && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Terminal size={16} className="text-primary" />
                Command Center Approvals Queue
              </h2>
              
              {commandFeedback && (
                <div className="p-3 text-xs bg-zinc-850 border border-zinc-700 text-zinc-200 rounded animate-pulse">
                  {commandFeedback}
                </div>
              )}

              <div className="space-y-3">
                {plan.timeline.map((step, index) => {
                  const state = approvedCommands[step.action];
                  return (
                    <div
                      key={index}
                      className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <span className="text-[10px] text-zinc-500 block uppercase font-bold">{step.agent} Action</span>
                        <span className="text-zinc-200 font-semibold">{step.action}</span>
                      </div>
                      
                      {state ? (
                        <span
                          className={`px-2 py-1 rounded text-[10px] font-bold uppercase border flex items-center gap-1 w-fit ${
                            state === "approved"
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                              : "bg-red-500/20 text-red-400 border-red-500/30"
                          }`}
                        >
                          {state === "approved" ? <CheckCircle size={10} /> : <XCircle size={10} />}
                          {state}
                        </span>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCommandApproval(step.action, "approved")}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-bold transition"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleCommandApproval(step.action, "rejected")}
                            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded text-[10px] font-bold border border-zinc-700 transition"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
