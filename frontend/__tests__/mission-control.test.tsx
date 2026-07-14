import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import MissionControlPage from "@/app/mission-control/page";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api-client", () => {
  const localMockPost = vi.fn().mockImplementation((url) => {
    if (url.includes("/ai/multi-agent/plan")) {
      return Promise.resolve({
        data: {
          plan: {
            query: "Gate D test",
            agents: {
              crowd: {
                name: "Crowd Agent",
                summary: "Gate D turnout test",
                reasoning: "Test reasoning",
                confidence: 0.95,
                recommended_actions: ["Open Gate D secondary"]
              }
            },
            collaboration_logs: [],
            conflicts: [
              {
                agent_a: "Crowd Agent",
                recommendation_a: "Open gate",
                agent_b: "Transit Agent",
                recommendation_b: "Close gate",
                resolution: "Keep it open"
              }
            ],
            timeline: [
              { time: "00:00", action: "Open Gate D", agent: "Crowd Agent" }
            ],
            resource_optimizations: {},
            confidence: 0.95,
            latency_ms: 120
          },
          briefings: {
            ceo: {
              role_title: "Chief Executive Officer",
              status: "Green",
              summary: "CEO summary test",
              predictions: "Predictions test",
              risks: [],
              recommended_actions: ["CEO action"],
              confidence: 0.95
            }
          }
        }
      });
    }
    return Promise.resolve({ data: { id: 123 } });
  });

  const localMockGet = vi.fn().mockResolvedValue({ data: {} });

  return {
    apiClient: {
      post: localMockPost,
      get: localMockGet
    }
  };
});

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("Mission Control Page", () => {
  it("should render page title and coordinate query response", async () => {
    render(<MissionControlPage />, { wrapper });
    
    expect(screen.getByText(/MULTI-AGENT MISSION CONTROL/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/Active Operational AI Agents/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Crowd Agent/i)[0]).toBeInTheDocument();
      expect(screen.getByText(/Gate D turnout test/i)).toBeInTheDocument();
    });
  });
});
