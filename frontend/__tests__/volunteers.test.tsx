/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import VolunteersPage from "@/app/volunteers/page";
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

describe("Volunteer Workspace View", () => {
  it("should render volunteer profiles workspace correctly", async () => {
    render(<VolunteersPage />, { wrapper });

    expect(screen.getByText(/VOLUNTEER & STEWARD WORKSPACE/i)).toBeInTheDocument();
  });
});
