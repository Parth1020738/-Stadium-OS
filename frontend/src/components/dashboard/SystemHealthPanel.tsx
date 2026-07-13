"use client";

import React from "react";
import { useTelemetryStore } from "@/store/telemetryStore";
import { Server, Database, Radio, Cpu, HardDrive, ShieldCheck } from "lucide-react";

export default function SystemHealthPanel() {
  const { metrics, wsConnected } = useTelemetryStore();

  const getStatusColor = (status: "Healthy" | "Degraded" | "Down") => {
    switch (status) {
      case "Healthy":
        return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
      case "Degraded":
        return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      case "Down":
        return "text-red-500 bg-red-500/10 border-red-500/20";
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Server size={14} className="text-primary" /> SYSTEM INFRASTRUCTURE STATUS
        </h2>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-[10px] font-bold">
          <ShieldCheck size={10} /> NOMINAL
        </div>
      </div>

      {/* Services status row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Postgres DB */}
        <div className="border border-border p-4 rounded-lg bg-background flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Postgres DB</span>
            <Database size={14} className="text-primary" />
          </div>
          <div>
            <div className="text-lg font-bold">Connected</div>
            <span className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase tracking-wider ${getStatusColor(metrics.db_status)}`}>
              {metrics.db_status}
            </span>
          </div>
        </div>

        {/* Redis Cache */}
        <div className="border border-border p-4 rounded-lg bg-background flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Redis Cache</span>
            <HardDrive size={14} className="text-primary" />
          </div>
          <div>
            <div className="text-lg font-bold">Connected</div>
            <span className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase tracking-wider ${getStatusColor(metrics.redis_status)}`}>
              {metrics.redis_status}
            </span>
          </div>
        </div>

        {/* Kafka Ingestion Bus */}
        <div className="border border-border p-4 rounded-lg bg-background flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Kafka Broker</span>
            <Radio size={14} className="text-primary" />
          </div>
          <div>
            <div className="text-lg font-bold">Active</div>
            <span className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase tracking-wider ${getStatusColor(metrics.kafka_status)}`}>
              {metrics.kafka_status}
            </span>
          </div>
        </div>
      </div>

      {/* Hardware Utilization Bars */}
      <div className="space-y-4 pt-4 border-t border-border">
        {/* CPU */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-1.5"><Cpu size={12} className="text-primary" /> Processor Utilization (CPU)</span>
            <span>{metrics.cpu_usage}%</span>
          </div>
          <div className="h-2 w-full bg-background rounded-full overflow-hidden border border-border">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${metrics.cpu_usage}%` }}
            ></div>
          </div>
        </div>

        {/* RAM */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-1.5"><HardDrive size={12} className="text-primary" /> Memory Allocated (RAM)</span>
            <span>{metrics.memory_usage}%</span>
          </div>
          <div className="h-2 w-full bg-background rounded-full overflow-hidden border border-border">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${metrics.memory_usage}%` }}
            ></div>
          </div>
        </div>

        {/* WebSocket health indicator */}
        <div className="flex justify-between text-[10px] text-muted-foreground pt-2">
          <span>Active Ingestion Streams: {metrics.active_connections} feeds</span>
          <span>Gateway: {wsConnected ? "WebSocket Connected" : "Polling Mode"}</span>
        </div>
      </div>
    </div>
  );
}
