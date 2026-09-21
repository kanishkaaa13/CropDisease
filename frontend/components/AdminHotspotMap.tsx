"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { api, type AdminHotspot } from "@/lib/api";
import SeverityBadge from "@/components/SeverityBadge";

interface AdminHotspotMapProps {
  filter?: "all" | "fungal" | "pest";
}

export default function AdminHotspotMap({ filter = "all" }: AdminHotspotMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [hotspots, setHotspots] = useState<AdminHotspot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevHotspotsHash, setPrevHotspotsHash] = useState<string>("");

  // Load hotspots data
  const loadHotspots = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.adminHotspots();
      setHotspots(data);
      
      // Create a simple hash to detect data changes
      const hash = JSON.stringify(data.map(h => ({
        r: h.risk_level,
        s: h.scan_count,
        d: h.dominant_disease_or_pest
      })));
      setPrevHotspotsHash(hash);
    } catch (err: any) {
      setError(err.message || "Failed to load hotspots");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHotspots();
  }, [loadHotspots]);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Initialize map centered on Maharashtra with CARTO Dark Matter tiles
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          }
        },
        layers: [
          {
            id: 'carto-dark',
            type: 'raster',
            source: 'carto-dark',
            minzoom: 0,
            maxzoom: 22
          }
        ]
      },
      center: [76.0, 19.0], // Center of Maharashtra
      zoom: 6,
    });

    map.current.addControl(new maplibregl.NavigationControl(), "top-right");

    return () => {
      map.current?.remove();
    };
  }, []);

  // Filter hotspots based on climate zone disease skew
  const filteredHotspots = hotspots.filter(hotspot => {
    if (filter === "all") return true;
    
    // Determine if this is fungal or pest based on climate zone
    const fungalZones = ["coastal_humid", "hill_station"];
    const pestZones = ["interior_dry", "semi_arid", "dry_drought_prone"];
    
    if (filter === "fungal") {
      return fungalZones.includes(hotspot.climate_zone);
    }
    if (filter === "pest") {
      return pestZones.includes(hotspot.climate_zone);
    }
    return true;
  });

  const addHotspotsToMap = useCallback(() => {
    if (!map.current) return;

    // Remove existing markers
    const markers = document.getElementsByClassName("admin-hotspot-marker");
    while (markers.length > 0) {
      markers[0].remove();
    }

    // Remove existing popups
    const popups = document.getElementsByClassName("maplibregl-popup");
    while (popups.length > 0) {
      popups[0].remove();
    }

    // Color mapping based on risk level (matching SeverityBadge)
    const riskColors: Record<string, string> = {
      LOW: "#10b981", // green
      MODERATE: "#f59e0b", // yellow
      HIGH: "#f97316", // orange
      CRITICAL: "#ef4444", // red
    };

    filteredHotspots.forEach((hotspot) => {
      const color = riskColors[hotspot.risk_level] || "#6b7280";
      
      // Scale marker size based on scan count (min 20px, max 40px)
      const size = Math.min(40, Math.max(20, 20 + Math.log(hotspot.scan_count + 1) * 5));

      // Create custom marker element
      const markerEl = document.createElement("div");
      markerEl.className = "admin-hotspot-marker";
      markerEl.style.width = `${size}px`;
      markerEl.style.height = `${size}px`;
      markerEl.style.borderRadius = "50%";
      markerEl.style.backgroundColor = color;
      markerEl.style.border = "3px solid white";
      markerEl.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
      markerEl.style.cursor = "pointer";
      markerEl.style.transition = "transform 0.2s";
      markerEl.style.display = "flex";
      markerEl.style.alignItems = "center";
      markerEl.style.justifyContent = "center";
      markerEl.style.color = "white";
      markerEl.style.fontSize = "10px";
      markerEl.style.fontWeight = "bold";

      markerEl.addEventListener("mouseenter", () => {
        markerEl.style.transform = "scale(1.2)";
      });

      markerEl.addEventListener("mouseleave", () => {
        markerEl.style.transform = "scale(1)";
      });

      markerEl.addEventListener("click", () => {
        const currentMap = map.current;
        if (currentMap) {
          // Generate sparkline SVG
          const maxTrend = Math.max(...hotspot.trend_data, 1);
          const sparklinePoints = hotspot.trend_data
            .map((val, idx) => {
              const x = idx * 20;
              const y = 30 - (val / maxTrend) * 25;
              return `${x},${y}`;
            })
            .join(" ");

          new maplibregl.Popup({ offset: 25, closeButton: true })
            .setHTML(`
              <div style="padding: 12px; min-width: 220px; font-family: system-ui, sans-serif;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; color: #1f2937;">
                  ${hotspot.name}
                </h3>
                <div style="margin-bottom: 8px;">
                  <span style="font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                    ${hotspot.climate_zone.replace(/_/g, " ")}
                  </span>
                  ${hotspot.source === "seeded" ? '<span style="margin-left: 8px; padding: 2px 6px; background: #f59e0b; color: white; font-size: 9px; border-radius: 4px; font-weight: bold;">DEMO</span>' : ''}
                </div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                  <span style="font-size: 12px; color: #4b5563;">Risk:</span>
                  <span style="color: ${color}; font-weight: bold; font-size: 12px;">${hotspot.risk_level}</span>
                </div>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Dominant:</strong> ${hotspot.dominant_disease_or_pest}
                </p>
                <p style="margin: 4px 0; font-size: 12px; color: #4b5563;">
                  <strong>Scans (7d):</strong> ${hotspot.scan_count}
                </p>
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
                  <p style="margin: 0 0 4px 0; font-size: 10px; color: #9ca3af;">7-day trend</p>
                  <svg width="120" height="30" viewBox="0 0 120 30">
                    <polyline
                      fill="none"
                      stroke="${color}"
                      strokeWidth="2"
                      points="${sparklinePoints}"
                    />
                  </svg>
                </div>
              </div>
            `)
            .setLngLat([hotspot.lng, hotspot.lat])
            .addTo(currentMap);
        }
      });

      const currentMap = map.current;
      if (currentMap) {
        new maplibregl.Marker({ element: markerEl })
          .setLngLat([hotspot.lng, hotspot.lat])
          .addTo(currentMap);
      }
    });
  }, [filteredHotspots]);

  // Only update markers if data has changed
  useEffect(() => {
    if (map.current && filteredHotspots.length > 0) {
      const currentHash = JSON.stringify(filteredHotspots.map(h => ({
        r: h.risk_level,
        s: h.scan_count,
        d: h.dominant_disease_or_pest
      })));
      
      if (currentHash !== prevHotspotsHash) {
        addHotspotsToMap();
      }
    }
  }, [filteredHotspots, prevHotspotsHash, addHotspotsToMap]);

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

      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/80">
          <div className="text-red-400 text-sm mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
          <button
            onClick={loadHotspots}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && filteredHotspots.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
          <div className="text-slate-400 text-sm flex flex-col items-center gap-2">
            <span className="text-3xl">🗺️</span>
            <span>No hotspots match the current filter</span>
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
