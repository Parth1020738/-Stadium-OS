/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AiPage from "@/app/ai/page";
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

describe("AI Decision Support Workspace", () => {
  it("should render risk speedometers and suggestions cards", async () => {
    render(<AiPage />, { wrapper });

    expect(screen.getByText(/AI DECISION SUPPORT PANEL/i)).toBeInTheDocument();
    expect(screen.getByText(/Overall Risk Index/i)).toBeInTheDocument();
  });
});
