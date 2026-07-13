import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "@/app/(auth)/login/page";

// Mock Next.js router
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("Login Screen View", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render credentials email and password input fields", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign In/i })).toBeInTheDocument();
  });

  it("should render validation errors on empty inputs submit", async () => {
    render(<LoginPage />);

    const submitBtn = screen.getByRole("button", { name: /Sign In/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid email format/i)).toBeInTheDocument();
      expect(screen.getByText(/Password must be at least 6 characters/i)).toBeInTheDocument();
    });
  });
});
