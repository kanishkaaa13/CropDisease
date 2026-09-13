"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { api, type RiskHotspot } from "@/lib/api";

interface OfficerMapProps {
  officerLat?: number;
  officerLng?: number;
  onHotspotClick?: (hotspot: RiskHotspot) => void;
}

export default function OfficerMap({ officerLat = 19.0, officerLng = 73.0, onHotspotClick }: OfficerMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [hotspots, setHotspots] = useState<RiskHotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedHotspot, setSelectedHotspot] = useState<RiskHotspot | null>(null);

  useEffect(() => {
    // Load hotspots data
    api.getHotspots("Maharashtra", 10.0)
      .then((data) => {
        setHotspots(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load hotspots:", err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Initialize map centered on Maharashtra
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [officerLng, officerLat],
      zoom: 6,
    });

    map.current.addControl(new maplibregl.NavigationControl(), "top-right");

    // Add hotspots when map loads
    map.current.on("load", () => {
      if (map.current && hotspots.length > 0) {
        addHotspotsToMap();
      }
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  useEffect(() => {
    if (map.current && hotspots.length > 0) {
      addHotspotsToMap();
    }
  }, [hotspots]);

  function addHotspotsToMap() {
    if (!map.current) return;

    // Remove existing markers
    const markers = document.getElementsByClassName("hotspot-marker");
    while (markers.length > 0) {
      markers[0].remove();
    }

    // Color mapping based on risk level
    const riskColors: Record<string, string> = {
      LOW: "#10b981", // green
      MODERATE: "#f59e0b", // yellow
      HIGH: "#f97316", // orange
      CRITICAL: "#ef4444", // red
    };

    hotspots.forEach((hotspot) => {
      const color = riskColors[hotspot.risk_level] || "#6b7280";

      // Create custom marker element
      const markerEl = document.createElement("div");
      markerEl.className = "hotspot-marker";
      markerEl.style.width = "24px";
      markerEl.style.height = "24px";
      markerEl.style.borderRadius = "50%";
      markerEl.style.backgroundColor = color;
      markerEl.style.border = "3px solid white";
      markerEl.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
      markerEl.style.cursor = "pointer";
      markerEl.style.transition = "transform 0.2s";

      markerEl.addEventListener("mouseenter", () => {
        markerEl.style.transform = "scale(1.2)";
      });

      markerEl.addEventListener("mouseleave", () => {
        markerEl.style.transform = "scale(1)";
      });

      markerEl.addEventListener("click", () => {
        setSelectedHotspot(hotspot);
        onHotspotClick?.(hotspot);

        // Show popup
        const currentMap = map.current;
        if (currentMap) {
          const popup = new maplibregl.Popup({ offset: 25 })
            .setHTML(`
              <div style="padding: 8px; min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; color: #1f2937;">
                  ${hotspot.district}, ${hotspot.taluka}
                </h3>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Risk Level:</strong> <span style="color: ${color}; font-weight: bold;">${hotspot.risk_level}</span>
                </p>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Avg Risk Score:</strong> ${hotspot.avg_risk_score.toFixed(1)}
                </p>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Farms:</strong> ${hotspot.farm_count} | <strong>Cases:</strong> ${hotspot.case_count}
                </p>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Dominant:</strong> ${hotspot.dominant_disease || "Unknown"}
                </p>
              </div>
            `)
            .setLngLat([hotspot.center_lng, hotspot.center_lat])
            .addTo(currentMap);
        }
      });

      const currentMap = map.current;
      if (currentMap) {
        new maplibregl.Marker({ element: markerEl })
          .setLngLat([hotspot.center_lng, hotspot.center_lat])
          .addTo(currentMap);
      }
    });
  }

  return (
    <div className="relative w-full h-full min-h-[400px] rounded-xl overflow-hidden border border-white/10">
      <div ref={mapContainer} className="absolute inset-0" />
      
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-slate-400 text-sm animate-pulse flex items-center gap-2">
            <svg className="animate-spin w-5 h-5 text-emerald-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Loading risk hotspots...
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-sm border border-white/10 rounded-lg p-3 z-10">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Risk Levels</p>
        <div className="space-y-1">
          {[
            { level: "CRITICAL", color: "#ef4444" },
            { level: "HIGH", color: "#f97316" },
            { level: "MODERATE", color: "#f59e0b" },
            { level: "LOW", color: "#10b981" },
          ].map(({ level, color }) => (
            <div key={level} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-[10px] text-slate-300">{level}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
