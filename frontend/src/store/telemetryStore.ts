import { create } from "zustand";

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  kafka_status: "Healthy" | "Degraded" | "Down";
  redis_status: "Healthy" | "Degraded" | "Down";
  db_status: "Healthy" | "Degraded" | "Down";
}

export interface LiveAlert {
  id: string;
  title: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  timestamp: string;
  message: string;
}

export interface ZoneData {
  zone_id: number;
  name: string;
  estimated_count: number;
  density_level: number; // 0.0 to 1.0
}

export interface VehicleData {
  vehicle_id: string;
  name: string;
  status: string;
  route_id: string;
  latitude: number;
  longitude: number;
  capacity_used: number;
}

export interface IncidentData {
  incident_id: number;
  title: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "Assigned" | "Resolved" | "Closed";
  location_zone: number;
  created_at: string;
}

export interface BarrierData {
  barrier_id: number;
  description: string;
  severity: "Low" | "Medium" | "High";
  location_zone: number;
}

interface TelemetryState {
  wsConnected: boolean;
  metrics: SystemMetrics;
  alerts: LiveAlert[];
  crowdCount: number;
  zones: ZoneData[];
  vehicles: VehicleData[];
  incidents: IncidentData[];
  barriers: BarrierData[];
  setWsConnected: (connected: boolean) => void;
  updateMetrics: (metrics: Partial<SystemMetrics>) => void;
  addAlert: (alert: LiveAlert) => void;
  clearAlerts: () => void;
  setCrowdCount: (count: number) => void;
  setZones: (zones: ZoneData[]) => void;
  updateZone: (zone_id: number, updates: Partial<ZoneData>) => void;
  setVehicles: (vehicles: VehicleData[]) => void;
  updateVehicle: (vehicle_id: string, updates: Partial<VehicleData>) => void;
  setIncidents: (incidents: IncidentData[]) => void;
  addOrUpdateIncident: (incident: IncidentData) => void;
  setBarriers: (barriers: BarrierData[]) => void;
}

// Initial mock stadium zones data matching standard layout
const initialZones: ZoneData[] = [
  { zone_id: 1, name: "North Stand (Zone A)", estimated_count: 5200, density_level: 0.65 },
  { zone_id: 2, name: "East Concourse (Zone B)", estimated_count: 3100, density_level: 0.45 },
  { zone_id: 3, name: "South Stand (Zone C)", estimated_count: 7800, density_level: 0.95 }, // High density
  { zone_id: 4, name: "West Concourse (Zone D)", estimated_count: 2400, density_level: 0.3 },
  { zone_id: 5, name: "Plaza Entry (Zone E)", estimated_count: 1500, density_level: 0.2 },
];

const initialVehicles: VehicleData[] = [
  { vehicle_id: "SHUTTLE-1", name: "North Shuttle", status: "In Transit", route_id: "R1", latitude: 35, longitude: 40, capacity_used: 18 },
  { vehicle_id: "SHUTTLE-2", name: "South Shuttle", status: "Stationary", route_id: "R2", latitude: 65, longitude: 60, capacity_used: 0 },
];

const initialIncidents: IncidentData[] = [
  { incident_id: 101, title: "Medical: Heat Exhaustion", severity: "Medium", status: "Assigned", location_zone: 3, created_at: "09:15 AM" },
  { incident_id: 102, title: "Security: Minor Scuffle", severity: "High", status: "Open", location_zone: 1, created_at: "09:20 AM" },
];

const initialBarriers: BarrierData[] = [
  { barrier_id: 501, description: "Gate 4 Turnstile Failure", severity: "Medium", location_zone: 3 },
];

export const useTelemetryStore = create<TelemetryState>((set) => ({
  wsConnected: false,
  metrics: {
    cpu_usage: 12,
    memory_usage: 34,
    active_connections: 4,
    kafka_status: "Healthy",
    redis_status: "Healthy",
    db_status: "Healthy",
  },
  alerts: [],
  crowdCount: 20000,
  zones: initialZones,
  vehicles: initialVehicles,
  incidents: initialIncidents,
  barriers: initialBarriers,

  setWsConnected: (connected) => set({ wsConnected: connected }),
  updateMetrics: (metrics) =>
    set((state) => ({ metrics: { ...state.metrics, ...metrics } })),
  addAlert: (alert) =>
    set((state) => {
      const updatedAlerts = [alert, ...state.alerts].slice(0, 50);
      return { alerts: updatedAlerts };
    }),
  clearAlerts: () => set({ alerts: [] }),
  setCrowdCount: (crowdCount) => set({ crowdCount }),
  setZones: (zones) => set({ zones }),
  updateZone: (zone_id, updates) =>
    set((state) => ({
      zones: state.zones.map((z) => (z.zone_id === zone_id ? { ...z, ...updates } : z)),
    })),
  setVehicles: (vehicles) => set({ vehicles }),
  updateVehicle: (vehicle_id, updates) =>
    set((state) => ({
      vehicles: state.vehicles.map((v) =>
        v.vehicle_id === vehicle_id ? { ...v, ...updates } : v
      ),
    })),
  setIncidents: (incidents) => set({ incidents }),
  addOrUpdateIncident: (incident) =>
    set((state) => {
      const exists = state.incidents.some((i) => i.incident_id === incident.incident_id);
      const incidentsList = exists
        ? state.incidents.map((i) => (i.incident_id === incident.incident_id ? incident : i))
        : [incident, ...state.incidents];
      return { incidents: incidentsList };
    }),
  setBarriers: (barriers) => set({ barriers }),
}));
