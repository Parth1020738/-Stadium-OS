"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { useAI } from "@/hooks/useAI";
import { ChatMessage as ChatMessageType } from "@/lib/ai-client";
import { apiClient } from "@/lib/api-client";
import { useTelemetryStore } from "@/store/telemetryStore";
import {
  ChatMessage,
  ThinkingIndicator,
  SuggestionCards,
  SourcePanel,
  ReasoningPanel,
  parseMessageSections,
  ConfidenceBadge,
} from "./components";
import {
  MessageSquare,
  Send,
  Sparkles,
  X,
  Terminal,
  HelpCircle,
  FileText,
  LayoutDashboard,
  RefreshCw,
  Globe,
  Play,
  CheckCircle,
  SkipForward,
  Brain,
} from "lucide-react";

interface WorkflowStep {
  id: number;
  command: string;
  detail: string;
  status: "pending" | "approved" | "skipped";
}

export default function CopilotPage() {
  const { loading, error, streamText, startStream, cancel } = useAI();

  const wsConnected = useTelemetryStore((s) => s.wsConnected);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      role: "assistant",
      content:
        "### Summary\nWelcome to Aegis Stadium Copilot. I am your operations assistant.\n\n### Reasoning\nReady to aggregate crowd, incident, transit, and volunteer status data.\n\n### Confidence\n1.0\n\n### Data Sources\nStadium DB, Active Sensor Feeds.\n\n### Recommended Actions\nAsk a question or select a suggested prompt card to inspect stadium operations.\n\n### Alternative Actions\nNone.\n\n### Potential Risks\nNone.",
    },
  ]);

  const [activeSession, setActiveSession] = useState<string>("Session_1");
  const [sessions, setSessions] = useState<string[]>(["Session_1"]);
  const [selectedMessageIdx, setSelectedMessageIdx] = useState<number | null>(
    null,
  );
  const [commandFeedback, setCommandFeedback] = useState<{
    text: string;
    isError?: boolean;
  } | null>(null);
  const [selectedLang, setSelectedLang] = useState<string>("en");
  const [stepStatuses, setStepStatuses] = useState<
    Record<string, "approved" | "skipped">
  >({});

  const chatEndRef = useRef<HTMLDivElement>(null);

  const streamDoneRef = useRef(false);
  useEffect(() => {
    if (loading && streamText) streamDoneRef.current = true;

    if (!loading && streamDoneRef.current) {
      const finalText = streamText?.trim();
      streamDoneRef.current = false;

      if (finalText) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: streamText },
        ]);
      }
    }
  }, [loading, streamText]);

  // Auto-scroll chat to bottom (only when new content is appended)
  const lastMessageCountRef = useRef<number>(messages.length);
  useEffect(() => {
    if (messages.length !== lastMessageCountRef.current) {
      lastMessageCountRef.current = messages.length;
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

  const handleSubmit = (text: string) => {
    if (!text.trim()) return;
    setInput("");

    // Append translation instructions if not English
    const targetQuery =
      selectedLang !== "en" ? `${text} (Translate to ${selectedLang})` : text;

    // Append user query
    setMessages((prev) => [...prev, { role: "user", content: text }]);

    // Trigger stream
    startStream(targetQuery);
  };

  const handleSelectPrompt = (prompt: string) => {
    handleSubmit(prompt);
  };

  const CRITICAL_COMMAND_TYPE = {
    gate_rate_override: "GATE_RATE_OVERRIDE",
    accessibility_override: "ACCESSIBILITY_OVERRIDE",
    emergency_evacuation: "EMERGENCY_EVACUATION",
    emergency_broadcast: "EMERGENCY_BROADCAST",
  } as const;

  const handleActionExecute = async (command: string, actionType: string) => {
    if (actionType === "explain" || actionType === "view_route") {
      handleSubmit(`Explain recommended action: ${command}`);
      return;
    }

    try {
      // Trigger actual Command Center API dispatch
      const payload: Record<string, unknown> = {
        action: actionType,
        source: "AI_COPILOT",
        timestamp: new Date().toISOString(),
      };

      // Contract alignment: backend approval is only created for specific command_type constants.
      // Keep UI labels (`command`) intact but map critical operations to backend command_type.
      let commandTypeToSubmit = command;

      const cmdLower = command.toLowerCase();
      if (cmdLower.includes("open gate d")) {
        commandTypeToSubmit = CRITICAL_COMMAND_TYPE.gate_rate_override;
      } else if (
        cmdLower.includes("accessibility") ||
        cmdLower.includes("ada")
      ) {
        commandTypeToSubmit = CRITICAL_COMMAND_TYPE.accessibility_override;
      } else if (
        cmdLower.includes("evacuation") ||
        cmdLower.includes("emergency")
      ) {
        commandTypeToSubmit = CRITICAL_COMMAND_TYPE.emergency_evacuation;
      }

      const response = await apiClient.post("/commands", {
        command_type: commandTypeToSubmit,
        payload: payload,
      });

      if (response.status === 201 || response.status === 200) {
        setCommandFeedback({
          text: `Command "${command}" [Action: ${actionType.toUpperCase()}] submitted successfully (ID: ${response.data.id}).`,
        });
      }
    } catch (err: unknown) {
      const errResponse = err as { response?: { data?: { detail?: string } } };
      const errDetail =
        errResponse.response?.data?.detail ||
        "Operation failed under current security roles.";

      setCommandFeedback({
        text: `Failed to execute: ${errDetail}`,
        isError: true,
      });
    }

    setTimeout(() => setCommandFeedback(null), 7000);
  };

  const activeIdx =
    selectedMessageIdx !== null ? selectedMessageIdx : messages.length - 1;
  const activeMessage = messages[activeIdx] || messages[messages.length - 1];

  const activeSections = useMemo(() => {
    if (!activeMessage) {
      return {
        summary: "",
        reasoning: "",
        confidence: "",
        sources: "",
        recommendedActions: "",
        alternativeActions: "",
        potentialRisks: "",
        workflow: "",
      };
    }
    return parseMessageSections(activeMessage.content);
  }, [activeMessage?.content]);

  // Parse and track workflow steps from active sections dynamically using useMemo
  const workflowSteps = React.useMemo(() => {
    if (!activeSections.workflow) return [];
    const lines = activeSections.workflow.split("\n");
    const steps: WorkflowStep[] = [];
    lines.forEach((line, index) => {
      const match = line.match(/^\d+\.\s*([^:]+):\s*(.*)$/);
      if (match) {
        const stepId = index + 1;
        const key = `${activeIdx}_${stepId}`;
        steps.push({
          id: stepId,
          command: match[1].trim(),
          detail: match[2].trim(),
          status: stepStatuses[key] || "pending",
        });
      }
    });
    return steps;
  }, [activeSections.workflow, stepStatuses, activeIdx]);

  // Parse PA announcement templates dynamically using useMemo
  const announcementTranslations = React.useMemo(() => {
    if (!activeSections.summary) return null;
    const matches: Record<string, string> = {};
    const langs = ["English", "Spanish", "French", "Portuguese", "Arabic"];
    langs.forEach((langName) => {
      const regex = new RegExp(`${langName}:\\s*([^\\n]+)`);
      const match = activeSections.summary.match(regex);
      if (match) {
        matches[langName] = match[1].trim();
      }
    });
    return Object.keys(matches).length > 0 ? matches : null;
  }, [activeSections.summary]);

  const handleWorkflowApprove = async (stepId: number, command: string) => {
    try {
      // Map to critical backend command_type when applicable
      let commandTypeToSubmit = command;
      const cmdLower = command.toLowerCase();
      if (
        cmdLower.includes("gate rate override") ||
        cmdLower.includes("open gate d")
      ) {
        commandTypeToSubmit = CRITICAL_COMMAND_TYPE.gate_rate_override;
      }

      const response = await apiClient.post("/commands", {
        command_type: commandTypeToSubmit,
        payload: { source: "AI_WORKFLOW", step_id: stepId },
      });

      if (response.status === 201 || response.status === 200) {
        const key = `${activeIdx}_${stepId}`;
        setStepStatuses((prev) => ({
          ...prev,
          [key]: "approved",
        }));
        setCommandFeedback({
          text: `Workflow Step ${stepId} "${command}" approved and dispatched successfully!`,
        });
      }
    } catch (err: unknown) {
      const errResponse = err as { response?: { data?: { detail?: string } } };
      const errDetail =
        errResponse.response?.data?.detail ||
        "Operation failed due to RBAC or workflow constraints.";

      setCommandFeedback({
        text: `Workflow Step failed: ${errDetail}`,
        isError: true,
      });
    }
    setTimeout(() => setCommandFeedback(null), 5000);
  };

  const handleWorkflowSkip = (stepId: number) => {
    const key = `${activeIdx}_${stepId}`;
    setStepStatuses((prev) => ({
      ...prev,
      [key]: "skipped",
    }));
  };

  const hasConversation = messages.length > 0;

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-6rem)] gap-4 p-4 text-zinc-100 overflow-hidden">
      {/* Sidebar - Sessions & History */}
      <div className="w-full lg:w-64 flex flex-col gap-3 bg-zinc-950/40 border border-zinc-800/40 rounded-2xl p-4 overflow-y-auto">
        <div className="flex justify-between items-center pb-2 border-b border-zinc-800/60">
          <span className="text-sm font-bold tracking-wide text-zinc-400">
            Sessions
          </span>
          <button
            onClick={() => {
              const newSess = `Session_${sessions.length + 1}`;
              setSessions((prev) => [...prev, newSess]);
              setActiveSession(newSess);
              setMessages([
                {
                  role: "assistant",
                  content:
                    "### Summary\nNew Session Initialized. How can I assist you with stadium operations?",
                },
              ]);
            }}
            className="p-1 rounded bg-indigo-650/20 hover:bg-indigo-600/30 text-indigo-300 transition text-xs"
          >
            New Chat
          </button>
        </div>

        <div className="flex flex-col gap-1">
          {sessions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setActiveSession(s)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition ${
                activeSession === s
                  ? "bg-indigo-600/25 border border-indigo-500/45 text-white font-medium"
                  : "hover:bg-zinc-800/30 text-zinc-400"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              {s.replace("_", " ")}
            </button>
          ))}
        </div>

        {/* Scenario Simulation Engine */}
        <div className="mt-4 pt-4 border-t border-zinc-800/60 flex flex-col gap-2">
          <span className="text-xs font-bold tracking-wide text-zinc-400 uppercase">
            Simulation Engine
          </span>
          <div className="flex flex-col gap-1.5">
            <button
              onClick={() =>
                handleSubmit("Simulate: Kickoff Egress crowd surge at Gate D")
              }
              className="w-full text-left px-3 py-2 rounded-lg bg-zinc-900/60 border border-zinc-800/65 hover:border-indigo-500/50 hover:bg-zinc-800 text-xs text-zinc-300 transition cursor-pointer"
            >
              ⚡ Egress Surge
            </button>
            <button
              onClick={() =>
                handleSubmit("Simulate: Medical emergency in South Stand")
              }
              className="w-full text-left px-3 py-2 rounded-lg bg-zinc-900/60 border border-zinc-800/65 hover:border-indigo-500/50 hover:bg-zinc-800 text-xs text-zinc-300 transition cursor-pointer"
            >
              🚨 Medical Emergency
            </button>
            <button
              onClick={() =>
                handleSubmit("Simulate: Power outage near elevator 2")
              }
              className="w-full text-left px-3 py-2 rounded-lg bg-zinc-900/60 border border-zinc-800/65 hover:border-indigo-500/50 hover:bg-zinc-800 text-xs text-zinc-300 transition cursor-pointer"
            >
              🔌 Power Outage
            </button>
          </div>
        </div>
      </div>

      {/* Main Panel - Conversation Area */}
      <div className="flex-1 flex flex-col bg-zinc-950/40 border border-zinc-800/40 rounded-2xl p-4 overflow-hidden relative">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-zinc-800/60 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <h1 className="text-lg font-bold">AI Stadium Copilot</h1>
          </div>
          <div className="flex items-center gap-4">
            {/* Language Selector */}
            <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1 text-xs">
              <Globe className="h-3.5 w-3.5 text-zinc-400" />
              <select
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="bg-transparent text-zinc-200 outline-none border-none cursor-pointer"
              >
                <option value="en" className="bg-zinc-950">
                  English
                </option>
                <option value="es" className="bg-zinc-950">
                  Español
                </option>
                <option value="fr" className="bg-zinc-950">
                  Français
                </option>
                <option value="pt" className="bg-zinc-950">
                  Português
                </option>
                <option value="ar" className="bg-zinc-950">
                  العربية
                </option>
              </select>
            </div>
            <span className="text-xs px-2 py-1 rounded bg-zinc-800/80 text-zinc-400 border border-zinc-700/40">
              gemini-2.5-flash
            </span>
          </div>
        </div>

        {/* Offline + Command Feedback Indicator */}
        {!wsConnected && (
          <div
            role="status"
            aria-live="polite"
            className="absolute top-16 left-4 right-4 z-10 p-3 rounded-lg border bg-zinc-950/70 border-zinc-800 text-zinc-300 text-sm flex items-center justify-between gap-3"
          >
            <span className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-amber-400" />
              Telemetry offline. Copilot will continue with best-effort mode.
            </span>
          </div>
        )}

        {commandFeedback && (
          <div
            role="status"
            aria-live="polite"
            className={`absolute top-16 left-4 right-4 z-10 p-3 rounded-lg border text-sm flex justify-between items-center ${
              commandFeedback.isError
                ? "bg-red-950/40 border-red-500/40 text-red-300"
                : "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
            }`}
          >
            <span className="flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              {commandFeedback.text}
            </span>
            <button
              type="button"
              onClick={() => setCommandFeedback(null)}
              aria-label="Dismiss feedback"
              className="opacity-60 hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Message Log */}
        <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-4">
          {/* Empty state */}
          {!hasConversation && !loading && (
            <div className="mt-6 p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/40 text-center">
              <div className="text-sm font-bold text-zinc-200 mb-2">
                No conversation yet
              </div>
              <div className="text-xs text-zinc-400">
                Ask Copilot a question to generate stadium operations guidance.
              </div>
            </div>
          )}

          {/* Error state (AI) */}
          {!!error && (
            <div
              role="alert"
              className="mt-2 p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200"
            >
              <div className="text-xs font-bold uppercase tracking-wider mb-2">
                Copilot encountered an error
              </div>
              <div className="text-sm leading-relaxed">{error}</div>
              <div className="mt-3 flex justify-center">
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-700 text-white transition"
                >
                  Retry
                </button>
              </div>
            </div>
          )}
          {messages.map((m, idx) => (
            <ChatMessage
              key={idx}
              message={m}
              onActionExecute={handleActionExecute}
              isActiveResponse={
                selectedMessageIdx === null
                  ? idx === messages.length - 1
                  : selectedMessageIdx === idx
              }
              onSelectMessage={() => setSelectedMessageIdx(idx)}
            />
          ))}

          {/* Rendering the active SSE stream chunk */}
          {/* Loading skeleton / streaming */}
          {loading && !streamText && (
            <div
              role="status"
              aria-live="polite"
              className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/40 self-start max-w-3xl mr-auto"
            >
              <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                Aegis Assistant (Preparing)
              </div>
              <div className="space-y-2">
                <div className="h-3 w-3/4 rounded bg-zinc-800 animate-pulse" />
                <div className="h-3 w-5/6 rounded bg-zinc-800 animate-pulse" />
                <div className="h-3 w-2/3 rounded bg-zinc-800 animate-pulse" />
              </div>
            </div>
          )}

          {loading && streamText && (
            <div
              role="status"
              aria-live="polite"
              className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/40 self-start max-w-3xl mr-auto"
            >
              <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">
                Aegis Assistant (Streaming)
              </div>
              <div className="text-sm text-zinc-100 whitespace-pre-line leading-relaxed">
                {parseMessageSections(streamText).summary || streamText}
              </div>
            </div>
          )}

          {loading && !streamText && <ThinkingIndicator />}

          {/* Suggestion Prompt Cards when conversation is thin */}
          {messages.length === 1 && !loading && (
            <div className="mt-auto">
              <div className="text-sm font-semibold text-zinc-400 mb-2">
                Suggested Prompt Actions
              </div>
              <SuggestionCards onSelectPrompt={handleSelectPrompt} />
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-zinc-800/60 pt-3 mt-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(input);
            }}
            className="flex gap-2 relative"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                loading
                  ? "Generating response..."
                  : "Ask Copilot about Gate bottlenecks, volunteer schedules..."
              }
              disabled={loading}
              aria-label="Copilot input"
              className="flex-1 bg-zinc-900/80 border border-zinc-800 hover:border-zinc-700 focus-visible:border-indigo-500 focus-visible:ring-1 focus-visible:ring-indigo-500 rounded-xl px-4 py-3 text-sm outline-none transition"
            />
            {loading ? (
              <button
                type="button"
                onClick={cancel}
                className="px-4 py-3 bg-red-650/20 hover:bg-red-600/30 text-red-300 rounded-xl text-sm font-medium transition flex items-center gap-1 cursor-pointer"
              >
                Cancel
              </button>
            ) : (
              <button
                type="submit"
                className="px-4 py-3 bg-indigo-650 hover:bg-indigo-650 text-white rounded-xl text-sm font-medium transition flex items-center gap-1 cursor-pointer"
              >
                <Send className="h-4 w-4" />
                Ask
              </button>
            )}
          </form>
        </div>
      </div>

      {/* Right Drawer - Explainability & Telemetry Context */}
      <div className="w-full lg:w-80 flex flex-col gap-4 bg-zinc-950/40 border border-zinc-800/40 rounded-2xl p-4 overflow-y-auto">
        <div className="pb-2 border-b border-zinc-800/60 flex justify-between items-center">
          <span className="text-sm font-bold tracking-wide text-zinc-400">
            Explainability Dashboard
          </span>
          {activeSections.confidence && (
            <ConfidenceBadge confidence={activeSections.confidence} />
          )}
        </div>

        {/* Multi-step Workflow steps panel */}
        {workflowSteps.length > 0 && (
          <div className="p-4 rounded-xl bg-zinc-900/45 border border-zinc-800/60 flex flex-col gap-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1">
              <Play className="h-3 w-3 text-indigo-400" /> AI Workflow Steps
            </h3>
            <div className="flex flex-col gap-3">
              {workflowSteps.map((step) => (
                <div
                  key={step.id}
                  className="p-2.5 rounded bg-zinc-950/40 border border-zinc-800/80 flex flex-col gap-1 text-xs"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-zinc-200">
                      Step {step.id}: {step.command}
                    </span>
                    {step.status === "approved" && (
                      <CheckCircle className="h-4 w-4 text-emerald-400" />
                    )}
                    {step.status === "skipped" && (
                      <SkipForward className="h-4 w-4 text-zinc-500" />
                    )}
                  </div>
                  <p className="text-zinc-400 leading-tight mb-2">
                    {step.detail}
                  </p>
                  {step.status === "pending" && (
                    <div className="flex gap-2">
                      <button
                        onClick={() =>
                          handleWorkflowApprove(step.id, step.command)
                        }
                        className="px-2 py-1 bg-indigo-650 hover:bg-indigo-600 text-white rounded text-[10px] transition"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleWorkflowSkip(step.id)}
                        className="px-2 py-1 bg-zinc-850 hover:bg-zinc-800 text-zinc-400 rounded text-[10px] transition"
                      >
                        Skip
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <ReasoningPanel
          reasoning={activeSections.reasoning}
          risks={activeSections.potentialRisks}
          alternative={activeSections.alternativeActions}
        />

        <SourcePanel sources={activeSections.sources} />

        {/* Dynamic PA Announcement templates copy generator */}
        {announcementTranslations && (
          <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/30 flex flex-col gap-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400">
              PA Announcement Copy
            </h3>
            <div className="flex flex-col gap-2.5 text-xs">
              {Object.entries(announcementTranslations).map(
                ([langName, textValue]) => (
                  <div key={langName} className="flex flex-col gap-1">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-zinc-300">
                        {langName}
                      </span>
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(textValue);
                            setCommandFeedback({
                              text: `Copied ${langName} PA announcement template.`,
                            });
                          } catch {
                            setCommandFeedback({
                              text: "Copy failed. Clipboard permissions may be blocked.",
                              isError: true,
                            });
                          } finally {
                            setTimeout(() => setCommandFeedback(null), 3000);
                          }
                        }}
                        className="text-[10px] text-indigo-400 hover:text-indigo-300 transition cursor-pointer"
                      >
                        Copy
                      </button>
                    </div>
                    <p className="text-[11px] text-zinc-400 italic leading-tight">
                      {textValue}
                    </p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {/* Sustainability Intelligence Resource optimization panel */}
        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50 flex flex-col gap-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
            Sustainability Intel
          </h3>
          <div className="flex flex-col gap-1.5 text-xs text-zinc-300">
            <div className="flex justify-between">
              <span>Lighting Setback:</span>
              <span className="text-emerald-400 font-semibold">
                -15% Halftime
              </span>
            </div>
            <div className="flex justify-between">
              <span>VIP Suite HVAC:</span>
              <span className="text-emerald-400 font-semibold">
                23°C (Halftime)
              </span>
            </div>
            <div className="flex justify-between">
              <span>Est. Energy Saved:</span>
              <span className="text-emerald-400 font-semibold">184 kWh</span>
            </div>
          </div>
        </div>

        {/* Multi-Agent Operations & Mission Control Link */}
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/40 flex flex-col gap-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
            <Brain className="h-3.5 w-3.5" /> Multi-Agent Engine
          </h3>
          <p className="text-[11px] text-zinc-400 leading-snug">
            Autonomous multi-agent planning compiles coordination strategies
            across 10 specialized agent roles.
          </p>
          <div className="grid grid-cols-5 gap-1.5 py-1">
            {["crowd", "transit", "volunteer", "security", "accessibility"].map(
              (role) => (
                <span
                  key={role}
                  title={`${role.toUpperCase()} Agent Active`}
                  className="h-2 w-full rounded bg-emerald-500/80 animate-pulse block"
                ></span>
              ),
            )}
          </div>
          <a
            href="/mission-control"
            className="w-full py-1.5 bg-indigo-650 hover:bg-indigo-600 text-white rounded text-center text-xs font-semibold block transition"
          >
            Launch Mission Control
          </a>
        </div>

        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">
            Related Modules
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <a
              href="/crowd"
              className="p-2 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-center transition flex items-center justify-center gap-1"
            >
              <LayoutDashboard className="h-3 w-3" /> Crowd
            </a>
            <a
              href="/incidents"
              className="p-2 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-center transition flex items-center justify-center gap-1"
            >
              <HelpCircle className="h-3 w-3" /> Incidents
            </a>
            <a
              href="/transit"
              className="p-2 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-center transition flex items-center justify-center gap-1"
            >
              <RefreshCw className="h-3 w-3" /> Transit
            </a>
            <a
              href="/volunteers"
              className="p-2 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-center transition flex items-center justify-center gap-1"
            >
              <FileText className="h-3 w-3" /> Volunteers
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
