"use client";

import React, { useEffect, useState, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useUiStore } from "@/store/uiStore";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useWebSocket } from "@/hooks/useWebSocket";
import { AlertCircle } from "lucide-react";

interface DashboardShellProps {
  children: React.ReactNode;
}

const IDLE_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const COUNTDOWN_MS = 60 * 1000; // 60 seconds warning

export default function DashboardShell({ children }: DashboardShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, logout } = useAuthStore();
  const { sidebarOpen } = useUiStore();
  
  const [mounted, setMounted] = useState(false);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [countdown, setCountdown] = useState(60);

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(0);
  const syncChannelRef = useRef<BroadcastChannel | null>(null);

  // Connect websocket streams for dashboard telemetry if logged in
  useWebSocket("metrics");
  useWebSocket("alerts");

  // Sync logouts across multiple open tabs
  useEffect(() => {
    if (typeof window !== "undefined") {
      const channel = new BroadcastChannel("aegis_session_sync");
      syncChannelRef.current = channel;
      channel.onmessage = (event) => {
        if (event.data === "logout") {
          console.log("Logged out from another tab. Syncing logout...");
          logout();
          router.push("/session-expired");
        }
      };
      return () => {
        channel.close();
      };
    }
  }, [logout, router]);

  // Track page mount
  useEffect(() => {
    lastActivityRef.current = Date.now();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  // Inactivity tracking
  useEffect(() => {
    if (!mounted || !accessToken) return;

    const resetIdleTimer = () => {
      lastActivityRef.current = Date.now();
      setShowTimeoutWarning(false);
      setCountdown(60);
      
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);

      idleTimerRef.current = setTimeout(() => {
        triggerWarning();
      }, IDLE_TIMEOUT_MS - COUNTDOWN_MS);
    };

    const triggerWarning = () => {
      setShowTimeoutWarning(true);
      let count = 60;
      setCountdown(count);

      countdownTimerRef.current = setInterval(() => {
        count -= 1;
        setCountdown(count);
        if (count <= 0) {
          clearInterval(countdownTimerRef.current!);
          handleAutoLogout();
        }
      }, 1000);
    };

    const handleAutoLogout = () => {
      logout();
      if (syncChannelRef.current) {
        syncChannelRef.current.postMessage("logout");
      }
      router.push("/session-expired");
    };

    // User activity listeners
    const activityEvents = ["mousemove", "keydown", "click", "scroll"];
    activityEvents.forEach((event) => {
      window.addEventListener(event, resetIdleTimer);
    });

    // Page Visibility API support
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        const timePassed = Date.now() - lastActivityRef.current;
        if (timePassed >= IDLE_TIMEOUT_MS) {
          handleAutoLogout();
        } else {
          resetIdleTimer();
        }
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    resetIdleTimer();

    return () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
      activityEvents.forEach((event) => {
        window.removeEventListener(event, resetIdleTimer);
      });
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [accessToken, mounted, logout, router]);

  // Auth redirection logic
  useEffect(() => {
    if (!mounted) return;

    const isAuthRoute =
      pathname === "/login" ||
      pathname === "/register" ||
      pathname === "/forgot-password" ||
      pathname === "/reset-password";

    if (!accessToken && !isAuthRoute && pathname !== "/session-expired") {
      router.push("/login");
    } else if (accessToken && isAuthRoute) {
      router.push("/");
    }
  }, [accessToken, pathname, mounted, router]);

  const keepSessionAlive = () => {
    lastActivityRef.current = Date.now();
    setShowTimeoutWarning(false);
    setCountdown(60);
    if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    
    idleTimerRef.current = setTimeout(() => {
      setShowTimeoutWarning(true);
    }, IDLE_TIMEOUT_MS - COUNTDOWN_MS);
  };

  if (!mounted) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background text-foreground text-sm font-semibold">
        Loading Aegis OS...
      </div>
    );
  }

  const isAuthRoute =
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password" ||
    pathname === "/session-expired";

  if (isAuthRoute) {
    return <main className="min-h-screen bg-background">{children}</main>;
  }

  if (!accessToken) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background text-foreground text-sm font-semibold">
        Authenticating Operator...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <Sidebar />

      <div
        className={`flex flex-col flex-1 min-h-screen transition-all duration-300 ${
          sidebarOpen ? "pl-64" : "pl-16"
        }`}
      >
        <Topbar />
        <main className="flex-1 p-6 pt-22 overflow-x-hidden">{children}</main>
      </div>

      {/* Session Expiring Dialog Warning Modal */}
      {showTimeoutWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-card border border-border p-6 rounded-lg shadow-2xl max-w-sm w-full text-center space-y-4 glow-critical">
            <div className="mx-auto h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
              <AlertCircle size={24} />
            </div>
            <div>
              <h2 className="text-md font-bold">SESSION INACTIVITY TIMEOUT</h2>
              <p className="text-xs text-muted-foreground mt-2">
                Your session is about to expire due to inactivity. You will be automatically logged out in:
              </p>
              <div className="mt-3 text-3xl font-extrabold text-red-500">
                {countdown}s
              </div>
            </div>
            <button
              onClick={keepSessionAlive}
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all"
            >
              Keep Session Alive
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
