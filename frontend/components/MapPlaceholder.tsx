/**
 * MapPlaceholder — scaffolds the slot where MapLibre GL will be mounted.
 * To activate:
 *   1. npm install maplibre-gl
 *   2. Import and initialise a MapLibre map in a useEffect
 *   3. Remove this placeholder div
 */
interface MapPlaceholderProps {
  label?: string;
}

export default function MapPlaceholder({ label = "MapLibre GL Map" }: MapPlaceholderProps) {
  return (
    <div
      id="map-container"
      className="w-full h-full bg-slate-800/50 rounded-xl border border-white/5 flex items-center justify-center"
    >
      <div className="text-center text-slate-500 select-none">
        <div className="text-5xl mb-3">🗺️</div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs mt-1 text-slate-600">Scaffold ready · wire up MapLibre tiles</p>
      </div>
    </div>
  );
}
