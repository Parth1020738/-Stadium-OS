"use client";

import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api-client";
import { useTelemetryStore } from "@/store/telemetryStore";
import { useAuthStore } from "@/store/authStore";
import { Bus, Settings, Loader2 } from "lucide-react";

// Form validation schema
const egressPacingSchema = z.object({
  venue_id: z.string().min(2),
  pacing_rate_limit_per_minute: z.number().min(1),
  calculation_model: z.string().optional(),
  authorized_user_id: z.number().min(1),
});

type EgressPacingFields = z.infer<typeof egressPacingSchema>;

interface RouteItem {
  id: number;
  name: string;
  route_code: string;
  route_type: string;
  description: string;
}

export default function TransitPage() {
  const { hasRole } = useAuthStore();
  const { vehicles } = useTelemetryStore();
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // React Query: Fetch transit routes
  const { data: routeResponse, isLoading, error } = useQuery<{ results: RouteItem[] }>({
    queryKey: ["transit-routes"],
    queryFn: async () => {
      const res = await apiClient.get("/transit/routes");
      const data = res.data;
      if (Array.isArray(data)) return { results: data };
      if (data.results) return data;
      if (data.items) return { results: data.items };
      return { results: [] };
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<EgressPacingFields>({
    resolver: zodResolver(egressPacingSchema),
    defaultValues: { venue_id: "stadium_main", pacing_rate_limit_per_minute: 40, calculation_model: "Dynamic", authorized_user_id: 1 },
  });

  // React Query Mutation: Update Egress Pacing Rate
  const updatePacingMutation = useMutation({
    mutationFn: async (payload: EgressPacingFields) => {
      const res = await apiClient.post("/transit/egress-pacing", {
        traceId: "trace-101",
        correlationId: "corr-101",
        data: payload,
      });
      return res.data;
    },
    onSuccess: () => {
      setSuccessMsg("Egress pacing limit updated successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
      reset({ venue_id: "stadium_main", pacing_rate_limit_per_minute: 40, calculation_model: "Dynamic", authorized_user_id: 1 });
    },
  });

  const onSubmitPacing = (data: EgressPacingFields) => {
    updatePacingMutation.mutate(data);
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-border">
        <h1 className="text-2xl font-bold tracking-tight">TRANSIT & TRANSPORTATION PANEL</h1>
        <p className="text-xs text-muted-foreground">
          Track shuttle fleet locations, schedules, and dynamic egress turnstile pacing.
        </p>
      </div>

      {/* Transit stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Active Shuttle Fleet
            </span>
            <span className="text-2xl font-black block">{vehicles.length}</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Operational Nominal
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center text-primary">
            <Bus size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Egress Pacing limit
            </span>
            <span className="text-2xl font-black block">40 / min</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Current gate pacing nominal
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <Settings size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Ingress Hub delay
            </span>
            <span className="text-2xl font-black block">0 min</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              No delays flagged
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <Bus size={20} />
          </div>
        </div>
      </div>

      {/* Main split view */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Shuttle Vehicles / Routes list */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active fleet tracking */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xs font-bold uppercase tracking-wider border-b border-border pb-2 text-muted-foreground mb-4">
              Active Shuttle Fleet Status
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {vehicles.map((v) => (
                <div key={v.vehicle_id} className="p-4 border border-border rounded bg-background/50 flex justify-between items-center">
                  <div className="space-y-1">
                    <span className="text-xs font-bold text-primary">{v.name}</span>
                    <span className="text-[10px] text-muted-foreground block">ID: {v.vehicle_id}</span>
                    <span className="text-[9px] text-muted-foreground block">Capacity Occupied: {v.capacity_used} passengers</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 uppercase">
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Registered routes list */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="p-4 border-b border-border bg-background/30">
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Registered Transport Routes
              </h2>
            </div>
            {isLoading ? (
              <div className="p-12 text-center text-xs text-muted-foreground">
                Ingesting registered transit routes...
              </div>
            ) : error ? (
              <div className="p-12 text-center text-xs text-red-500">
                Failed to load transit routes.
              </div>
            ) : !routeResponse?.results || routeResponse.results.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground">
                No active routes registered.
              </div>
            ) : (
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
                  <tr>
                    <th className="p-4">Route ID</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Code</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {routeResponse.results.map((route) => (
                    <tr key={route.id} className="hover:bg-muted/30 transition-colors">
                      <td className="p-4 font-mono font-semibold">{route.id}</td>
                      <td className="p-4 font-semibold text-primary">{route.name}</td>
                      <td className="p-4 font-mono">{route.route_code}</td>
                      <td className="p-4 uppercase text-[10px] text-muted-foreground font-semibold">{route.route_type}</td>
                      <td className="p-4 text-muted-foreground">{route.description || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Egress pacing configuration panel */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          <div className="border-b border-border pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Settings size={14} className="text-primary" /> Turnstile Egress Pacing
            </h2>
            <span className="text-[10px] text-muted-foreground block mt-0.5">Adjust crowd outflow rates near exit gates</span>
          </div>

          {successMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-500 text-xs">
              {successMsg}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmitPacing)} className="space-y-4 text-xs">
            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground">Venue Scope ID</label>
              <input
                type="text"
                {...register("venue_id")}
                className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
              />
              {errors.venue_id && <span className="text-[10px] text-red-500">{errors.venue_id.message}</span>}
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-muted-foreground">Egress Flow Limit (pax/min)</label>
              <input
                type="number"
                {...register("pacing_rate_limit_per_minute", { valueAsNumber: true })}
                className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
              />
              {errors.pacing_rate_limit_per_minute && (
                <span className="text-[10px] text-red-500">{errors.pacing_rate_limit_per_minute.message}</span>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !hasRole(["Administrator", "OperationsManager"])}
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              {isSubmitting && <Loader2 size={12} className="animate-spin" />}
              <span>Apply Pacing Limits</span>
            </button>
            {!hasRole(["Administrator", "OperationsManager"]) && (
              <span className="text-[9px] text-red-500 block text-center font-medium">
                Access Denied: Requires Administrator or OperationsManager role scope approval permissions.
              </span>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
