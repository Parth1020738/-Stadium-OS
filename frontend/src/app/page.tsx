"use client";

import React from "react";
import { useTelemetryStore } from "@/store/telemetryStore";
import StadiumMap from "@/components/map/StadiumMap";
import SystemHealthPanel from "@/components/dashboard/SystemHealthPanel";
import TimelineWidget from "@/components/dashboard/TimelineWidget";
import { Users, Activity, AlertTriangle } from "lucide-react";

export default function DashboardHome() {
  const { crowdCount, incidents } = useTelemetryStore();

  const activeIncidentsCount = incidents.filter(
    (i) => i.status !== "Closed" && i.status !== "Resolved"
  ).length;

  return (
    <div className="space-y-6">
      {/* Page Title & Status Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">OPERATIONS COMMAND CENTRAL</h1>
          <p className="text-xs text-muted-foreground">
            Aegis Smart Stadium OS — Real-Time Telemetry and Event Control
          </p>
        </div>
        <div className="flex items-center gap-2 bg-card border border-border px-3 py-1.5 rounded-md text-xs">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-semibold text-muted-foreground uppercase">SYSTEM ONLINE</span>
        </div>
      </div>

      {/* Overview Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Estimated Crowd size */}
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Estimated Crowd Size
            </span>
            <span className="text-2xl font-black block">{crowdCount.toLocaleString()}</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Ingestion In-Progress
            </span>
          </div>
          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            <Users size={20} />
          </div>
        </div>

        {/* System telemetry status */}
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Event Telemetry Influx
            </span>
            <span className="text-2xl font-black block">99.98%</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Average latency: 42ms
            </span>
          </div>
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <Activity size={20} />
          </div>
        </div>

        {/* Active security incidents */}
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between hover:border-primary/40 transition-all">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Active Incidents
            </span>
            <span className="text-2xl font-black block">{activeIncidentsCount}</span>
            <span className="text-[9px] text-yellow-500 font-bold block uppercase">
              Dispatched & Pending
            </span>
          </div>
          <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center text-yellow-500">
            <AlertTriangle size={20} />
          </div>
        </div>
      </div>

      {/* Main Interactive Ingest Dashboard layout grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column: Interactive Map */}
        <div className="xl:col-span-2">
          <StadiumMap />
        </div>

        {/* Right Column: Infrastructure Health + Ingest Timeline */}
        <div className="flex flex-col gap-6">
          <SystemHealthPanel />
          <TimelineWidget />
        </div>
      </div>
    </div>
  );
}
