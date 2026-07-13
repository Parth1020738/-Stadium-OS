/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";

vi.mock("axios", async () => {
  const actual: any = await vi.importActual("axios");
  return {
    ...actual,
    post: vi.fn(),
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      defaults: { headers: { common: {} } },
    })),
  };
});

describe("Axios Request Interceptor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().logout();
  });

  it("should configure base authorization header if token exists", async () => {
    useAuthStore.getState().accessToken = "mock-access-token";

    // Invoke interceptor
    const requestInterceptor = (apiClient.interceptors.request as any).handlers[0].fulfilled;
    const configObj = { headers: {} };
    const result = requestInterceptor(configObj);

    expect(result.headers.Authorization).toBe("Bearer mock-access-token");
  });
});
