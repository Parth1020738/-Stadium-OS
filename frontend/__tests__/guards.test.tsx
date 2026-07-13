import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { RoleGuard, PermissionGuard } from "@/components/common/Guards";
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

describe("RBAC UI Guards", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it("should render fallback if not authenticated", () => {
    render(
      <RoleGuard allowedRoles={["Steward"]} fallback={<div>Fallback Text</div>}>
        <div>Secret Content</div>
      </RoleGuard>
    );

    expect(screen.queryByText("Secret Content")).not.toBeInTheDocument();
    expect(screen.getByText("Fallback Text")).toBeInTheDocument();
  });

  it("should render secret content if user has allowed role", () => {
    const token = generateMockToken(["Steward"]);
    useAuthStore.getState().login(token, "mock", "test@steward.com");

    render(
      <RoleGuard allowedRoles={["Steward", "Operator"]}>
        <div>Secret Content</div>
      </RoleGuard>
    );

    expect(screen.getByText("Secret Content")).toBeInTheDocument();
  });

  it("should hide content and show fallback if user lacks role", () => {
    const token = generateMockToken(["Steward"]);
    useAuthStore.getState().login(token, "mock", "test@steward.com");

    render(
      <RoleGuard allowedRoles={["Operator"]} fallback={<div>Forbidden Action</div>}>
        <div>Control Panel</div>
      </RoleGuard>
    );

    expect(screen.queryByText("Control Panel")).not.toBeInTheDocument();
    expect(screen.getByText("Forbidden Action")).toBeInTheDocument();
  });

  it("should correctly render content based on permissions", () => {
    const token = generateMockToken(["Operator"]);
    useAuthStore.getState().login(token, "mock", "test@operator.com");

    render(
      <PermissionGuard permission="transit:write" fallback={<div>ReadOnly</div>}>
        <div>Shuttle Console</div>
      </PermissionGuard>
    );

    expect(screen.getByText("Shuttle Console")).toBeInTheDocument();
    expect(screen.queryByText("ReadOnly")).not.toBeInTheDocument();
  });
});
