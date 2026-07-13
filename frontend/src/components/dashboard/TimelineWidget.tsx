"use client";

import React from "react";
import { useTelemetryStore } from "@/store/telemetryStore";
import { AlertCircle, Clock, CheckCircle, Flame } from "lucide-react";

export default function TimelineWidget() {
  const { alerts, incidents } = useTelemetryStore();

  const getSeverityColor = (severity: "Low" | "Medium" | "High" | "Critical") => {
    switch (severity) {
      case "Critical":
        return "text-red-500 border-red-500/20 bg-red-500/5";
      case "High":
        return "text-orange-500 border-orange-500/20 bg-orange-500/5";
      case "Medium":
        return "text-amber-500 border-amber-500/20 bg-amber-500/5";
      case "Low":
        return "text-primary border-primary/20 bg-primary/5";
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
          <Clock size={14} className="text-primary" /> REAL-TIME INCIDENT TICKER
        </h2>
        <span className="text-[10px] text-muted-foreground">Ingesting live feeds</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[360px]">
        {/* Render live WebSocket alerts if available */}
        {alerts.length > 0 ? (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 border rounded-lg transition-colors flex items-start gap-3 ${getSeverityColor(
                alert.severity
              )}`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {alert.severity === "Critical" ? (
                  <Flame size={14} className="text-red-500 animate-bounce" />
                ) : (
                  <AlertCircle size={14} />
                )}
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-[9px] font-bold uppercase tracking-wider">
                    {alert.severity} ALERT
                  </span>
                  <span className="text-[9px] text-muted-foreground font-mono">
                    {alert.timestamp}
                  </span>
                </div>
                <h3 className="text-xs font-semibold">{alert.title}</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  {alert.message}
                </p>
              </div>
            </div>
          ))
        ) : (
          // Display active incidents list if WebSocket telemetry alerts list is empty
          incidents.map((inc) => (
            <div
              key={inc.incident_id}
              className={`p-3 border border-border rounded-lg bg-background/50 hover:bg-background transition-colors flex items-start gap-3`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {inc.status === "Resolved" ? (
                  <CheckCircle size={14} className="text-emerald-500" />
                ) : (
                  <AlertCircle
                    size={14}
                    className={inc.severity === "High" || inc.severity === "Critical" ? "text-red-500" : "text-yellow-500"}
                  />
                )}
              </div>
              <div className="space-y-0.5 flex-1">
                <div className="flex items-center justify-between gap-4">
                  <span
                    className={`text-[9px] font-bold uppercase tracking-wider ${
                      inc.severity === "High" || inc.severity === "Critical" ? "text-red-500" : "text-yellow-500"
                    }`}
                  >
                    {inc.severity} Severity
                  </span>
                  <span className="text-[9px] text-muted-foreground font-mono">
                    {inc.created_at}
                  </span>
                </div>
                <h3 className="text-xs font-semibold">{inc.title}</h3>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                  <span>Zone: {inc.location_zone}</span>
                  <span className="font-semibold">{inc.status}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
