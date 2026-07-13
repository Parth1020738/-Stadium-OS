/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import CrowdPage from "@/app/crowd/page";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: any) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("Crowd Workspace View", () => {
  it("should render workspace headers and loading cards", async () => {
    render(<CrowdPage />, { wrapper });

    expect(screen.getByText(/CROWD MANAGEMENT WORKSPACE/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search stands or zones/i)).toBeInTheDocument();
  });
});
