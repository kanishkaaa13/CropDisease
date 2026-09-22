"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster";
import "leaflet.heat";
import { LocateFixed, Maximize2, RefreshCw, RotateCcw } from "lucide-react";
import { api, type OfficerMapData, type OfficerMapDistrict, type OfficerMapPoint } from "@/lib/api";

const RISK_ORDER = { LOW: 1, MODERATE: 2, HIGH: 3, CRITICAL: 4 } as const;
const RISK_COLORS: Record<keyof typeof RISK_ORDER, string> = {
  LOW: "#2f9e62",
  MODERATE: "#d9a514",
  HIGH: "#e2762d",
  CRITICAL: "#c94848",
};
const MAP_CENTER: [number, number] = [19.7, 75.7];
const INDIA_BOUNDS: L.LatLngBoundsExpression = [[6.5, 68], [35.7, 97.5]];
const DEFAULT_FILTERS = { crop: "", disease: "", risk: "", days: 30 };

export interface OfficerMapFilters {
  crop: string;
  disease: string;
  risk: string;
  days: number;
  district?: string;
}

interface OfficerMapProps {
  officerLat?: number;
  officerLng?: number;
  onValidatePoint?: (point: OfficerMapPoint) => void;
  onChatPoint?: (point: OfficerMapPoint) => void;
  onFilterChange?: (filters: OfficerMapFilters) => void;
}

interface MapControllerProps {
  onMapReady: (map: L.Map) => void;
  onLocate: () => void;
}

interface ClusterLayer extends L.LayerGroup {
  addLayer(layer: L.Layer): this;
  clearLayers(): this;
  addTo(map: L.Map): this;
}

type LeafletWithPlugins = typeof L & {
  markerClusterGroup: (options?: L.MarkerClusterGroupOptions) => ClusterLayer;
  heatLayer: (latlngs: [number, number, number][], options?: L.LayerOptions & Record<string, unknown>) => L.Layer;
};

const leafletWithPlugins = L as LeafletWithPlugins;

function MapController({ onMapReady, onLocate }: MapControllerProps) {
  const map = useMap();

  useEffect(() => {
    onMapReady(map);
    map.invalidateSize();
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map, onMapReady]);

  useEffect(() => {
    map.setMaxBounds(INDIA_BOUNDS);
    map.options.maxBoundsViscosity = 0.8;
  }, [map]);

  useEffect(() => {
    const locate = () => onLocate();
    map.on("locationfound", locate);
    return () => {
      map.off("locationfound", locate);
    };
  }, [map, onLocate]);

  return null;
}

function escapeHtml(value: string) {
  return value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character] ?? character);
}

function riskForDistrict(district: OfficerMapDistrict | undefined) {
  return district?.max_risk ?? "LOW";
}

function MapLayers({
  data,
  showClusters,
  showHeatmap,
  onPointSelect,
  onClusterSelect,
  onValidatePoint,
  onChatPoint,
}: {
  data: OfficerMapData;
  showClusters: boolean;
  showHeatmap: boolean;
  onPointSelect: (point: OfficerMapPoint) => void;
  onClusterSelect: (point: OfficerMapPoint) => void;
  onValidatePoint?: (point: OfficerMapPoint) => void;
  onChatPoint?: (point: OfficerMapPoint) => void;
}) {
  const map = useMap();
  const pointsRef = useRef<OfficerMapPoint[]>(data.points);
  pointsRef.current = data.points;

  useEffect(() => {
    const clusterGroup = leafletWithPlugins.markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 48,
      iconCreateFunction: (cluster) => {
        const markers = cluster.getAllChildMarkers();
        const highest = markers.reduce<keyof typeof RISK_ORDER>((current, marker) => {
          const risk = (marker.options as { risk?: keyof typeof RISK_ORDER }).risk ?? "LOW";
          return RISK_ORDER[risk] > RISK_ORDER[current] ? risk : current;
        }, "LOW");
        const size = markers.length > 99 ? 48 : markers.length > 25 ? 42 : 36;
        return L.divIcon({
          html: `<span aria-label="${markers.length} cases, highest risk ${highest}">${markers.length}</span>`,
          className: `risk-cluster risk-cluster-${highest.toLowerCase()}`,
          iconSize: [size, size],
        });
      },
    });

    data.points.forEach((point) => {
      const size = 12 + Math.round(Math.max(0, Math.min(100, point.confidence)) / 18);
      const marker = L.marker([point.lat, point.lng], {
        risk: point.risk,
        pointId: point.id,
        icon: L.divIcon({
          className: "risk-observation-icon",
          html: `<span style="width:${size}px;height:${size}px;background:${RISK_COLORS[point.risk]}"></span>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        }),
      } as L.MarkerOptions & { risk: keyof typeof RISK_ORDER; pointId: string });
      marker.bindPopup(`
        <div class="risk-popup">
          <strong>${escapeHtml(point.farm_name)}</strong>
          <span>${escapeHtml(point.crop)} · ${escapeHtml(point.disease)}</span>
          <span>Confidence: ${point.confidence.toFixed(1)}%</span>
          <span>Risk: <b class="risk-text-${point.risk.toLowerCase()}">${point.risk}</b></span>
          <span>Reported: ${new Date(point.date).toLocaleDateString()}</span>
          <span>Distance: ${point.distance_km.toFixed(1)} km</span>
          <button type="button" class="risk-popup-action" data-action="validate" data-point-id="${point.id}">Validate</button>
          <button type="button" class="risk-popup-action" data-action="chat" data-point-id="${point.id}">Chat</button>
        </div>
      `);
      marker.on("click", () => onPointSelect(point));
      marker.on("popupopen", (event) => {
        const popup = event.popup.getElement();
        popup?.querySelector<HTMLButtonElement>("[data-action='validate']")?.addEventListener("click", () => onValidatePoint?.(point));
        popup?.querySelector<HTMLButtonElement>("[data-action='chat']")?.addEventListener("click", () => onChatPoint?.(point));
      });
      clusterGroup.addLayer(marker);
    });

    clusterGroup.on("clusterclick", (event) => {
      const child = event.layer.getAllChildMarkers()[0];
      const location = child?.getLatLng();
      const point = pointsRef.current.find((candidate) => candidate.lat === location?.lat && candidate.lng === location?.lng);
      if (point) onClusterSelect(point);
    });

    if (showClusters) clusterGroup.addTo(map);

    const heat = leafletWithPlugins.heatLayer(
      data.points.map((point) => [point.lat, point.lng, RISK_ORDER[point.risk] / 4] as [number, number, number]),
      { radius: 28, blur: 22, maxZoom: 11, gradient: { 0.25: "#2f9e62", 0.5: "#d9a514", 0.75: "#e2762d", 1: "#c94848" } },
    );
    if (showHeatmap) heat.addTo(map);

    return () => {
      map.removeLayer(clusterGroup);
      map.removeLayer(heat);
    };
  }, [data.points, map, onChatPoint, onClusterSelect, onPointSelect, onValidatePoint, showClusters, showHeatmap]);

  return null;
}

function districtStyle(feature?: Feature<Geometry>) {
  const risk = (feature?.properties?.risk as keyof typeof RISK_ORDER | undefined) ?? "LOW";
  return { color: "#59635c", weight: 1, fillColor: RISK_COLORS[risk], fillOpacity: 0.42 };
}

export default function OfficerMap({ officerLat = 19.7, officerLng = 75.7, onValidatePoint, onChatPoint, onFilterChange }: OfficerMapProps) {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [data, setData] = useState<OfficerMapData | null>(null);
  const [geoJson, setGeoJson] = useState<FeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [map, setMap] = useState<L.Map | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [showClusters, setShowClusters] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showDistricts, setShowDistricts] = useState(true);
  const [selectedDistrict, setSelectedDistrict] = useState<OfficerMapDistrict | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<OfficerMapPoint | null>(null);
  const [tab, setTab] = useState<"live" | "gis">("live");
  const [gisError, setGisError] = useState(false);
  const gisTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [mapData, boundaryResponse] = await Promise.all([
        api.getOfficerMapData({ ...filters, officerLat, officerLng }),
        fetch("/geo/maharashtra_districts.geojson").then((response) => {
          if (!response.ok) throw new Error("District boundary data could not be loaded.");
          return response.json() as Promise<FeatureCollection>;
        }),
      ]);
      setData(mapData);
      setGeoJson(boundaryResponse);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Map data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [filters, officerLat, officerLng]);

  useEffect(() => {
    const timeout = setTimeout(loadData, 300);
    return () => clearTimeout(timeout);
  }, [loadData]);

  useEffect(() => {
    onFilterChange?.(filters);
  }, [filters, onFilterChange]);

  useEffect(() => () => {
    if (gisTimer.current) clearTimeout(gisTimer.current);
  }, []);

  const districtFeatures = useMemo(() => {
    if (!geoJson || !data) return null;
    const districtMap = new Map(data.districts.map((district) => [district.district.toLowerCase(), district]));
    return {
      ...geoJson,
      features: geoJson.features.map((feature) => {
        const name = String(feature.properties?.NAME_2 ?? feature.properties?.name ?? "");
        const district = districtMap.get(name.toLowerCase());
        return { ...feature, properties: { ...feature.properties, risk: riskForDistrict(district), district } };
      }),
    } as FeatureCollection;
  }, [data, geoJson]);

  const selectedTrend = data?.trend ?? [];
  const districtClick = useCallback((feature: Feature<Geometry>) => {
    const district = feature.properties?.district as OfficerMapDistrict | undefined;
    if (district) {
      setSelectedDistrict(district);
      setFilters((current) => ({ ...current, district: district.district }));
    }
  }, []);

  const locate = useCallback(() => {
    if (!map) return;
    map.locate({ setView: true, maxZoom: 10 });
  }, [map]);

  const startGis = () => {
    setTab("gis");
    setGisError(false);
    if (gisTimer.current) clearTimeout(gisTimer.current);
    gisTimer.current = setTimeout(() => {
      setGisError(true);
      setTab("live");
    }, 5000);
  };

  const priorityCases = selectedDistrict && data
    ? data.priority_cases.filter((point) => point.district === selectedDistrict.district)
    : data?.priority_cases ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Risk map filters">
        <select aria-label="Filter by crop" value={filters.crop} onChange={(event) => setFilters({ ...filters, crop: event.target.value })} className="map-control"><option value="">All crops</option>{data?.filter_options.crops.map((crop) => <option key={crop}>{crop}</option>)}</select>
        <select aria-label="Filter by disease" value={filters.disease} onChange={(event) => setFilters({ ...filters, disease: event.target.value })} className="map-control"><option value="">All diseases</option>{data?.filter_options.diseases.map((disease) => <option key={disease}>{disease}</option>)}</select>
        <select aria-label="Filter by risk" value={filters.risk} onChange={(event) => setFilters({ ...filters, risk: event.target.value })} className="map-control"><option value="">All risk levels</option>{Object.keys(RISK_ORDER).map((risk) => <option key={risk}>{risk}</option>)}</select>
        <select aria-label="Filter by date range" value={filters.days} onChange={(event) => setFilters({ ...filters, days: Number(event.target.value) })} className="map-control"><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option></select>
        <div className="ml-auto flex gap-2">
          <button type="button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="map-button" aria-label="Switch map theme">{theme === "dark" ? "Light map" : "Dark map"}</button>
          <button type="button" onClick={() => map?.setView(MAP_CENTER, 6)} className="map-icon-button" aria-label="Reset map view"><RotateCcw className="h-4 w-4" /></button>
          <button type="button" onClick={locate} className="map-icon-button" aria-label="Locate me"><LocateFixed className="h-4 w-4" /></button>
          <button type="button" onClick={() => map?.getContainer().requestFullscreen?.()} className="map-icon-button" aria-label="Open map fullscreen"><Maximize2 className="h-4 w-4" /></button>
          <button type="button" onClick={loadData} className="map-icon-button" aria-label="Refresh map data"><RefreshCw className="h-4 w-4" /></button>
        </div>
      </div>

      <div className="flex gap-1 border-b border-white/10">
        <button type="button" onClick={() => setTab("live")} className={`map-tab ${tab === "live" ? "map-tab-active" : ""}`}>Live Map</button>
        <button type="button" onClick={startGis} className={`map-tab ${tab === "gis" ? "map-tab-active" : ""}`}>Government GIS</button>
      </div>

      {tab === "gis" && !gisError ? (
        <iframe title="Government GIS Maharashtra" src="https://stategisportal.nic.in/stategisportal/Home/Map/27" className="h-[600px] w-full rounded-lg border border-white/10 bg-[#202721]" onError={() => { setGisError(true); setTab("live"); }} />
      ) : (
        <div className="relative h-[420px] overflow-hidden rounded-lg border border-white/10 sm:h-[560px]">
          {loading && <div className="absolute inset-0 z-20 animate-pulse bg-[#202721] p-6"><div className="h-full rounded-lg bg-white/5" /></div>}
          {error && <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-3 bg-[#202721] text-sm text-red-200"><p>{error}</p><button type="button" onClick={loadData} className="map-button"><RefreshCw className="mr-2 inline h-4 w-4" />Retry</button></div>}
          {!loading && !error && data?.points.length === 0 && <div className="absolute inset-0 z-20 flex items-center justify-center bg-[#202721]/85 text-sm text-stone-300">No observations match these filters.</div>}
          <MapContainer center={MAP_CENTER} zoom={6} minZoom={5} maxZoom={14} scrollWheelZoom className="h-full w-full" ref={setMap}>
            <MapController onMapReady={setMap} onLocate={() => undefined} />
            <TileLayer key={theme} url={theme === "dark" ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"} attribution='&copy; OpenStreetMap contributors &copy; CARTO' eventHandlers={{ tileerror: () => setError("Base map tiles could not be loaded.") }} />
            {showDistricts && districtFeatures && <GeoJSON data={districtFeatures} style={districtStyle} onEachFeature={(feature, layer) => { layer.on({ mouseover: (event) => event.target.setStyle({ weight: 2, fillOpacity: 0.65 }), mouseout: (event) => event.target.setStyle(districtStyle(feature)), click: () => { districtClick(feature); map?.fitBounds((layer as L.Polygon).getBounds(), { padding: [20, 20] }); } }); const district = feature.properties?.district as OfficerMapDistrict | undefined; layer.bindTooltip(`${district?.district ?? feature.properties?.NAME_2 ?? "District"} · ${district?.total ?? 0} cases · ${district?.dominant_disease ?? "No dominant disease"} · ${district?.max_risk ?? "LOW"}`); }} />}
            {data && <MapLayers data={data} showClusters={showClusters} showHeatmap={showHeatmap} onPointSelect={setSelectedPoint} onClusterSelect={setSelectedPoint} onValidatePoint={onValidatePoint} onChatPoint={onChatPoint} />}
          </MapContainer>
          <div className="absolute bottom-3 left-3 z-[400] rounded-lg border border-white/10 bg-[#202721]/95 p-3 text-xs text-stone-300">
            <p className="mb-2 font-semibold text-stone-100">Risk legend</p>
            {Object.entries(RISK_COLORS).map(([risk, color]) => <div key={risk} className="flex items-center gap-2"><span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />{risk}</div>)}
            <label className="mt-2 flex items-center gap-2"><input type="checkbox" checked={showClusters} onChange={(event) => setShowClusters(event.target.checked)} />Clusters</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={showHeatmap} onChange={(event) => setShowHeatmap(event.target.checked)} />Heatmap</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={showDistricts} onChange={(event) => setShowDistricts(event.target.checked)} />Districts</label>
          </div>
        </div>
      )}

      {gisError && <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">Government GIS could not be loaded. <a className="font-semibold underline" href="https://stategisportal.nic.in/stategisportal/Home/Map/27" target="_blank" rel="noopener noreferrer">Open in new tab</a></div>}

      {(selectedDistrict || selectedPoint) && (
        <aside className="rounded-lg border border-white/10 bg-[#202721] p-5 text-sm text-stone-300 lg:fixed lg:right-6 lg:top-24 lg:z-[450] lg:w-[360px] lg:shadow-2xl">
          <div className="flex items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wider text-emerald-300">{selectedDistrict ? "District details" : "Priority case"}</p><h3 className="mt-1 text-lg font-semibold text-stone-100">{selectedDistrict?.district ?? selectedPoint?.farm_name}</h3></div><button type="button" aria-label="Close details" onClick={() => { setSelectedDistrict(null); setSelectedPoint(null); }} className="map-icon-button">×</button></div>
          {selectedPoint && <div className="mt-4 space-y-1"><p>{selectedPoint.crop} · {selectedPoint.disease}</p><p>Risk: <strong style={{ color: RISK_COLORS[selectedPoint.risk] }}>{selectedPoint.risk}</strong></p><p>Confidence: {selectedPoint.confidence.toFixed(1)}%</p><p>Distance: {selectedPoint.distance_km.toFixed(1)} km</p><div className="mt-3 flex gap-2"><button type="button" onClick={() => onValidatePoint?.(selectedPoint)} className="map-button">Validate</button><button type="button" onClick={() => onChatPoint?.(selectedPoint)} className="map-button">Chat</button></div></div>}
          {selectedDistrict && data && <div className="mt-4 space-y-3"><p>{selectedDistrict.total} cases · dominant disease: {selectedDistrict.dominant_disease}</p><div><p className="mb-1 text-xs text-stone-500">Top diseases</p>{selectedDistrict.top_diseases.map((disease) => <div key={disease.name} className="flex justify-between"><span>{disease.name}</span><span>{disease.count}</span></div>)}</div><div><p className="mb-1 text-xs text-stone-500">30-day case trend</p><div className="flex h-12 items-end gap-0.5">{selectedTrend.map((day) => <span key={day.date} className="flex-1 bg-emerald-500/60" style={{ height: `${Math.max(4, day.count * 8)}%` }} title={`${day.date}: ${day.count}`} />)}</div></div><div><p className="mb-1 text-xs text-stone-500">Highest-priority cases</p>{priorityCases.map((point) => <button type="button" key={point.id} onClick={() => setSelectedPoint(point)} className="block w-full truncate py-1 text-left text-emerald-300 hover:text-emerald-200">{point.farm_name} · {point.risk}</button>)}</div><button type="button" onClick={() => setFilters((current) => ({ ...current, district: selectedDistrict.district }))} className="map-button w-full">View all in queue</button></div>}
        </aside>
      )}
    </div>
  );
}