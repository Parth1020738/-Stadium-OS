import { useEffect, useRef } from "react";
import { useAuthStore } from "@/store/authStore";
import { useTelemetryStore } from "@/store/telemetryStore";

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const useWebSocket = (channel: string) => {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const { accessToken } = useAuthStore();
  const { setWsConnected } = useTelemetryStore();

  useEffect(() => {
    if (!accessToken) return;

    const connect = () => {
      // Build full WebSocket URL with token query parameter
      const wsUrl = `${WS_BASE_URL}/ws/dashboard${
        channel ? `/${channel}` : ""
      }?token=${accessToken}`;

      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setWsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Start heartbeat ping
        heartbeatIntervalRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send("ping");
          }
        }, 30000);
      };

      socket.onmessage = (event) => {
        if (event.data === "pong") return;

        try {
          const data = JSON.parse(event.data);
          // Broadcast message parser to Zustand telemetryStore
          const telemetryStore = useTelemetryStore.getState();

          if (channel === "metrics") {
            telemetryStore.updateMetrics(data);
          } else if (channel === "alerts") {
            telemetryStore.addAlert(data);
          } else if (channel === "crowd") {
            telemetryStore.setCrowdCount(data.estimated_count || 0);
          }
        } catch {
          // Avoid console noise in production; ignore malformed events
        }
      };

      socket.onclose = () => {
        setWsConnected(false);
        cleanup();

        // Auto-reconnect logic with exponential backoff
        const delay = Math.min(
          1000 * Math.pow(2, reconnectAttemptsRef.current),
          30000,
        );
        reconnectAttemptsRef.current += 1;

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      socket.onerror = () => {
        // Avoid console noise in production; onclose will handle status update/reconnect
      };
    };

    const cleanup = () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    connect();

    return () => {
      cleanup();
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [channel, accessToken, setWsConnected]);
};
