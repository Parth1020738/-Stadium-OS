/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import AccessibilityPage from "@/app/accessibility/page";
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

describe("Accessibility Operations View", () => {
  it("should render barrier registry workspace correctly", async () => {
    render(<AccessibilityPage />, { wrapper });

    expect(screen.getByText(/ACCESSIBILITY OPERATIONS/i)).toBeInTheDocument();
  });
});
