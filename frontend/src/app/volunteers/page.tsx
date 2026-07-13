"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ShieldCheck, Search, Filter, Phone, Mail, Award, Clock } from "lucide-react";

interface VolunteerItem {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  preferred_language: string;
  skills: { name: string }[];
  certifications: { name: string; authority: string }[];
}

export default function VolunteersPage() {
  const [search, setSearch] = useState("");
  const [selectedVolunteer, setSelectedVolunteer] = useState<VolunteerItem | null>(null);

  // React Query: Fetch volunteers list
  const { data: volunteerResponse, isLoading, error } = useQuery<{ results: VolunteerItem[] }>({
    queryKey: ["volunteers", search],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const res = await apiClient.get("/volunteers", { params });
      // Depending on backend design, results could be wrapped inPaginationResponse or direct array
      const data = res.data;
      if (Array.isArray(data)) return { results: data };
      if (data.results) return data;
      if (data.items) return { results: data.items };
      return { results: [] };
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">VOLUNTEER & STEWARD WORKSPACE</h1>
        <p className="text-xs text-muted-foreground">
          Track stadium staff registries, certifications, and sector assignments.
        </p>
      </div>

      {/* Roster statistics row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Active Volunteers Present
            </span>
            <span className="text-2xl font-black block">48</span>
            <span className="text-[9px] text-emerald-500 font-bold block uppercase">
              Nominal coverage sectors
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center text-primary">
            <ShieldCheck size={20} />
          </div>
        </div>

        <div className="bg-card border border-border p-4 rounded-lg flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">
              Assigned Sectors Shifts
            </span>
            <span className="text-2xl font-black block">32 / 37</span>
            <span className="text-[9px] text-amber-500 font-bold block uppercase">
              5 shifts require assignment
            </span>
          </div>
          <div className="h-10 w-10 rounded bg-amber-500/10 flex items-center justify-center text-amber-500">
            <Clock size={20} />
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
            placeholder="Search volunteers by first name, last name, email..."
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <button className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded text-xs hover:bg-muted text-muted-foreground hover:text-foreground">
          <Filter size={14} />
          <span>Filter Roles</span>
        </button>
      </div>

      {/* Split pane details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Volunteers List */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              Ingesting volunteer registry...
            </div>
          ) : error ? (
            <div className="p-12 text-center text-xs text-red-500">
              Failed to load volunteer records.
            </div>
          ) : !volunteerResponse?.results || volunteerResponse.results.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground">
              No registered volunteers matching search query.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-background border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
                <tr>
                  <th className="p-4">Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Phone</th>
                  <th className="p-4">Language</th>
                  <th className="p-4">Skills</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {volunteerResponse.results.map((vol) => (
                  <tr
                    key={vol.id}
                    onClick={() => setSelectedVolunteer(vol)}
                    className={`cursor-pointer transition-colors ${
                      selectedVolunteer?.id === vol.id ? "bg-primary/5 hover:bg-primary/10" : "hover:bg-muted/30"
                    }`}
                  >
                    <td className="p-4 font-semibold text-primary">
                      {vol.first_name} {vol.last_name}
                    </td>
                    <td className="p-4 text-muted-foreground">{vol.email}</td>
                    <td className="p-4 font-mono">{vol.phone}</td>
                    <td className="p-4 uppercase text-[10px]">{vol.preferred_language}</td>
                    <td className="p-4">
                      <div className="flex gap-1 flex-wrap">
                        {vol.skills && vol.skills.slice(0, 2).map((s, idx) => (
                          <span key={idx} className="px-1.5 py-0.5 rounded bg-background border border-border text-[9px]">
                            {s.name}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Selected profile details side panel */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          {selectedVolunteer ? (
            <>
              <div className="border-b border-border pb-3 text-center space-y-3">
                <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl font-bold font-mono">
                  {selectedVolunteer.first_name[0]}
                  {selectedVolunteer.last_name[0]}
                </div>
                <div>
                  <h2 className="text-sm font-bold">
                    {selectedVolunteer.first_name} {selectedVolunteer.last_name}
                  </h2>
                  <span className="text-[10px] text-muted-foreground block uppercase mt-0.5">
                    Steward / Marshall
                  </span>
                </div>
              </div>

              <div className="space-y-4 text-xs">
                <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                  Contact Details
                </h3>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Mail size={12} className="text-muted-foreground" />
                    <span>{selectedVolunteer.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone size={12} className="text-muted-foreground" />
                    <span>{selectedVolunteer.phone}</span>
                  </div>
                </div>
              </div>

              {/* Skills Certifications lists */}
              <div className="space-y-4 pt-2 text-xs">
                <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border pb-1 flex items-center gap-1">
                  <Award size={12} className="text-yellow-500" /> Certifications & Competencies
                </h3>

                <div className="space-y-2">
                  {selectedVolunteer.certifications && selectedVolunteer.certifications.length > 0 ? (
                    selectedVolunteer.certifications.map((c, idx) => (
                      <div key={idx} className="p-2 border border-border rounded bg-background/50">
                        <div className="font-semibold text-primary">{c.name}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">Authority: {c.authority}</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-[11px] text-muted-foreground italic">No certified credentials registered.</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-xs text-muted-foreground flex flex-col items-center gap-2">
              <ShieldCheck size={24} className="text-muted-foreground" />
              <span>Select a volunteer operator to inspect profile and credential records</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
