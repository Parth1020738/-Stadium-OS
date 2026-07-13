/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import TransitPage from "@/app/transit/page";
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

describe("Transit Fleet Workspace", () => {
  it("should render fleet telemetry workspace correctly", async () => {
    render(<TransitPage />, { wrapper });

    expect(screen.getByText(/TRANSIT & TRANSPORTATION PANEL/i)).toBeInTheDocument();
  });
});
