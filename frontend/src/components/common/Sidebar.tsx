"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUiStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";
import {
  LayoutDashboard,
  Users2,
  AlertOctagon,
  ShieldCheck,
  Bus,
  Accessibility,
  BookOpen,
  BrainCircuit,
  Terminal,
  FileBarChart2,
  Users,
  Settings,
  Activity,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/crowd", label: "Crowd", icon: Users2 },
  { href: "/incidents", label: "Incidents", icon: AlertOctagon },
  { href: "/volunteers", label: "Volunteers", icon: ShieldCheck },
  { href: "/transit", label: "Transit", icon: Bus },
  { href: "/accessibility", label: "Accessibility", icon: Accessibility },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/ai", label: "AI", icon: BrainCircuit },
  { href: "/command-center", label: "Command Center", icon: Terminal },
  { href: "/reports", label: "Reports", icon: FileBarChart2 },
  { href: "/users", label: "Users", icon: Users, roles: ["Administrator"] },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/health", label: "Health", icon: Activity },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUiStore();
  const { user, logout } = useAuthStore();

  const handleLogout = (e: React.MouseEvent) => {
    e.preventDefault();
    logout();
  };

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen transition-all duration-300 border-r border-border bg-card flex flex-col ${
        sidebarOpen ? "w-64" : "w-16"
      }`}
    >
      {/* Sidebar Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-border">
        {sidebarOpen ? (
          <span className="text-md font-bold tracking-wider text-primary">
            AEGIS STADIUM OS
          </span>
        ) : (
          <span className="text-md font-bold text-primary">A</span>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
        >
          {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>

      {/* User Session Profile details */}
      {sidebarOpen && user && (
        <div className="p-4 border-b border-border bg-background/50">
          <div className="text-xs text-muted-foreground uppercase tracking-widest">
            Operator
          </div>
          <div className="text-sm font-semibold truncate">{user.email}</div>
          <div className="mt-1 flex flex-wrap gap-1">
            {user.roles.map((role) => (
              <span
                key={role}
                className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-primary/20 text-primary border border-primary/30"
              >
                {role}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sidebar Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          // Check role restrictions
          if (item.roles && user) {
            const hasRole = item.roles.some((r) => user.roles.includes(r));
            if (!hasRole) return null;
          }

          const IconComponent = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                isActive
                  ? "bg-primary text-primary-foreground font-semibold shadow"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <IconComponent
                size={18}
                className={`flex-shrink-0 ${
                  isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"
                }`}
              />
              {sidebarOpen && <span className="ml-3 truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Logout control at bottom */}
      <div className="p-3 border-t border-border">
        <a
          href="#"
          onClick={handleLogout}
          className="flex items-center px-3 py-2.5 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 transition-all"
        >
          <LogOut size={18} className="flex-shrink-0" />
          {sidebarOpen && <span className="ml-3">Logout</span>}
        </a>
      </div>
    </aside>
  );
}
