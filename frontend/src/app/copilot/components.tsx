"use client";

import React from "react";
import { ChatMessage as ChatMessageType } from "../../lib/ai-client";

export interface ParsedSections {
  summary: string;
  reasoning: string;
  confidence: string;
  sources: string;
  recommendedActions: string;
  alternativeActions: string;
  potentialRisks: string;
  workflow: string;
}

export function parseMessageSections(text: string): ParsedSections {
  const sections: ParsedSections = {
    summary: "",
    reasoning: "",
    confidence: "",
    sources: "",
    recommendedActions: "",
    alternativeActions: "",
    potentialRisks: "",
    workflow: "",
  };

  const summaryMatch = text.match(/### Summary\n([\s\S]*?)(?=\n\n###|$)/);
  const reasoningMatch = text.match(/### Reasoning\n([\s\S]*?)(?=\n\n###|$)/);
  const confidenceMatch = text.match(/### Confidence\n([\s\S]*?)(?=\n\n###|$)/);
  const sourcesMatch = text.match(/### Data Sources\n([\s\S]*?)(?=\n\n###|$)/);
  const recommendedMatch = text.match(/### Recommended Actions\n([\s\S]*?)(?=\n\n###|$)/);
  const alternativeMatch = text.match(/### Alternative Actions\n([\s\S]*?)(?=\n\n###|$)/);
  const risksMatch = text.match(/### Potential Risks\n([\s\S]*?)(?=\n\n###|$)/);
  const workflowMatch = text.match(/### Workflow\n([\s\S]*?)(?=\n\n###|$)/);

  sections.summary = summaryMatch ? summaryMatch[1].trim() : "";
  sections.reasoning = reasoningMatch ? reasoningMatch[1].trim() : "";
  sections.confidence = confidenceMatch ? confidenceMatch[1].trim() : "";
  sections.sources = sourcesMatch ? sourcesMatch[1].trim() : "";
  sections.recommendedActions = recommendedMatch ? recommendedMatch[1].trim() : "";
  sections.alternativeActions = alternativeMatch ? alternativeMatch[1].trim() : "";
  sections.potentialRisks = risksMatch ? risksMatch[1].trim() : "";
  sections.workflow = workflowMatch ? workflowMatch[1].trim() : "";

  // If no structured headers matched, treat the whole text as summary
  if (!summaryMatch && !reasoningMatch && !confidenceMatch && !recommendedMatch) {
    sections.summary = text;
  }

  return sections;
}

export function ConfidenceBadge({ confidence }: { confidence: string }) {
  if (!confidence) return null;
  const num = parseFloat(confidence);
  const isHigh = num >= 0.9;
  const isMedium = num >= 0.7 && num < 0.9;

  let bgClass = "bg-red-500/20 text-red-300 border-red-500/30";
  if (isHigh) bgClass = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
  else if (isMedium) bgClass = "bg-amber-500/20 text-amber-300 border-amber-500/30";

  return (
    <div className={`px-2 py-0.5 rounded border text-xs font-semibold ${bgClass}`}>
      Confidence: {(num * 100).toFixed(0)}%
    </div>
  );
}

export function ActionCards({
  recommendedText,
  onActionExecute,
}: {
  recommendedText: string;
  onActionExecute: (command: string, actionType: string) => void;
}) {
  const textLower = recommendedText.toLowerCase();

  if (textLower.includes("open gate d") || textLower.includes("gate d")) {
    return (
      <div className="mt-3 p-3 rounded-lg bg-zinc-800/80 border border-zinc-700/50 flex flex-col gap-2">
        <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Recommended Action: Open Gate D</div>
        <div className="flex gap-2">
          <button
            onClick={() => onActionExecute("Open Gate D", "execute")}
            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm transition"
          >
            Execute
          </button>
          <button
            onClick={() => onActionExecute("Open Gate D", "ignore")}
            className="px-3 py-1 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 rounded text-sm transition"
          >
            Ignore
          </button>
          <button
            onClick={() => onActionExecute("Open Gate D", "explain")}
            className="px-3 py-1 border border-zinc-600 text-zinc-300 hover:bg-zinc-700 rounded text-sm transition"
          >
            Explain
          </button>
        </div>
      </div>
    );
  }

  if (textLower.includes("dispatch volunteers") || textLower.includes("steward")) {
    return (
      <div className="mt-3 p-3 rounded-lg bg-zinc-800/80 border border-zinc-700/50 flex flex-col gap-2">
        <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Recommended Action: Dispatch Volunteers</div>
        <div className="flex gap-2">
          <button
            onClick={() => onActionExecute("Dispatch Volunteers", "assign")}
            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-sm transition"
          >
            Assign
          </button>
          <button
            onClick={() => onActionExecute("Dispatch Volunteers", "modify")}
            className="px-3 py-1 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 rounded text-sm transition"
          >
            Modify
          </button>
          <button
            onClick={() => onActionExecute("Dispatch Volunteers", "cancel")}
            className="px-3 py-1 border border-red-500/30 text-red-300 hover:bg-red-500/10 rounded text-sm transition"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (textLower.includes("delay shuttle") || textLower.includes("shuttle")) {
    return (
      <div className="mt-3 p-3 rounded-lg bg-zinc-800/80 border border-zinc-700/50 flex flex-col gap-2">
        <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Recommended Action: Delay Shuttle</div>
        <div className="flex gap-2">
          <button
            onClick={() => onActionExecute("Delay Shuttle", "approve")}
            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm transition"
          >
            Approve
          </button>
          <button
            onClick={() => onActionExecute("Delay Shuttle", "reject")}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition"
          >
            Reject
          </button>
          <button
            onClick={() => onActionExecute("Delay Shuttle", "view_route")}
            className="px-3 py-1 border border-zinc-600 text-zinc-300 hover:bg-zinc-700 rounded text-sm transition"
          >
            View Route
          </button>
        </div>
      </div>
    );
  }

  return null;
}

export function SuggestionCards({
  onSelectPrompt,
}: {
  onSelectPrompt: (prompt: string) => void;
}) {
  const prompts = [
    "Why is Gate A crowded?",
    "Summarize active incidents.",
    "Show volunteer shortages.",
    "Recommend transport improvements.",
    "Accessibility issues near Gate C.",
    "Generate executive briefing.",
    "Create today's operations summary.",
    "Recommend command actions.",
    "Explain today's AI alerts.",
    "Predict next congestion.",
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
      {prompts.map((p, idx) => (
        <button
          key={idx}
          onClick={() => onSelectPrompt(p)}
          className="text-left p-3 rounded-lg bg-zinc-800/50 border border-zinc-700/40 hover:border-indigo-500/50 hover:bg-zinc-850 text-sm text-zinc-200 hover:text-white transition cursor-pointer"
        >
          {p}
        </button>
      ))}
    </div>
  );
}

export function ChatMessage({
  message,
  onActionExecute,
  isActiveResponse,
  onSelectMessage,
}: {
  message: ChatMessageType;
  onActionExecute: (command: string, actionType: string) => void;
  isActiveResponse?: boolean;
  onSelectMessage?: () => void;
}) {
  const isUser = message.role === "user";
  const parsed = parseMessageSections(message.content);

  return (
    <div
      onClick={onSelectMessage}
      className={`flex flex-col gap-1 p-4 rounded-xl transition cursor-pointer ${
        isUser
          ? "bg-indigo-950/40 border border-indigo-900/30 self-end max-w-2xl ml-auto"
          : "bg-zinc-900/60 border border-zinc-800/40 self-start max-w-3xl mr-auto " +
            (isActiveResponse ? "ring-1 ring-indigo-500/40" : "")
      }`}
    >
      <div className="flex justify-between items-center gap-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          {isUser ? "Operator" : "Aegis Assistant"}
        </span>
        {!isUser && parsed.confidence && (
          <ConfidenceBadge confidence={parsed.confidence} />
        )}
      </div>

      <div className="text-sm text-zinc-100 mt-1 whitespace-pre-line leading-relaxed">
        {parsed.summary}
      </div>

      {!isUser && parsed.recommendedActions && (
        <ActionCards
          recommendedText={parsed.recommendedActions}
          onActionExecute={onActionExecute}
        />
      )}
    </div>
  );
}

export function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-2 p-4 rounded-xl bg-zinc-900/40 border border-zinc-850 self-start mr-auto">
      <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Aegis is analyzing</span>
      <div className="flex gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce"></span>
        <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce [animation-delay:0.2s]"></span>
        <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce [animation-delay:0.4s]"></span>
      </div>
    </div>
  );
}

export function SourcePanel({ sources }: { sources: string }) {
  return (
    <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
      <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">Sources</h3>
      {sources ? (
        <p className="text-sm text-zinc-300 leading-relaxed">{sources}</p>
      ) : (
        <p className="text-xs text-zinc-500 italic">No telemetry data sources queried for this task.</p>
      )}
    </div>
  );
}

export function ReasoningPanel({
  reasoning,
  risks,
  alternative,
}: {
  reasoning: string;
  risks: string;
  alternative: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">AI Reasoning Steps</h3>
        {reasoning ? (
          <p className="text-sm text-zinc-300 leading-relaxed">{reasoning}</p>
        ) : (
          <p className="text-xs text-zinc-500 italic">No reasoning step log emitted yet.</p>
        )}
      </div>

      <div className="p-4 rounded-xl bg-red-950/20 border border-red-900/30">
        <h3 className="text-xs font-bold uppercase tracking-wider text-red-300 mb-2">Potential Risks</h3>
        {risks ? (
          <p className="text-sm text-zinc-300 leading-relaxed">{risks}</p>
        ) : (
          <p className="text-xs text-zinc-500 italic">No structural risks identified.</p>
        )}
      </div>

      <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">Alternative Courses</h3>
        {alternative ? (
          <p className="text-sm text-zinc-300 leading-relaxed">{alternative}</p>
        ) : (
          <p className="text-xs text-zinc-500 italic">No fallback recommendations identified.</p>
        )}
      </div>
    </div>
  );
}
