import { create } from "zustand";

interface UiState {
  sidebarOpen: boolean;
  activeZoneId: number | null;
  activeEventName: string;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveZoneId: (zoneId: number | null) => void;
  setActiveEventName: (name: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  activeZoneId: null,
  activeEventName: "Championship Bowl 2026",
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveZoneId: (zoneId) => set({ activeZoneId: zoneId }),
  setActiveEventName: (name) => set({ activeEventName: name }),
}));
