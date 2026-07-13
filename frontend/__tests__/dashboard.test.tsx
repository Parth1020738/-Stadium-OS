import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StadiumMap from "@/components/map/StadiumMap";
import { useUiStore } from "@/store/uiStore";

describe("Stadium Interactive Telemetry Map", () => {
  beforeEach(() => {
    // Reset store states
    useUiStore.getState().setActiveZoneId(null);
  });

  it("should render all stadium zones with estimated counts", () => {
    render(<StadiumMap />);

    // Check that stands are displayed
    expect(screen.getByText(/North/i)).toBeInTheDocument();
    expect(screen.getByText(/South/i)).toBeInTheDocument();
  });

  it("should update active zone selection on zone polygon click", () => {
    render(<StadiumMap />);

    // Click North Stand Zone (A)
    const northStandLabel = screen.getByText(/North/i);
    // Find the polygon group wrapper or parent and trigger click
    const groupElement = northStandLabel.closest("g");
    expect(groupElement).not.toBeNull();

    fireEvent.click(groupElement!);

    // Expect uiStore state to have captured the zone ID (1 for North)
    expect(useUiStore.getState().activeZoneId).toBe(1);

    // Toggle click to deselect
    fireEvent.click(groupElement!);
    expect(useUiStore.getState().activeZoneId).toBeNull();
  });
});
