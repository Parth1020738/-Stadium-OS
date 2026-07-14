"use client";

import React, { useState } from "react";
import { FileBarChart2, Download, CheckCircle, TrendingUp, AlertTriangle, Users } from "lucide-react";

export default function ReportsPage() {
  const [isExporting, setIsExporting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleExport = (type: string) => {
    setIsExporting(true);
    setSuccessMsg(null);
    setTimeout(() => {
      setIsExporting(false);
      setSuccessMsg(`Successfully generated and downloaded Aegis Smart Stadium OS ${type} Report.`);
    }, 1200);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight uppercase flex items-center gap-2">
          <FileBarChart2 className="text-primary" size={24} /> Incident & Operations Reports
        </h1>
        <p className="text-xs text-muted-foreground mt-1">
          Export analytical summaries of crowd flows, security incidents, transit metrics, and accessibility requests.
        </p>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-500 text-xs flex items-center gap-2 animate-fadeIn">
          <CheckCircle size={14} className="flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Grid Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-lg space-y-2">
          <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Crowd Throughput</span>
          <div className="flex justify-between items-baseline">
            <span className="text-xl font-bold font-mono">48,291</span>
            <span className="text-[10px] text-emerald-500 flex items-center font-bold">
              <TrendingUp size={10} className="mr-0.5" /> +12.4%
            </span>
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg space-y-2">
          <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Active Incidents</span>
          <div className="flex justify-between items-baseline">
            <span className="text-xl font-bold font-mono">2</span>
            <span className="text-[10px] text-amber-500 flex items-center font-bold">
              <AlertTriangle size={10} className="mr-0.5" /> Resolving
            </span>
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg space-y-2">
          <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Assisted Mobility Requests</span>
          <div className="flex justify-between items-baseline">
            <span className="text-xl font-bold font-mono">148</span>
            <span className="text-[10px] text-muted-foreground flex items-center font-bold">
              <Users size={10} className="mr-0.5" /> Completed
            </span>
          </div>
        </div>
      </div>

      {/* Report Types List */}
      <div className="bg-card border border-border rounded-lg p-6 space-y-4">
        <h2 className="text-xs uppercase font-bold tracking-wider border-b border-border pb-2 text-muted-foreground">
          Available Export Options
        </h2>

        <div className="divide-y divide-border/60">
          <div className="py-4 flex justify-between items-center gap-4">
            <div>
              <h3 className="text-xs font-bold">Crowd Flow & Congestion Heatmap Report</h3>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                Comprehensive dataset containing gate counts, zone densities, and bottleneck analytics for the current match.
              </p>
            </div>
            <button
              onClick={() => handleExport("Crowd Ingestion")}
              disabled={isExporting}
              className="bg-primary hover:bg-primary/95 text-primary-foreground font-semibold px-3 py-1.5 rounded text-[10px] flex items-center gap-1.5 transition-all flex-shrink-0"
            >
              <Download size={12} /> Export CSV
            </button>
          </div>

          <div className="py-4 flex justify-between items-center gap-4">
            <div>
              <h3 className="text-xs font-bold">Incident Log & Audit History</h3>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                Chronological ledger of security reports, resolution logs, steward dispatch timestamps, and AI alerts.
              </p>
            </div>
            <button
              onClick={() => handleExport("Incident Audit")}
              disabled={isExporting}
              className="bg-primary hover:bg-primary/95 text-primary-foreground font-semibold px-3 py-1.5 rounded text-[10px] flex items-center gap-1.5 transition-all flex-shrink-0"
            >
              <Download size={12} /> Export PDF
            </button>
          </div>

          <div className="py-4 flex justify-between items-center gap-4">
            <div>
              <h3 className="text-xs font-bold">Accessibility Services Performance</h3>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                Summary of special requests, average volunteer response times, and general accessibility utilization stats.
              </p>
            </div>
            <button
              onClick={() => handleExport("Accessibility Performance")}
              disabled={isExporting}
              className="bg-primary hover:bg-primary/95 text-primary-foreground font-semibold px-3 py-1.5 rounded text-[10px] flex items-center gap-1.5 transition-all flex-shrink-0"
            >
              <Download size={12} /> Export CSV
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
