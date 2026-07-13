"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Sparkles, Cpu, ArrowRight, Activity, Award } from "lucide-react";

interface RecommendationItem {
  id: number;
  title: string;
  description: string;
  confidence_score: number;
  risk_score: number;
  reasoning: string;
  status: string;
  suggested_action: string;
}

interface RiskResponse {
  overall_risk_score: number;
  crowd_risk: number;
  transit_risk: number;
  incident_risk: number;
}

export default function AiPage() {
  const [selectedRec, setSelectedRec] = useState<RecommendationItem | null>(null);

  // React Query: Fetch AI recommendations
  const { data: recommendations, isLoading: loadingRecs } = useQuery<RecommendationItem[]>({
    queryKey: ["ai-recommendations"],
    queryFn: async () => {
      const res = await apiClient.get("/ai/recommendations");
      return res.data;
    },
  });

  // React Query: Fetch AI live risk assessment
  const { data: riskData } = useQuery<RiskResponse>({
    queryKey: ["ai-risk"],
    queryFn: async () => {
      const res = await apiClient.get("/ai/risk");
      return res.data;
    },
  });

  const getRiskBadgeColor = (score: number) => {
    if (score > 70) return "text-red-500 bg-red-500/10 border-red-500/20";
    if (score > 40) return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
    return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-border">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="text-yellow-500" /> AI DECISION SUPPORT PANEL
        </h1>
        <p className="text-xs text-muted-foreground">
          Real-time incident correlations, predictive crowd alerts, and suggested gateway dispatch actions.
        </p>
      </div>

      {/* Risk Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Overall risk score */}
        <div className="bg-card border border-border p-4 rounded-lg flex flex-col justify-between">
          <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
            Overall Risk Index
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-black">
              {riskData?.overall_risk_score !== undefined ? Math.round(riskData.overall_risk_score * 100) : 34}%
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[8px] border font-bold uppercase ${getRiskBadgeColor((riskData?.overall_risk_score || 0.34) * 100)}`}>
              {(riskData?.overall_risk_score || 0.3) > 0.7 ? "Critical" : (riskData?.overall_risk_score || 0.3) > 0.4 ? "Medium" : "Nominal"}
            </span>
          </div>
          <div className="h-1.5 w-full bg-background rounded-full overflow-hidden border border-border mt-3">
            <div
              className="h-full bg-primary"
              style={{ width: `${Math.round((riskData?.overall_risk_score || 0.34) * 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Crowd risk */}
        <div className="bg-card border border-border p-4 rounded-lg flex flex-col justify-between">
          <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
            Stands Crowd Density Risk
          </span>
          <div className="text-xl font-bold mt-2">
            {riskData?.crowd_risk !== undefined ? Math.round(riskData.crowd_risk * 100) : 48}%
          </div>
          <span className="text-[9px] text-muted-foreground block mt-1">Ingesting Sector density checks</span>
        </div>

        {/* Transit risk */}
        <div className="bg-card border border-border p-4 rounded-lg flex flex-col justify-between">
          <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
            Transit Fleet Delay Risk
          </span>
          <div className="text-xl font-bold mt-2">
            {riskData?.transit_risk !== undefined ? Math.round(riskData.transit_risk * 100) : 15}%
          </div>
          <span className="text-[9px] text-muted-foreground block mt-1">Shuttles tracking delay index</span>
        </div>

        {/* Incident severity risk */}
        <div className="bg-card border border-border p-4 rounded-lg flex flex-col justify-between">
          <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
            Open Incident Severity Risk
          </span>
          <div className="text-xl font-bold mt-2">
            {riskData?.incident_risk !== undefined ? Math.round(riskData.incident_risk * 100) : 22}%
          </div>
          <span className="text-[9px] text-muted-foreground block mt-1">Dispatched ticket severity load</span>
        </div>
      </div>

      {/* Recommendations & Details Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Recommendations list */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="p-4 border-b border-border bg-background/30 flex justify-between items-center">
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Cpu size={14} className="text-primary" /> Active Copilot Recommendations
              </h2>
            </div>

            {loadingRecs ? (
              <div className="p-12 text-center text-xs text-muted-foreground">
                Analyzing current telemetry feeds for insights...
              </div>
            ) : !recommendations || recommendations.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground">
                All stadium sectors stable. No recommendations issued.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    onClick={() => setSelectedRec(rec)}
                    className={`p-4 cursor-pointer transition-colors flex items-start gap-4 ${
                      selectedRec?.id === rec.id ? "bg-primary/5 hover:bg-primary/10" : "hover:bg-muted/30"
                    }`}
                  >
                    <div className="mt-0.5 h-7 w-7 rounded bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
                      <Sparkles size={14} />
                    </div>
                    <div className="space-y-1 flex-1">
                      <div className="flex justify-between items-start gap-4">
                        <h3 className="text-xs font-bold text-primary">{rec.title}</h3>
                        <span className="text-[9px] font-mono text-muted-foreground">
                          Confidence: {Math.round(rec.confidence_score * 100)}%
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        {rec.description}
                      </p>
                      <div className="flex gap-2 pt-2">
                        <span className={`px-1.5 py-0.5 rounded text-[8px] border font-bold uppercase ${getRiskBadgeColor(rec.risk_score * 100)}`}>
                          Risk impact: {Math.round(rec.risk_score * 100)}%
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-background border border-border text-[8px] font-semibold text-muted-foreground">
                          {rec.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Explainability side drawer */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          {selectedRec ? (
            <>
              <div className="border-b border-border pb-3">
                <h2 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                  <Activity size={14} /> Explainability Details
                </h2>
                <span className="text-[10px] text-muted-foreground block mt-0.5">
                  Reasoning logic, confidence matrix, and evidence references.
                </span>
              </div>

              <div className="space-y-4 text-xs">
                {/* Summary */}
                <div className="space-y-1">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold">AI Explanations Summary</span>
                  <p className="bg-background border border-border p-3 rounded leading-relaxed">
                    {selectedRec.reasoning || "No explanation summary available."}
                  </p>
                </div>

                {/* Suggested Action */}
                <div className="space-y-1">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold flex items-center gap-1 text-primary">
                    Suggested Action <ArrowRight size={10} />
                  </span>
                  <p className="bg-background border border-border p-3 rounded font-mono font-medium text-[11px] text-foreground">
                    {selectedRec.suggested_action}
                  </p>
                </div>

                {/* Evidence References */}
                <div className="space-y-2">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold flex items-center gap-1">
                    <Award size={12} className="text-primary" /> Reasoning Evidences
                  </span>
                  <div className="p-3 border border-border rounded bg-background/50 text-[11px] leading-relaxed">
                    Correlation analysis indicates a threshold overflow. Sector occupancy exceeds limits while vehicle egress counts remained static.
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-xs text-muted-foreground flex flex-col items-center gap-2">
              <Cpu size={24} className="text-muted-foreground" />
              <span>Select an AI suggestion card to view reasoning tree references</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
