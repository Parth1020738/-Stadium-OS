"use client";

import React from "react";
import { useTelemetryStore } from "@/store/telemetryStore";
import { useUiStore } from "@/store/uiStore";
import { AlertOctagon, Bus, ShieldAlert } from "lucide-react";

export default function StadiumMap() {
  const { zones, vehicles, incidents, barriers } = useTelemetryStore();
  const { activeZoneId, setActiveZoneId } = useUiStore();

  // SVG polygons coordinates representing stadium zones
  const zoneShapes = [
    {
      id: 1,
      name: "North Stand (Zone A)",
      points: "100,50 300,50 350,150 50,150",
      centerX: 200,
      centerY: 100,
    },
    {
      id: 2,
      name: "East Concourse (Zone B)",
      points: "300,50 400,100 400,300 350,350 300,250",
      centerX: 350,
      centerY: 200,
    },
    {
      id: 3,
      name: "South Stand (Zone C)",
      points: "50,250 350,250 300,350 100,350",
      centerX: 200,
      centerY: 300,
    },
    {
      id: 4,
      name: "West Concourse (Zone D)",
      points: "100,50 50,150 50,250 100,350 150,200",
      centerX: 100,
      centerY: 200,
    },
    {
      id: 5,
      name: "Plaza Entry (Zone E)",
      points: "20,20 80,20 80,80 20,80",
      centerX: 50,
      centerY: 50,
    },
  ];

  // Helper to color-code zones based on live crowd density
  const getZoneFillColor = (zoneId: number, density: number, isActive: boolean) => {
    let baseColor = "rgba(16, 185, 129, 0.2)"; // Low density
    let strokeColor = "rgba(16, 185, 129, 0.6)";

    if (density > 0.8) {
      baseColor = "rgba(239, 68, 68, 0.4)"; // High density
      strokeColor = "rgba(239, 68, 68, 0.8)";
    } else if (density > 0.5) {
      baseColor = "rgba(245, 158, 11, 0.35)"; // Medium density
      strokeColor = "rgba(245, 158, 11, 0.7)";
    }

    if (isActive) {
      return { fill: baseColor, stroke: "#38bdf8", strokeWidth: 3 };
    }
    return { fill: baseColor, stroke: strokeColor, strokeWidth: 1.5 };
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Interactive Arena Ingestion Map
        </h2>
        <span className="text-[10px] text-muted-foreground">Click a zone to isolate details</span>
      </div>

      <div className="relative flex-1 bg-background/30 rounded border border-border/50 overflow-hidden flex items-center justify-center min-h-[300px] lg:min-h-[400px]">
        
        {/* SVG Drawing Layer */}
        <svg viewBox="0 0 450 400" className="w-full h-full max-h-[420px]">
          {/* Outer Grid Mock Background */}
          <defs>
            <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Zones Render */}
          {zoneShapes.map((shape) => {
            const liveZone = zones.find((z) => z.zone_id === shape.id);
            const density = liveZone?.density_level || 0;
            const isActive = activeZoneId === shape.id;
            const style = getZoneFillColor(shape.id, density, isActive);

            return (
              <g key={shape.id} className="cursor-pointer" onClick={() => setActiveZoneId(isActive ? null : shape.id)}>
                <polygon
                  points={shape.points}
                  fill={style.fill}
                  stroke={style.stroke}
                  strokeWidth={style.strokeWidth}
                  className="transition-all duration-300 hover:fill-opacity-80"
                />
                {/* Zone label text */}
                <text
                  x={shape.centerX}
                  y={shape.centerY}
                  fill="#f9fafb"
                  fontSize="9"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="pointer-events-none select-none drop-shadow"
                >
                  {liveZone?.name.split(" ")[0]}
                </text>
                <text
                  x={shape.centerX}
                  y={shape.centerY + 12}
                  fill={density > 0.8 ? "#ef4444" : density > 0.5 ? "#f59e0b" : "#10b981"}
                  fontSize="8"
                  textAnchor="middle"
                  className="pointer-events-none select-none font-semibold"
                >
                  {liveZone?.estimated_count.toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* Render Active Incident Icons */}
          {incidents
            .filter((inc) => inc.status !== "Closed" && inc.status !== "Resolved")
            .map((inc) => {
              const zone = zoneShapes.find((s) => s.id === inc.location_zone);
              if (!zone) return null;
              // Slightly offset incidents from center
              const x = zone.centerX - 25;
              const y = zone.centerY - 20;

              return (
                <g key={inc.incident_id} className="animate-pulse">
                  <circle cx={x} cy={y} r="12" fill="rgba(239, 68, 68, 0.2)" stroke="rgba(239, 68, 68, 0.8)" strokeWidth="1" />
                  <foreignObject x={x - 6} y={y - 6} width="12" height="12">
                    <AlertOctagon size={12} className="text-red-500" />
                  </foreignObject>
                </g>
              );
            })}

          {/* Render Active Shuttle Vehicles */}
          {vehicles.map((v) => {
            // Position shuttle according to coordinates
            const x = (v.longitude / 100) * 450;
            const y = (v.latitude / 100) * 400;

            return (
              <g key={v.vehicle_id} className="transition-all duration-500">
                <rect x={x - 10} y={y - 10} width="20" height="20" rx="3" fill="#0ea5e9" stroke="#ffffff" strokeWidth="1" className="shadow" />
                <foreignObject x={x - 6} y={y - 6} width="12" height="12">
                  <Bus size={12} className="text-white" />
                </foreignObject>
                <text x={x} y={y - 12} fontSize="7" fill="#9ca3af" textAnchor="middle" fontWeight="bold">
                  {v.vehicle_id.split("-")[1]}
                </text>
              </g>
            );
          })}

          {/* Render Accessibility Barriers */}
          {barriers.map((b) => {
            const zone = zoneShapes.find((s) => s.id === b.location_zone);
            if (!zone) return null;
            const x = zone.centerX + 25;
            const y = zone.centerY + 15;

            return (
              <g key={b.barrier_id} className="animate-bounce">
                <circle cx={x} cy={y} r="8" fill="rgba(245, 158, 11, 0.2)" stroke="rgba(245, 158, 11, 0.8)" strokeWidth="1" />
                <foreignObject x={x - 4} y={y - 4} width="8" height="8">
                  <ShieldAlert size={8} className="text-yellow-500" />
                </foreignObject>
              </g>
            );
          })}
        </svg>

        {/* Selected Zone Info Panel overlay */}
        {activeZoneId && (
          <div className="absolute bottom-4 left-4 right-4 bg-[#111827]/90 border border-border p-3 rounded-lg text-xs space-y-1 backdrop-blur">
            {(() => {
              const liveZone = zones.find((z) => z.zone_id === activeZoneId);
              return (
                <>
                  <div className="flex justify-between font-bold">
                    <span className="text-primary">{liveZone?.name}</span>
                    <button onClick={() => setActiveZoneId(null)} className="text-muted-foreground hover:text-white">✕</button>
                  </div>
                  <div className="flex justify-between text-[11px] text-muted-foreground">
                    <span>Estimated Count: {liveZone?.estimated_count.toLocaleString()}</span>
                    <span>Density Ratio: {Math.round((liveZone?.density_level || 0) * 100)}%</span>
                  </div>
                </>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
