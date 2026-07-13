"use client";

import React from "react";
import { useAuthStore } from "@/store/authStore";
import { Shield, Mail, Key, User, Clock, Terminal } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();

  if (!user) {
    return (
      <div className="p-6">
        <p className="text-sm text-muted-foreground">No active operator profile loaded.</p>
      </div>
    );
  }

  // Derived mock last login from session storage or default it
  const lastLogin = "2026-07-13 09:23 AM";

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">OPERATOR PROFILE & SETTINGS</h1>
        <p className="text-xs text-muted-foreground">
          View your smart stadium security credentials, access roles, and permissions.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Card info */}
        <div className="md:col-span-1 bg-card border border-border p-6 rounded-lg text-center space-y-4">
          <div className="mx-auto h-20 w-20 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-2xl font-bold font-mono">
            {user.email.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h2 className="text-md font-bold">Operator Profile</h2>
            <p className="text-xs text-muted-foreground mt-1">{user.email}</p>
          </div>
          <div className="flex justify-center gap-1.5 flex-wrap">
            {user.roles.map((role) => (
              <span
                key={role}
                className="px-2 py-0.5 text-[10px] font-semibold bg-primary/10 text-primary border border-primary/20 rounded"
              >
                {role}
              </span>
            ))}
          </div>
        </div>

        {/* Credentials & Details list */}
        <div className="md:col-span-2 bg-card border border-border p-6 rounded-lg space-y-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider border-b border-border pb-2 text-muted-foreground flex items-center gap-2">
            <Shield size={16} /> Operator Access Credentials
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <span className="text-muted-foreground block">Email Address</span>
              <div className="flex items-center gap-2 bg-background border border-border px-3 py-2 rounded">
                <Mail size={12} className="text-muted-foreground" />
                <span>{user.email}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-muted-foreground block">Authentication ID</span>
              <div className="flex items-center gap-2 bg-background border border-border px-3 py-2 rounded">
                <User size={12} className="text-muted-foreground" />
                <span className="font-mono">{user.id}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-muted-foreground block">Last Login Ingestion</span>
              <div className="flex items-center gap-2 bg-background border border-border px-3 py-2 rounded">
                <Clock size={12} className="text-muted-foreground" />
                <span>{lastLogin}</span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-muted-foreground block">Session Security Status</span>
              <div className="flex items-center gap-2 bg-background border border-border px-3 py-2 rounded">
                <Key size={12} className="text-emerald-500" />
                <span className="text-emerald-500 font-semibold">Active JWT Session</span>
              </div>
            </div>
          </div>

          {/* List of Permissions derived from RBAC */}
          <div className="space-y-2.5 pt-4 border-t border-border">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Terminal size={14} /> Active Ingestion Scope Permissions ({user.scopes.length})
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {user.scopes.map((scope) => (
                <div
                  key={scope}
                  className="px-2 py-1.5 bg-background border border-border rounded text-[10px] font-mono text-primary flex items-center gap-1.5"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse"></span>
                  <span>{scope}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
