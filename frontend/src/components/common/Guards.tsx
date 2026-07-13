"use client";

import React from "react";
import { useAuthStore } from "@/store/authStore";

interface GuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface RoleGuardProps extends GuardProps {
  allowedRoles: string[];
}

interface PermissionGuardProps extends GuardProps {
  permission: string;
}

export function RoleGuard({ allowedRoles, children, fallback = null }: RoleGuardProps) {
  const { hasRole, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) return fallback;

  if (hasRole(allowedRoles)) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
}

export function PermissionGuard({ permission, children, fallback = null }: PermissionGuardProps) {
  const { hasPermission, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) return fallback;

  if (hasPermission(permission)) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
}
