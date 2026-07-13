/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";
import {
  Terminal,
  CheckCircle,
  XCircle,
  Clock,
  ShieldCheck,
  Search,
  Plus,
  Loader2,
  FileText,
} from "lucide-react";

// Schemas
const approveSchema = z.object({
  comments: z.string().min(2, { message: "Comments must explain reason" }),
});

const commandSchema = z.object({
  command_type: z.string().min(2),
  payload: z.string().optional(),
});

type ApproveFields = z.infer<typeof approveSchema>;
type CommandFields = z.infer<typeof commandSchema>;

interface CommandItem {
  id: number;
  command_type: string;
  payload: any;
  status: string;
  creator_id: number;
  approver_id: number | null;
  created_at: string;
  updated_at: string;
}

export default function CommandCenterPage() {
  const queryClient = useQueryClient();
  const { hasRole } = useAuthStore();
  const [search, setSearch] = useState("");
  const [selectedCommand, setSelectedCommand] = useState<CommandItem | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // React Query: Fetch commands history list
  const { data: commands, isLoading, error } = useQuery<CommandItem[]>({
    queryKey: ["commands", search],
    queryFn: async () => {
      const res = await apiClient.get("/commands");
      return res.data;
    },
  });

  const {
    register: registerApprove,
    handleSubmit: handleSubmitApprove,
    formState: { errors: approveErrors, isSubmitting: isApproving },
    reset: resetApprove,
  } = useForm<ApproveFields>({
    resolver: zodResolver(approveSchema),
  });

  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    formState: { errors: createErrors, isSubmitting: isCreating },
    reset: resetCreate,
  } = useForm<CommandFields>({
    resolver: zodResolver(commandSchema),
  });

  // React Query Mutations: Submit Command
  const createCommandMutation = useMutation({
    mutationFn: async (payload: CommandFields) => {
      const parsedPayload = JSON.parse(payload.payload || "{}");
      const res = await apiClient.post("/commands", {
        command_type: payload.command_type,
        payload: parsedPayload,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commands"] });
      setShowCreateModal(false);
      resetCreate();
      setSuccessMsg("Command queued successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
  });

  // React Query Mutations: Approve Command
  const approveMutation = useMutation({
    mutationFn: async (payload: { id: number; comments: string }) => {
      const res = await apiClient.post(`/commands/${payload.id}/approve`, {
        comments: payload.comments,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commands"] });
      setSelectedCommand(null);
      resetApprove();
      setSuccessMsg("Command approved successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
  });

  // React Query Mutations: Reject Command
  const rejectMutation = useMutation({
    mutationFn: async (payload: { id: number; comments: string }) => {
      const res = await apiClient.post(`/commands/${payload.id}/reject`, {
        comments: payload.comments,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commands"] });
      setSelectedCommand(null);
      resetApprove();
      setSuccessMsg("Command rejected successfully!");
      setTimeout(() => setSuccessMsg(null), 3000);
    },
  });

  const handleCreate = (data: CommandFields) => {
    createCommandMutation.mutate(data);
  };

  const handleApprove = (data: ApproveFields) => {
    if (selectedCommand) {
      approveMutation.mutate({ id: selectedCommand.id, comments: data.comments });
    }
  };

  const handleReject = (data: ApproveFields) => {
    if (selectedCommand) {
      rejectMutation.mutate({ id: selectedCommand.id, comments: data.comments });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Approved":
      case "Completed":
        return <CheckCircle size={14} className="text-emerald-500" />;
      case "Rejected":
      case "Failed":
        return <XCircle size={14} className="text-red-500" />;
      case "Pending":
        return <Clock size={14} className="text-yellow-500 animate-pulse" />;
      default:
        return <Terminal size={14} className="text-primary" />;
    }
  };

  const filteredCommands = (commands || []).filter(
    (c) =>
      c.command_type.toLowerCase().includes(search.toLowerCase()) ||
      c.status.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">OPERATIONS COMMAND CENTRAL</h1>
          <p className="text-xs text-muted-foreground">
            Execute critical gateway overrides, inspect pending two-person approvals, and track system audits.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold rounded text-xs transition-all shadow"
        >
          <Plus size={14} />
          <span>Queue Override</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-500 text-xs">
          {successMsg}
        </div>
      )}

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
            placeholder="Search commands override queue..."
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {/* Workspace split view */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Commands Queue */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              Ingesting commands history logs...
            </div>
          ) : error ? (
            <div className="p-12 text-center text-xs text-red-500">
              Failed to load commands queue.
            </div>
          ) : filteredCommands.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              No overrides or commands reported in queue.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
                <tr>
                  <th className="p-4">Command ID</th>
                  <th className="p-4">Override Actions</th>
                  <th className="p-4">Creator ID</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Created Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredCommands.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => setSelectedCommand(c)}
                    className={`cursor-pointer transition-colors ${
                      selectedCommand?.id === c.id ? "bg-primary/5 hover:bg-primary/10" : "hover:bg-muted/30"
                    }`}
                  >
                    <td className="p-4 font-mono font-semibold">{c.id}</td>
                    <td className="p-4 font-semibold text-primary">{c.command_type}</td>
                    <td className="p-4 font-mono text-muted-foreground">Operator {c.creator_id}</td>
                    <td className="p-4 flex items-center gap-2">
                      {getStatusIcon(c.status)}
                      <span className="font-semibold text-muted-foreground">{c.status}</span>
                    </td>
                    <td className="p-4 text-muted-foreground">{c.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Command approval actions panel */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          {selectedCommand ? (
            <>
              <div className="border-b border-border pb-3">
                <h2 className="text-sm font-bold text-primary">{selectedCommand.command_type}</h2>
                <span className="text-[10px] text-muted-foreground font-mono">Command ID: {selectedCommand.id}</span>
              </div>

              <div className="space-y-4 text-xs">
                <div className="space-y-1">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Creator ID</span>
                  <span className="font-semibold block font-mono">Operator {selectedCommand.creator_id}</span>
                </div>

                <div className="space-y-1">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Payload Parameters</span>
                  <pre className="bg-background border border-border p-3 rounded font-mono text-[10px] overflow-x-auto text-foreground">
                    {JSON.stringify(selectedCommand.payload, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Approval controls - visible if status is Pending */}
              {selectedCommand.status === "Pending" && (
                <div className="space-y-4 pt-4 border-t border-border">
                  <div className="border-b border-border pb-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1.5">
                      <ShieldCheck size={14} /> Two-Person Auth Approval Required
                    </h3>
                  </div>

                  <form className="space-y-3 text-xs">
                    <div className="space-y-1">
                      <label className="font-semibold text-muted-foreground">Comments / Reason</label>
                      <input
                        type="text"
                        placeholder="Explain reason for override approval/rejection..."
                        {...registerApprove("comments")}
                        className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                      />
                      {approveErrors.comments && <span className="text-[10px] text-red-500">{approveErrors.comments.message}</span>}
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <button
                        type="button"
                        onClick={handleSubmitApprove(handleApprove)}
                        disabled={isApproving || !hasRole(["Administrator", "OperationsManager"])}
                        className="bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                      >
                        {isApproving && <Loader2 size={12} className="animate-spin" />}
                        <span>Approve</span>
                      </button>
                      <button
                        type="button"
                        onClick={handleSubmitApprove(handleReject)}
                        disabled={isApproving || !hasRole(["Administrator", "OperationsManager"])}
                        className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                      >
                        {isApproving && <Loader2 size={12} className="animate-spin" />}
                        <span>Reject</span>
                      </button>
                    </div>
                    {!hasRole(["Administrator", "OperationsManager"]) && (
                      <span className="text-[9px] text-red-500 block text-center font-medium">
                        Access Denied: Requires Administrator or OperationsManager scope to approve overrides.
                      </span>
                    )}
                  </form>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20 text-xs text-muted-foreground flex flex-col items-center gap-2">
              <FileText size={24} className="text-muted-foreground" />
              <span>Select a queued override to view approval triggers</span>
            </div>
          )}
        </div>
      </div>

      {/* Creation Modal form */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="bg-card border border-border p-6 rounded-lg shadow-2xl max-w-md w-full space-y-4">
            <div className="flex justify-between items-center border-b border-border pb-2">
              <h2 className="text-sm font-bold flex items-center gap-1.5 text-primary">
                <Terminal size={16} /> Submit Command Override
              </h2>
              <button onClick={() => setShowCreateModal(false)} className="text-muted-foreground hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Command Override Type</label>
                <input
                  type="text"
                  placeholder="e.g. TurnstileUnlock, RouteRedirect"
                  {...registerCreate("command_type")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {createErrors.command_type && <span className="text-[10px] text-red-500">{createErrors.command_type.message}</span>}
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Payload Parameters (JSON String)</label>
                <textarea
                  rows={4}
                  placeholder='e.g. { "gate_id": "G4", "state": "Unlocked" }'
                  {...registerCreate("payload")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none font-mono"
                />
                {createErrors.payload && <span className="text-[10px] text-red-500">{createErrors.payload.message}</span>}
              </div>

              <button
                type="submit"
                disabled={isCreating}
                className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5"
              >
                {isCreating && <Loader2 size={12} className="animate-spin" />}
                <span>Queue Command</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
