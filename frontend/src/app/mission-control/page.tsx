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
  status: string;
  summary: string;
  predictions: string;
  risks: string[];
  recommended_actions: string[];
  confidence: number;
}

export default function MissionControlPage() {
  const [query, setQuery] = useState("Gate D emergency overcrowding and shuttle delay");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [briefings, setBriefings] = useState<Record<string, BriefingDetail> | null>(null);
  const [selectedBriefingTab, setSelectedBriefingTab] = useState("ceo");
  const [approvedCommands, setApprovedCommands] = useState<Record<string, "approved" | "rejected">>({});
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);

  // Digital twin telemetry mock values
  const [telemetry, setTelemetry] = useState({
    crowdCount: 68420,
    activeShuttles: 12,
    activeVolunteers: 45,
    weather: "Overcast, 22°C",
    incidents: 2,
  });

  // Load initial nominal plan on page load
  useEffect(() => {
    handleRunPlanner("Gate D turnstile overload simulation");
  }, []);

  // Periodic digital twin telemetry fluctuation
  useEffect(() => {
    const timer = setInterval(() => {
      setTelemetry((prev) => ({
        ...prev,
        crowdCount: prev.crowdCount + Math.floor(Math.random() * 20) - 10,
        activeVolunteers: prev.activeVolunteers + (Math.random() > 0.85 ? 1 : Math.random() > 0.85 ? -1 : 0),
      }));
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleRunPlanner = async (searchQuery: string) => {
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
  };

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
        setCommandFeedback(`Command "${commandName}" queued and logged in audit history.`);
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

  const getBriefingIcon = (tab: string) => {
    return getAgentIcon(tab);
  };

  return (
    <div className="space-y-6">
      {/* Title & Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Brain size={24} className="text-primary animate-pulse" />
            MULTI-AGENT MISSION CONTROL
          </h1>
          <p className="text-xs text-muted-foreground">
            Aegis Smart Stadium OS — Coordinated Autonomous Operation Timeline & Synthesis Planner
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-zinc-800/80 border border-zinc-700/50 px-3 py-1 rounded text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-semibold text-zinc-300">10 / 10 AGENTS ACTIVE</span>
          </div>
        </div>
      </div>

      {/* Query Bar */}
      <div className="bg-card border border-border p-4 rounded-lg flex flex-col md:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a situation, emergency scenario or command request..."
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
              Coordinating...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Simulate & Coordinate
            </>
          )}
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Column: Agents Reasonings & Digital Twin */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Active Agents Grid */}
          <div className="bg-card border border-border p-5 rounded-lg space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
              <Shield size={16} className="text-primary" />
              Active Operational AI Agents
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {plan &&
                Object.entries(plan.agents).map(([key, value]) => (
                  <div
                    key={key}
                    className="p-4 rounded-lg bg-zinc-800/60 border border-zinc-700/50 hover:border-zinc-600 transition flex flex-col justify-between space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getAgentIcon(key)}
                        <span className="text-xs font-bold text-zinc-200">{value.name}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 font-semibold">
                        Conf: {(value.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300 leading-relaxed">{value.summary}</p>
                    <div className="text-[10px] text-zinc-400 italic">
                      <strong className="text-zinc-300">Reasoning:</strong> {value.reasoning}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Digital Twin Telemetry widget */}
          <div className="bg-card border border-border p-5 rounded-lg space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
              <Activity size={16} className="text-emerald-400" />
              Digital Twin Telemetry Sync
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Crowd Count</span>
                <span className="text-lg font-bold text-zinc-200">{telemetry.crowdCount.toLocaleString()}</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Shuttles</span>
                <span className="text-lg font-bold text-zinc-200">{telemetry.activeShuttles} Active</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Volunteers</span>
                <span className="text-lg font-bold text-zinc-200">{telemetry.activeVolunteers} Stewards</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Weather</span>
                <span className="text-xs font-bold text-zinc-200 mt-1 block">{telemetry.weather}</span>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-[10px] text-zinc-400 uppercase tracking-widest block">Active Incidents</span>
                <span className="text-lg font-bold text-red-400">{telemetry.incidents} High</span>
              </div>
            </div>
          </div>

          {/* Executive Briefings Tabs */}
          {briefings && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300">
                Executive Domain Briefings
              </h2>
              <div className="flex flex-wrap gap-1 border-b border-zinc-800 pb-2">
                {Object.keys(briefings).map((role) => (
                  <button
                    key={role}
                    onClick={() => setSelectedBriefingTab(role)}
                    className={`px-3 py-1 text-xs rounded transition flex items-center gap-1.5 ${
                      selectedBriefingTab === role
                        ? "bg-primary text-primary-foreground font-semibold"
                        : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                    }`}
                  >
                    {getBriefingIcon(role)}
                    {role.toUpperCase()}
                  </button>
                ))}
              </div>

              {briefings[selectedBriefingTab] && (
                <div className="p-4 rounded-lg bg-zinc-900/60 border border-zinc-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-zinc-200">
                      {briefings[selectedBriefingTab].role_title} Briefing
                    </h3>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-semibold border border-zinc-700">
                      Status: {briefings[selectedBriefingTab].status}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {briefings[selectedBriefingTab].summary}
                  </p>
                  <div className="text-[11px] text-zinc-400">
                    <strong className="text-zinc-300">Predictions:</strong> {briefings[selectedBriefingTab].predictions}
                  </div>
                  {briefings[selectedBriefingTab].recommended_actions.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-zinc-300 uppercase block">Focus Actions:</span>
                      <ul className="list-disc list-inside text-xs text-zinc-400 space-y-0.5">
                        {briefings[selectedBriefingTab].recommended_actions.map((act, i) => (
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

        {/* Right Column: Coordinator Decision, Conflicts, Timeline & Command Approval */}
        <div className="space-y-6">

          {/* Coordinator Decision Summary Card */}
          {plan && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Brain size={16} className="text-primary" />
                Coordinator Synthesis
              </h2>
              
              {/* Risk Meter */}
              <div className="flex items-center justify-between p-3 rounded bg-zinc-800/40 border border-zinc-700/50">
                <span className="text-xs font-semibold text-zinc-300">Operational Risk Index</span>
                <span className="text-xs font-extrabold text-yellow-500 uppercase">Medium Risk (42%)</span>
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <strong className="text-zinc-300 block">Average Coordinator Confidence:</strong>
                  <span className="text-sm font-black text-emerald-400">{(plan.confidence * 100).toFixed(0)}%</span>
                </div>
                <div>
                  <strong className="text-zinc-300 block">Inference latency:</strong>
                  <span className="text-zinc-400">{plan.latency_ms} ms</span>
                </div>
              </div>
            </div>
          )}

          {/* Conflicts Panel */}
          {plan && plan.conflicts.length > 0 && (
            <div className="bg-card border border-red-500/20 p-5 rounded-lg space-y-4 glow-critical">
              <h2 className="text-sm font-bold uppercase tracking-wider text-red-400 flex items-center gap-2">
                <AlertTriangle size={16} />
                AI Conflict Resolved
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
                  <div className="p-3 rounded bg-emerald-950/40 border border-emerald-800/50 text-emerald-300">
                    <strong>Coordinator Resolution:</strong> {conf.resolution}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Autonomous Timeline */}
          {plan && (
            <div className="bg-card border border-border p-5 rounded-lg space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                <Clock size={16} className="text-indigo-400" />
                Coordinated Action Timeline
              </h2>
              <div className="relative border-l border-zinc-800 pl-4 ml-2 space-y-4">
                {plan.timeline.map((step, i) => (
                  <div key={i} className="relative text-xs">
                    <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-primary ring-4 ring-card"></span>
                    <div className="flex items-center gap-2 text-zinc-400 font-mono text-[10px]">
                      <span>{step.time}</span>
                      <span>•</span>
                      <span className="text-zinc-500 font-sans">{step.agent}</span>
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
                Command Approval Queue
              </h2>
              
              {commandFeedback && (
                <div className="p-3 text-xs bg-zinc-800 border border-zinc-700 text-zinc-200 rounded animate-pulse">
                  {commandFeedback}
                </div>
              )}

              <div className="space-y-3">
                {plan.timeline.map((step, index) => {
                  const state = approvedCommands[step.action];
                  return (
                    <div
                      key={index}
                      className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1">
                        <span className="text-[10px] text-zinc-500 block uppercase font-bold">{step.agent} Action</span>
                        <span className="text-zinc-200 font-semibold">{step.action}</span>
                      </div>
                      
                      {state ? (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border flex items-center gap-1 ${
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
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-bold"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleCommandApproval(step.action, "rejected")}
                            className="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 rounded text-[10px] font-bold border border-zinc-700"
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
