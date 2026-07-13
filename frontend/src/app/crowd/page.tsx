"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useTelemetryStore } from "@/store/telemetryStore";
import { Users, Filter, Search, ShieldAlert, TrendingUp } from "lucide-react";

interface ZoneResponse {
  id: number;
  name: string;
  description: string;
}

export default function CrowdPage() {
  const [search, setSearch] = useState("");
  const { zones } = useTelemetryStore();

  // Fetch zones list from FastAPI DB using React Query
  const { data: dbZones, isLoading, error } = useQuery<ZoneResponse[]>({
    queryKey: ["crowd-zones"],
    queryFn: async () => {
      const res = await apiClient.get("/zones/");
      return res.data;
    },
  });

  const getDensityColor = (density: number) => {
    if (density > 0.8) return "text-red-500 bg-red-500/10 border-red-500/20";
    if (density > 0.5) return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
    return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
  };

  // Combine database definitions with active WebSocket telemetry state
  const mergedZones = (dbZones || []).map((dbz) => {
    const live = zones.find((z) => z.zone_id === dbz.id);
    return {
      id: dbz.id,
      name: dbz.name,
      description: dbz.description,
      estimated_count: live?.estimated_count || 0,
      density_level: live?.density_level || 0.1,
    };
  });

  const filteredZones = mergedZones.filter(
    (z) =>
      z.name.toLowerCase().includes(search.toLowerCase()) ||
      z.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">CROWD MANAGEMENT WORKSPACE</h1>
        <p className="text-xs text-muted-foreground">
          Monitor stadium stands density, occupancy metrics, and pedestrian safety levels.
        </p>
      </div>

      {/* KPI occupancy card row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Total Ingress Inflow
            </span>
            <span className="text-2xl font-black block">19,842</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Gate check nominal
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center text-primary">
            <Users size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Peak Stands Occupancy
            </span>
            <span className="text-2xl font-black block">95%</span>
            <span className="text-[9px] text-red-500 font-bold block uppercase">
              South Stand (Zone C) critical
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-red-500/10 flex items-center justify-center text-red-500">
            <ShieldAlert size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Flow Rate Trend
            </span>
            <span className="text-2xl font-black block">+12.4%</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Average 140 entries/min
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <TrendingUp size={20} />
          </div>
        </div>
      </div>

      {/* Toolbar actions */}
      <div className="flex items-center gap-4 bg-card border border-border p-4 rounded-lg">
        <div className="relative flex-1 max-w-sm">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
            <Search size={14} />
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search stands or zones..."
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <button className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded text-xs hover:bg-muted text-muted-foreground hover:text-foreground">
          <Filter size={14} />
          <span>Filters</span>
        </button>
      </div>

      {/* Ingress tables */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-muted-foreground">
            Ingesting crowd zones configuration...
          </div>
        ) : error ? (
          <div className="p-12 text-center text-xs text-red-500">
            Failed to load crowd zones metadata.
          </div>
        ) : filteredZones.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground">
            No stadium zones matching search criteria found.
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
              <tr>
                <th className="p-4">Zone ID</th>
                <th className="p-4">Stand / Area</th>
                <th className="p-4">Description</th>
                <th className="p-4">Estimated Count</th>
                <th className="p-4">Density Level</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredZones.map((zone) => (
                <tr key={zone.id} className="hover:bg-muted/30 transition-colors">
                  <td className="p-4 font-mono font-semibold">{zone.id}</td>
                  <td className="p-4 font-semibold text-primary">{zone.name}</td>
                  <td className="p-4 text-muted-foreground">{zone.description || "N/A"}</td>
                  <td className="p-4 font-bold">{zone.estimated_count.toLocaleString()}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 bg-background border border-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                          style={{
                            width: `${Math.round(zone.density_level * 100)}%`,
                            backgroundColor:
                              zone.density_level > 0.8
                                ? "#ef4444"
                                : zone.density_level > 0.5
                                ? "#f59e0b"
                                : "#10b981",
                          }}
                        ></div>
                      </div>
                      <span className="font-mono text-[10px]">
                        {Math.round(zone.density_level * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${getDensityColor(
                        zone.density_level
                      )}`}
                    >
                      {zone.density_level > 0.8
                        ? "CRITICAL"
                        : zone.density_level > 0.5
                        ? "WARNING"
                        : "NOMINAL"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
