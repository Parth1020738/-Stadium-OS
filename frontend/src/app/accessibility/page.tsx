"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api-client";
import { Accessibility, Search, AlertOctagon, Plus, Loader2, Info } from "lucide-react";

// Form validation schema
const barrierSchema = z.object({
  barrier_type: z.string().min(2),
  severity: z.enum(["Low", "Medium", "High"]),
  location_zone: z.number().min(1),
  location_details: z.string().min(2),
  description: z.string().min(5),
});

type BarrierFields = z.infer<typeof barrierSchema>;

interface BarrierItem {
  id: number;
  barrier_type: string;
  severity: string;
  location_zone: number;
  location_details: string;
  description: string;
  status: string;
}

export default function AccessibilityPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // React Query: Fetch accessibility barriers for stadium_main
  const { data: barriers, isLoading, error } = useQuery<BarrierItem[]>({
    queryKey: ["barriers", search],
    queryFn: async () => {
      const res = await apiClient.get("/venues/stadium_main/accessibility/barriers");
      return res.data;
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<BarrierFields>({
    resolver: zodResolver(barrierSchema),
    defaultValues: { severity: "Medium", location_zone: 1 },
  });

  // React Query Mutation: Register Barrier
  const createBarrierMutation = useMutation({
    mutationFn: async (payload: BarrierFields) => {
      const res = await apiClient.post("/venues/stadium_main/accessibility/barriers", {
        traceId: "trace-202",
        correlationId: "corr-202",
        data: payload,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["barriers"] });
      setSuccessMsg("Accessibility barrier registered successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
      setShowModal(false);
      reset();
    },
  });

  const onSubmitBarrier = (data: BarrierFields) => {
    createBarrierMutation.mutate(data);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "High":
        return "text-red-500 bg-red-500/10 border-red-500/20";
      case "Medium":
        return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      default:
        return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    }
  };

  const filteredBarriers = (barriers || []).filter(
    (b) =>
      b.barrier_type.toLowerCase().includes(search.toLowerCase()) ||
      b.description.toLowerCase().includes(search.toLowerCase()) ||
      b.location_details.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">ACCESSIBILITY OPERATIONS</h1>
          <p className="text-xs text-muted-foreground">
            Track structural obstacles, lift outages, and verify wheelchair path clearances.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold rounded text-xs transition-all shadow"
        >
          <Plus size={14} />
          <span>Report Barrier</span>
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Active Structural Obstacles
            </span>
            <span className="text-2xl font-black block">{filteredBarriers.length}</span>
            <span className="text-[9px] text-amber-500 font-bold block uppercase">
              Rerouting active near Gate 4
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-amber-500/10 flex items-center justify-center text-amber-500">
            <AlertOctagon size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Elevators Operational
            </span>
            <span className="text-2xl font-black block">11 / 12</span>
            <span className="text-[9px] text-amber-500 font-bold block uppercase">
              1 unit in Zone C servicing
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-amber-500/10 flex items-center justify-center text-amber-500">
            <Info size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Steward Wheelchair escorts
            </span>
            <span className="text-2xl font-black block">6 Active</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              nominal steward availability
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <Accessibility size={20} />
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
            placeholder="Search barriers by type, description, sector..."
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-500 text-xs">
          {successMsg}
        </div>
      )}

      {/* Barriers List Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-muted-foreground">
            Ingesting active accessibility barriers...
          </div>
        ) : error ? (
          <div className="p-12 text-center text-xs text-red-500">
            Failed to load active barriers.
          </div>
        ) : filteredBarriers.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted-foreground">
            No active barriers matching query found. All pathways clear.
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
              <tr>
                <th className="p-4">Barrier ID</th>
                <th className="p-4">Type</th>
                <th className="p-4">Description</th>
                <th className="p-4">Zone</th>
                <th className="p-4">Location Details</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredBarriers.map((b) => (
                <tr key={b.id} className="hover:bg-muted/30 transition-colors">
                  <td className="p-4 font-mono font-semibold">{b.id}</td>
                  <td className="p-4 font-semibold text-primary">{b.barrier_type}</td>
                  <td className="p-4 text-muted-foreground">{b.description}</td>
                  <td className="p-4">Sector {b.location_zone}</td>
                  <td className="p-4 truncate max-w-[150px]">{b.location_details}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${getSeverityColor(b.severity)}`}>
                      {b.severity}
                    </span>
                  </td>
                  <td className="p-4 font-semibold text-muted-foreground">{b.status || "Active"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal Report Barrier Form */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="bg-card border border-border p-6 rounded-lg shadow-2xl max-w-md w-full space-y-4">
            <div className="flex justify-between items-center border-b border-border pb-2">
              <h2 className="text-sm font-bold flex items-center gap-1.5 text-primary">
                <Accessibility size={16} /> Report Accessibility Obstruction
              </h2>
              <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSubmit(onSubmitBarrier)} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Barrier Type</label>
                <input
                  type="text"
                  placeholder="e.g. Lift Inoperable, Path Blocked"
                  {...register("barrier_type")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {errors.barrier_type && <span className="text-[10px] text-red-500">{errors.barrier_type.message}</span>}
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Description</label>
                <textarea
                  rows={2}
                  placeholder="Provide detailed obstruction conditions..."
                  {...register("description")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {errors.description && <span className="text-[10px] text-red-500">{errors.description.message}</span>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Severity</label>
                  <select {...register("severity")} className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none">
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Location Zone</label>
                  <input
                    type="number"
                    {...register("location_zone", { valueAsNumber: true })}
                    className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                  />
                  {errors.location_zone && <span className="text-[10px] text-red-500">{errors.location_zone.message}</span>}
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Location Details</label>
                <input
                  type="text"
                  placeholder="e.g. Near Elevator 2 Stand C lobby"
                  {...register("location_details")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {errors.location_details && <span className="text-[10px] text-red-500">{errors.location_details.message}</span>}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5"
              >
                {isSubmitting && <Loader2 size={12} className="animate-spin" />}
                <span>Register Obstruction</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
