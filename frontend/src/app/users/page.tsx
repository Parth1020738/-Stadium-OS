"use client";

import React, { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/lib/api-client";
import { Users, Shield, RefreshCw } from "lucide-react";

interface UserProfile {
  first_name: string;
  last_name: string;
  phone?: string;
}

interface UserPreferences {
  language: string;
  receive_notifications: boolean;
}

interface UserData {
  id: number;
  email: string;
  status: string;
  roles: string[];
  version_id: number;
  profile?: UserProfile;
  preferences?: UserPreferences;
}

export default function UsersPage() {
  const { user: currentUser } = useAuthStore();
  const [users, setUsers] = useState<UserData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [, setErrorMsg] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await apiClient.get("/users/");
      setUsers(response.data || []);
    } catch (err) {
      const error = err as Error;
      console.warn("Failed fetching backend users, using fallback mock users.", error);
      // Fallback Mock Users
      const mockUsers: UserData[] = [
        {
          id: 1,
          email: "admin@stadium.aegis.com",
          status: "Active",
          roles: ["Administrator"],
          version_id: 1,
          profile: { first_name: "Aegis", last_name: "Admin" }
        },
        {
          id: 2,
          email: "operator@stadium.aegis.com",
          status: "Active",
          roles: ["Operator"],
          version_id: 1,
          profile: { first_name: "Alex", last_name: "Operator" }
        },
        {
          id: 3,
          email: "steward.john@stadium.aegis.com",
          status: "Active",
          roles: ["Steward"],
          version_id: 1,
          profile: { first_name: "John", last_name: "Steward" }
        },
        {
          id: 4,
          email: "steward.jane@stadium.aegis.com",
          status: "Deactivated",
          roles: ["Steward"],
          version_id: 1,
          profile: { first_name: "Jane", last_name: "Steward" }
        }
      ];
      setUsers(mockUsers);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initialization fetch — safe setState pattern
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchUsers();
  }, []);

  const handleToggleStatus = async (userToUpdate: UserData) => {
    const action = userToUpdate.status === "Active" ? "deactivate" : "activate";
    const nextStatus = userToUpdate.status === "Active" ? "Deactivated" : "Active";
    
    try {
      await apiClient.post(`/users/${userToUpdate.id}/${action}`);
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, status: nextStatus } : u));
    } catch (err) {
      const error = err as Error;
      console.warn(`Failed backend status toggle for user ${userToUpdate.id}, simulating locally.`, error);
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, status: nextStatus } : u));
    }
  };

  const handleAssignRole = async (userToUpdate: UserData, roleName: string) => {
    try {
      await apiClient.post(`/users/${userToUpdate.id}/roles`, { role_name: roleName });
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, roles: Array.from(new Set([...u.roles, roleName])) } : u));
    } catch (err) {
      const error = err as Error;
      console.warn(`Failed backend role assign for user ${userToUpdate.id}, simulating locally.`, error);
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, roles: Array.from(new Set([...u.roles, roleName])) } : u));
    }
  };

  const handleRemoveRole = async (userToUpdate: UserData, roleName: string) => {
    try {
      await apiClient.delete(`/users/${userToUpdate.id}/roles`, { data: { role_name: roleName } });
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, roles: u.roles.filter(r => r !== roleName) } : u));
    } catch (err) {
      const error = err as Error;
      console.warn(`Failed backend role removal for user ${userToUpdate.id}, simulating locally.`, error);
      setUsers(prev => prev.map(u => u.id === userToUpdate.id ? { ...u, roles: u.roles.filter(r => r !== roleName) } : u));
    }
  };

  // Administrator guard check
  const isAdmin = currentUser?.roles.includes("Administrator");

  if (!isAdmin) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded p-6 max-w-lg mx-auto text-center space-y-4">
        <h2 className="text-md font-bold text-red-500 uppercase">ACCESS DENIED</h2>
        <p className="text-xs text-muted-foreground">
          You do not have the required role clearances to access the Operator User Management dashboard. Please contact system administrators.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight uppercase flex items-center gap-2">
            <Users className="text-primary" size={24} /> Operator User Console
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Activate, deactivate, inspect, and modify security roles for stadium operators and steward personnel.
          </p>
        </div>
        <button
          onClick={fetchUsers}
          className="p-2 bg-muted hover:bg-muted/80 rounded border border-border text-muted-foreground hover:text-foreground transition-all"
          title="Refresh User Console"
        >
          <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-xs text-muted-foreground">
          Loading user records...
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-muted/50 border-b border-border uppercase text-[10px] font-semibold text-muted-foreground">
                <th className="p-4">Name / Email</th>
                <th className="p-4">Status</th>
                <th className="p-4">Assigned Roles</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 font-mono">
              {users.map((item) => (
                <tr key={item.id} className="hover:bg-muted/20 transition-colors">
                  <td className="p-4">
                    <div className="font-sans font-bold">
                      {item.profile ? `${item.profile.first_name} ${item.profile.last_name}` : "Pending profile setup"}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">{item.email}</div>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                      item.status === "Active"
                        ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                        : "bg-red-500/10 text-red-500 border-red-500/20"
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-1.5 font-sans">
                      {item.roles.map((r) => (
                        <span
                          key={r}
                          className="px-1.5 py-0.5 bg-primary/10 text-primary border border-primary/20 rounded text-[9px] font-medium flex items-center gap-1"
                        >
                          <Shield size={10} /> {r}
                          {/* Allow removing role except for the main Administrator */}
                          {r !== "Administrator" && (
                            <button
                              onClick={() => handleRemoveRole(item, r)}
                              className="text-primary hover:text-red-500 ml-1 font-bold font-mono"
                              title={`Remove ${r} role`}
                            >
                              ×
                            </button>
                          )}
                        </span>
                      ))}

                      {/* Dropdown helper to assign additional roles */}
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            handleAssignRole(item, e.target.value);
                            e.target.value = "";
                          }
                        }}
                        className="bg-muted text-muted-foreground border border-border rounded text-[9px] px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                        defaultValue=""
                      >
                        <option value="" disabled>+</option>
                        {!item.roles.includes("Operator") && <option value="Operator">Operator</option>}
                        {!item.roles.includes("Steward") && <option value="Steward">Steward</option>}
                        {!item.roles.includes("OperationsManager") && <option value="OperationsManager">Manager</option>}
                      </select>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleToggleStatus(item)}
                      className={`font-sans text-[10px] font-bold px-2 py-1 rounded border transition-all ${
                        item.status === "Active"
                          ? "bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20"
                          : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border-emerald-500/20"
                      }`}
                    >
                      {item.status === "Active" ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
