import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/store/authStore";

// Mock JWT token helper
const generateMockToken = (roles: string[]) => {
  const payload = {
    sub: "123",
    roles: roles,
    exp: Math.floor(Date.now() / 1000) + 3600,
    iat: Math.floor(Date.now() / 1000),
    jti: "mock-jti",
  };
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const data = btoa(JSON.stringify(payload));
  return `${header}.${data}.signature`;
};

describe("Authentication Zustand Store", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it("should initialize with default guest values", () => {
    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("should process login and decode roles/scopes correctly", () => {
    const token = generateMockToken(["Operator"]);
    useAuthStore.getState().login(token, "mock-refresh", "operator@stadium.com");

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe(token);
    expect(state.user?.email).toBe("operator@stadium.com");
    expect(state.user?.roles).toContain("Operator");
    expect(state.isAuthenticated).toBe(true);

    // Operator scopes should be resolved
    expect(state.user?.scopes).toContain("transit:read");
    expect(state.user?.scopes).toContain("incidents:write");
    expect(state.user?.scopes).not.toContain("commands:approve");
  });

  it("should respect Administrator scope bypass", () => {
    const token = generateMockToken(["Administrator"]);
    useAuthStore.getState().login(token, "mock-refresh", "admin@stadium.com");

    const state = useAuthStore.getState();
    expect(state.hasRole(["Operator"])).toBe(true); // Admin bypasses checks
    expect(state.hasPermission("commands:approve")).toBe(true);
    expect(state.hasPermission("some:nonexistent:scope")).toBe(true);
  });

  it("should clear session variables on logout", () => {
    const token = generateMockToken(["Steward"]);
    useAuthStore.getState().login(token, "mock-refresh", "steward@stadium.com");
    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});
