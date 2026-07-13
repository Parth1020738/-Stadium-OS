/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import CommandCenterPage from "@/app/command-center/page";
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

describe("Operations Command Override Queue", () => {
  it("should render command centers override table", async () => {
    render(<CommandCenterPage />, { wrapper });

    expect(screen.getByText(/OPERATIONS COMMAND CENTRAL/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search commands override queue/i)).toBeInTheDocument();
  });
});
