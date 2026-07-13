"use client";

import React, { useEffect, useState } from "react";
import { useUiStore } from "@/store/uiStore";
import { useTelemetryStore } from "@/store/telemetryStore";
import { useAuthStore } from "@/store/authStore";
import { Search, Bell, Sparkles, LogOut, Clock } from "lucide-react";

export default function Topbar() {
  const { activeEventName } = useUiStore();
  const { wsConnected } = useTelemetryStore();
  const { user, logout } = useAuthStore();
  const [sessionSecs, setSessionSecs] = useState(0);

  // Simple timer tracking active session duration
  useEffect(() => {
    const interval = setInterval(() => {
      setSessionSecs((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatSessionTime = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins}m ${secs}s`;
  };

  const getAvatarInitials = (email?: string) => {
    if (!email) return "OP";
    return email.slice(0, 2).toUpperCase();
  };

  return (
    <header className="fixed top-0 right-0 z-30 h-16 border-b border-border bg-card/85 backdrop-blur-md flex items-center justify-between px-6 transition-all duration-300 left-16 md:left-64">
      {/* Search Input Box */}
      <div className="relative w-64 max-w-xs hidden sm:block">
        <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
          <Search size={16} />
        </span>
        <input
          type="text"
          placeholder="Global operational search..."
          className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-primary text-foreground placeholder-muted-foreground"
        />
      </div>

      {/* Top Bar Actions & Status Widgets */}
      <div className="flex items-center gap-4 ml-auto">
        {/* Active Event Context */}
        <div className="text-right hidden md:block">
          <span className="text-[10px] text-muted-foreground block uppercase tracking-widest">
            Current Event
          </span>
          <span className="text-xs font-semibold text-primary">
            {activeEventName}
          </span>
        </div>

        <div className="h-8 w-px bg-border hidden md:block"></div>

        {/* Inactivity Session Timer */}
        <div className="flex items-center gap-1.5 bg-background border border-border px-2 py-1 rounded text-xs text-muted-foreground">
          <Clock size={12} className="text-primary" />
          <span className="text-[9px] font-mono tracking-wider">
            SESSION: {formatSessionTime(sessionSecs)}
          </span>
        </div>

        {/* Live WebSocket Status Pulse Badge */}
        <div
          className={`flex items-center gap-1.5 border px-2.5 py-1 rounded text-xs font-semibold ${
            wsConnected
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500"
              : "bg-red-500/10 border-red-500/30 text-red-500"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              wsConnected ? "bg-emerald-500 animate-ping" : "bg-red-500"
            }`}
          ></span>
          <span className="text-[10px] tracking-wider uppercase">
            {wsConnected ? "WS: OK" : "WS: DOWN"}
          </span>
        </div>

        {/* Floating AI recommendations alert */}
        <button className="relative p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground">
          <Sparkles size={16} className="text-yellow-500 animate-pulse" />
        </button>

        {/* Bell Alerts Dropdown Trigger */}
        <button className="relative p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500"></span>
        </button>

        {/* User Session Profile details */}
        {user && (
          <div className="flex items-center gap-3 pl-2 border-l border-border">
            <div className="flex flex-col text-right hidden sm:flex">
              <span className="text-xs font-semibold text-foreground truncate max-w-[120px]">
                {user.email}
              </span>
              <span className="text-[9px] text-primary font-bold uppercase tracking-wider">
                {user.roles[0] || "Steward"}
              </span>
            </div>
            {/* User Initial Avatar */}
            <div className="h-8 w-8 rounded-full bg-primary/20 text-primary border border-primary/30 flex items-center justify-center text-xs font-bold font-mono">
              {getAvatarInitials(user.email)}
            </div>
            {/* Logout Trigger */}
            <button
              onClick={() => logout()}
              title="Logout session"
              className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
