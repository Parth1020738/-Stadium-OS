/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";
import AIInsightCard from "@/components/common/AIInsightCard";
import {
  AlertTriangle,
  Search,
  Filter,
  Plus,
  Clock,
  UserCheck,
  Send,
  Loader2,
  FileText,
} from "lucide-react";

// Form validation schemas
const createIncidentSchema = z.object({
  title: z.string().min(3, { message: "Title must be at least 3 characters" }),
  description: z.string().min(5, { message: "Description must be at least 5 characters" }),
  severity: z.enum(["Low", "Medium", "High", "Critical"]),
  priority: z.enum(["Low", "Medium", "High", "Critical"]),
  category: z.enum(["Security", "Medical", "Crowd", "Facility"]),
  location_zone: z.number().min(1),
  location_details: z.string().min(2),
  sla_minutes: z.number().optional(),
});

const commentSchema = z.object({
  comment: z.string().min(1, { message: "Comment cannot be empty" }),
});

type CreateIncidentFields = z.infer<typeof createIncidentSchema>;
type CommentFields = z.infer<typeof commentSchema>;

interface IncidentItem {
  id: number;
  title: string;
  description: string;
  status: string;
  severity: string;
  priority: string;
  category: string;
  location_zone: number;
  location_details: string;
  reporter_id: number;
  created_at: string;
  comments: any[];
}

export default function IncidentsPage() {
  const queryClient = useQueryClient();
  const { hasRole } = useAuthStore();
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("All");
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // React Query: Fetch Incidents List
  const { data: incidentResponse, isLoading, error } = useQuery<{ items: IncidentItem[]; total: number }>({
    queryKey: ["incidents", priorityFilter, search],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (priorityFilter !== "All") params.priority = priorityFilter;
      if (search) params.search = search;
      const res = await apiClient.get("/incidents/", { params });
      return res.data;
    },
  });

  // React Query: Fetch Specific Incident Details (when selected)
  const { data: activeDetails } = useQuery<IncidentItem>({
    queryKey: ["incident-details", selectedIncident?.id],
    queryFn: async () => {
      const res = await apiClient.get(`/incidents/${selectedIncident?.id}`);
      return res.data;
    },
    enabled: !!selectedIncident?.id,
  });

  // Forms setup
  const {
    register: registerIncident,
    handleSubmit: handleSubmitIncident,
    reset: resetIncidentForm,
    formState: { errors: formErrors, isSubmitting: isSubmittingIncident },
  } = useForm<CreateIncidentFields>({
    resolver: zodResolver(createIncidentSchema),
    defaultValues: { severity: "Medium", priority: "Medium", category: "Security", sla_minutes: 15 },
  });

  const {
    register: registerComment,
    handleSubmit: handleSubmitComment,
    reset: resetCommentForm,
    formState: { isSubmitting: isSubmittingComment },
  } = useForm<CommentFields>({
    resolver: zodResolver(commentSchema),
  });

  // React Query Mutations: Submit Incident
  const createIncidentMutation = useMutation({
    mutationFn: async (payload: CreateIncidentFields) => {
      const res = await apiClient.post("/incidents/", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      setShowCreateModal(false);
      resetIncidentForm();
    },
  });

  // React Query Mutations: Post Comment
  const postCommentMutation = useMutation({
    mutationFn: async (payload: { incidentId: number; text: string }) => {
      const res = await apiClient.post(`/incidents/${payload.incidentId}/comments`, {
        comment: payload.text,
      });
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      // Update selected incident reference to reflect comments list
      setSelectedIncident((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          comments: [...(prev.comments || []), data],
        };
      });
      resetCommentForm();
    },
  });

  const handleCreateIncident = (data: CreateIncidentFields) => {
    createIncidentMutation.mutate(data);
  };

  const handlePostComment = (data: CommentFields) => {
    if (selectedIncident) {
      postCommentMutation.mutate({
        incidentId: selectedIncident.id,
        text: data.comment,
      });
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "Critical":
        return "text-red-500 bg-red-500/10 border-red-500/20";
      case "High":
        return "text-orange-500 bg-orange-500/10 border-orange-500/20";
      case "Medium":
        return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      default:
        return "text-primary bg-primary/10 border-primary/20";
    }
  };

  const handleExecuteCommand = (cmd: string) => {
    alert(`AI Dispatching Command: ${cmd}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">INCIDENT MANAGEMENT WORKSPACE</h1>
          <p className="text-xs text-muted-foreground">
            Ingest, dispatch, and track security and medical tickets across stadium sectors.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold rounded text-xs transition-all shadow"
        >
          <Plus size={14} />
          <span>Report Incident</span>
        </button>
      </div>

      {/* AI Insight Card */}
      <AIInsightCard page="incident" onExecuteCommand={handleExecuteCommand} />

      {/* Toolbar filters */}
      <div className="flex items-center gap-4 bg-card border border-border p-4 rounded-lg">
        <div className="relative flex-1 max-w-sm">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
            <Search size={14} />
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tickets by ID, title, zone..."
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
        >
          <option value="All">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>

      {/* Main Workspace split panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Incident List */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              Ingesting active incident logs...
            </div>
          ) : error ? (
            <div className="p-12 text-center text-xs text-red-500">
              Failed to load stadium incident tickets.
            </div>
          ) : !incidentResponse?.items || incidentResponse.items.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              No active security or medical tickets found.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
                <tr>
                  <th className="p-4">Ticket ID</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Title</th>
                  <th className="p-4">Zone</th>
                  <th className="p-4">Priority</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {incidentResponse.items.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => setSelectedIncident(inc)}
                    className={`cursor-pointer transition-colors ${
                      selectedIncident?.id === inc.id ? "bg-primary/5 hover:bg-primary/10" : "hover:bg-muted/30"
                    }`}
                  >
                    <td className="p-4 font-mono font-semibold">{inc.id}</td>
                    <td className="p-4 uppercase text-[10px] tracking-wider text-muted-foreground font-semibold">
                      {inc.category}
                    </td>
                    <td className="p-4 font-semibold text-primary">{inc.title}</td>
                    <td className="p-4">Zone {inc.location_zone}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${getPriorityColor(inc.priority)}`}>
                        {inc.priority}
                      </span>
                    </td>
                    <td className="p-4 font-semibold text-muted-foreground">{inc.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Detailed Side Panel Drawer */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          {activeDetails ? (
            <>
              <div className="border-b border-border pb-3 flex justify-between items-start">
                <div>
                  <h2 className="text-sm font-bold text-primary">{activeDetails.title}</h2>
                  <span className="text-[10px] text-muted-foreground font-mono">Ticket ID: {activeDetails.id}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${getPriorityColor(activeDetails.priority)}`}>
                  {activeDetails.priority}
                </span>
              </div>

              <div className="space-y-4 text-xs">
                <div className="space-y-1">
                  <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Description</span>
                  <p className="bg-background border border-border p-3 rounded leading-relaxed">{activeDetails.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Location Zone</span>
                    <span className="font-semibold block mt-1">Sector {activeDetails.location_zone}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Details</span>
                    <span className="font-semibold block mt-1 truncate">{activeDetails.location_details}</span>
                  </div>
                </div>
              </div>

              {/* Comment Thread Timeline */}
              <div className="space-y-3 pt-4 border-t border-border">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1.5">
                  <Clock size={12} /> Communication Log
                </h3>

                <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1">
                  {activeDetails.comments && activeDetails.comments.length > 0 ? (
                    activeDetails.comments.map((comment: any, idx: number) => (
                      <div key={idx} className="p-2.5 border border-border rounded bg-background/50 text-[11px] space-y-1">
                        <div className="flex justify-between text-muted-foreground text-[9px]">
                          <span>Operator ID: {comment.author_id || "System"}</span>
                          <span>{comment.created_at}</span>
                        </div>
                        <p className="leading-relaxed">{comment.comment}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-[11px] text-muted-foreground py-2">No updates reported yet.</p>
                  )}
                </div>

                {/* Comment Entry form */}
                <form onSubmit={handleSubmitComment(handlePostComment)} className="flex items-center gap-2 pt-2">
                  <input
                    type="text"
                    placeholder="Submit message update..."
                    {...registerComment("comment")}
                    className="flex-1 bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                  />
                  <button type="submit" className="p-2 bg-primary hover:bg-primary/95 text-primary-foreground rounded transition-all flex items-center justify-center">
                    <Send size={12} />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-xs text-muted-foreground flex flex-col items-center gap-2">
              <FileText size={24} className="text-muted-foreground" />
              <span>Select an incident ticket from the workspace to show details</span>
            </div>
          )}
        </div>
      </div>

      {/* Incident Reporting Form Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="bg-card border border-border p-6 rounded-lg shadow-2xl max-w-md w-full space-y-4">
            <div className="flex justify-between items-center border-b border-border pb-2">
              <h2 className="text-sm font-bold flex items-center gap-1.5">
                <AlertTriangle size={16} className="text-primary" /> Report Operational Incident
              </h2>
              <button onClick={() => setShowCreateModal(false)} className="text-muted-foreground hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSubmitIncident(handleCreateIncident)} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Title</label>
                <input
                  type="text"
                  placeholder="e.g. Crowd spillover Stand B"
                  {...registerIncident("title")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {formErrors.title && <span className="text-[10px] text-red-500">{formErrors.title.message}</span>}
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-muted-foreground">Description</label>
                <textarea
                  rows={2}
                  placeholder="Provide detailed incident conditions..."
                  {...registerIncident("description")}
                  className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                />
                {formErrors.description && <span className="text-[10px] text-red-500">{formErrors.description.message}</span>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Category</label>
                  <select {...registerIncident("category")} className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none">
                    <option value="Security">Security</option>
                    <option value="Medical">Medical</option>
                    <option value="Crowd">Crowd</option>
                    <option value="Facility">Facility</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Priority</label>
                  <select {...registerIncident("priority")} className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none">
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Location Zone</label>
                  <input
                    type="number"
                    {...registerIncident("location_zone", { valueAsNumber: true })}
                    className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                  />
                  {formErrors.location_zone && <span className="text-[10px] text-red-500">{formErrors.location_zone.message}</span>}
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-muted-foreground">Location Details</label>
                  <input
                    type="text"
                    placeholder="e.g. Near Gate 3 corridor"
                    {...registerIncident("location_details")}
                    className="w-full bg-background border border-border rounded px-3 py-1.5 text-xs text-foreground focus:outline-none"
                  />
                  {formErrors.location_details && <span className="text-[10px] text-red-500">{formErrors.location_details.message}</span>}
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmittingIncident}
                className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-1.5"
              >
                {isSubmittingIncident && <Loader2 size={12} className="animate-spin" />}
                <span>File Ticket</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
