/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import IncidentsPage from "@/app/incidents/page";
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

describe("Incidents Workspace Split View", () => {
  it("should render tickets workspace split view correctly", async () => {
    render(<IncidentsPage />, { wrapper });

    expect(screen.getByText(/INCIDENT MANAGEMENT WORKSPACE/i)).toBeInTheDocument();
    expect(screen.getByText(/Report Incident/i)).toBeInTheDocument();
  });
});
