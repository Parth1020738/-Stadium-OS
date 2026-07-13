import { create } from "zustand";

export interface UserPayload {
  id: string;
  email: string;
  roles: string[];
  scopes: string[];
}

export const ROLE_PERMISSIONS: Record<string, string[]> = {
  Steward: ["transit:read", "accessibility:read", "incidents:read", "volunteers:read"],
  Operator: [
    "transit:read",
    "transit:write",
    "accessibility:read",
    "accessibility:write",
    "incidents:read",
    "incidents:write",
    "volunteers:read",
    "volunteers:write",
  ],
  OperationsManager: [
    "transit:read",
    "transit:write",
    "accessibility:read",
    "accessibility:write",
    "incidents:read",
    "incidents:write",
    "volunteers:read",
    "volunteers:write",
    "commands:approve",
  ],
  Administrator: [
    "transit:read",
    "transit:write",
    "accessibility:read",
    "accessibility:write",
    "incidents:read",
    "incidents:write",
    "volunteers:read",
    "volunteers:write",
    "commands:approve",
    "admin:*",
  ],
};

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserPayload | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isRefreshing: boolean;
  login: (accessToken: string, refreshToken: string, userEmail: string) => void;
  logout: () => void;
  setRefreshing: (refreshing: boolean) => void;
  hasRole: (allowedRoles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

// Helper to decode JWT sub and roles
const decodeJwtPayload = (token: string): { sub: string; roles: string[] } | null => {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Failed to decode JWT:", e);
    return null;
  }
};

const getInitialState = () => {
  if (typeof window === "undefined" || typeof window.localStorage === "undefined") {
    return {
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isRefreshing: false,
    };
  }
  const accessToken = window.localStorage.getItem("aegis_access_token");
  const refreshToken = window.localStorage.getItem("aegis_refresh_token");
  const userJson = window.localStorage.getItem("aegis_user");
  let user: UserPayload | null = null;
  try {
    user = userJson ? JSON.parse(userJson) : null;
  } catch (e) {
    console.error("Failed parsing initial user context:", e);
  }
  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated: !!accessToken,
    isLoading: false,
    isRefreshing: false,
  };
};

export const useAuthStore = create<AuthState>((set, get) => ({
  ...getInitialState(),

  login: (accessToken, refreshToken, userEmail) => {
    const decoded = decodeJwtPayload(accessToken);
    const roles = decoded?.roles || ["Steward"];
    const id = decoded?.sub || "unknown";

    // Gather client permissions derived from database roles
    const scopesSet = new Set<string>();
    roles.forEach((role) => {
      const perms = ROLE_PERMISSIONS[role] || [];
      perms.forEach((p) => scopesSet.add(p));
    });

    const user: UserPayload = {
      id,
      email: userEmail,
      roles,
      scopes: Array.from(scopesSet),
    };

    if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
      window.localStorage.setItem("aegis_access_token", accessToken);
      window.localStorage.setItem("aegis_refresh_token", refreshToken);
      window.localStorage.setItem("aegis_user", JSON.stringify(user));
    }

    set({ accessToken, refreshToken, user, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
      window.localStorage.removeItem("aegis_access_token");
      window.localStorage.removeItem("aegis_refresh_token");
      window.localStorage.removeItem("aegis_user");
    }
    set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  },

  setRefreshing: (isRefreshing) => set({ isRefreshing }),

  hasRole: (allowedRoles) => {
    const user = get().user;
    if (!user) return false;
    // Administrator bypass
    if (user.roles.includes("Administrator")) return true;
    return allowedRoles.some((role) => user.roles.includes(role));
  },

  hasPermission: (permission) => {
    const user = get().user;
    if (!user) return false;
    if (user.roles.includes("Administrator")) return true;
    return user.scopes.includes(permission);
  },
}));
