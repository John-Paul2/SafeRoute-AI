/**
 * SafeRoute AI — Full-Bleed Leaflet Map View
 * Course Outcome Mapping:
 * - CO1: Agent Spatial Environment Visualization
 * - CO2: Risk-Aware A* path (solid #30a83c) vs Dijkstra (gray dashed)
 * - DESIGN.md: Cold→Warm→Hot translucent high-risk hazard zones
 */

import React, { useEffect, useMemo, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Polyline,
  Circle,
  Marker,
  Popup,
  useMapEvents,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import type { RouteResponse, HighRiskZone } from '../api/types';
import { Shield, Zap, AlertTriangle, MapPin } from 'lucide-react';

interface MapViewProps {
  routeData: RouteResponse | null;
  origin: [number, number];
  destination: [number, number];
  onMapClickCoordinates: (lat: number, lng: number) => void;
  showFastestComparison: boolean;
  cityCenter: [number, number];
  zoom: number;
  isCalculating?: boolean;
}

// Custom vector pins for Origin (A) and Destination (B)
const createPinIcon = (label: 'A' | 'B', color: string) => {
  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="
        background-color: ${color};
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.35);
        border: 2px solid #ffffff;
      ">
        <span style="transform: rotate(45deg); font-weight: 700; font-size: 14px; font-family: Mulish, sans-serif;">
          ${label}
        </span>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30],
  });
};

// Map click event listener component
const MapClickHandler: React.FC<{ onCoordSelected: (lat: number, lng: number) => void }> = ({
  onCoordSelected,
}) => {
  useMapEvents({
    click(e) {
      onCoordSelected(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

// Auto-pan / fit bounds when routes change
const MapBoundsController: React.FC<{
  coords: [number, number][];
}> = ({ coords }) => {
  const map = useMap();

  useEffect(() => {
    if (coords && coords.length > 1) {
      const bounds = L.latLngBounds(coords.map((c) => L.latLng(c[0], c[1])));
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 15 });
    }
  }, [coords, map]);

  return null;
};

export const MapView: React.FC<MapViewProps> = ({
  routeData,
  origin,
  destination,
  onMapClickCoordinates,
  showFastestComparison,
  cityCenter,
  zoom,
  isCalculating = false,
}) => {
  const [clickStep, setClickStep] = useState<'origin' | 'dest'>('origin');

  const originIcon = useMemo(() => createPinIcon('A', '#30a83c'), []);
  const destIcon = useMemo(() => createPinIcon('B', '#ce1736'), []);

  const handleCoordinateClick = (lat: number, lng: number) => {
    onMapClickCoordinates(lat, lng);
    setClickStep((prev) => (prev === 'origin' ? 'dest' : 'origin'));
  };

  // Get color for high-risk zones (cold #034eb1 -> warm #fb6001 -> hot #ce1736)
  const getZoneColor = (severity: HighRiskZone['severity']) => {
    switch (severity) {
      case 'hot':
        return '#ce1736';
      case 'warm':
        return '#fb6001';
      case 'cold':
      default:
        return '#034eb1';
    }
  };

  const safeCoords = routeData?.safe_route?.coordinates || [];
  const fastestCoords = routeData?.fastest_route?.coordinates || [];
  const allCoords = useMemo(
    () => [...safeCoords, ...fastestCoords, origin, destination],
    [safeCoords, fastestCoords, origin, destination]
  );

  return (
    <div className="relative w-full h-full overflow-hidden select-none">
      {/* Interactive Helper Banner on Top of Map */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] pointer-events-none flex flex-col items-center gap-1.5">
        <div className="px-3.5 py-1.5 rounded-full bg-surface/95 backdrop-blur-sm border border-hairline shadow-md text-xs font-bold text-ink flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-brand" />
          <span>
            {clickStep === 'origin'
              ? 'Click map to set Origin (A)'
              : 'Click map to set Destination (B)'}
          </span>
          <span className="text-[10px] text-body font-mono">
            [Click to toggle]
          </span>
        </div>

        {isCalculating && (
          <div className="px-3 py-1 rounded-full bg-brand text-white shadow-lg text-[11px] font-bold flex items-center gap-1.5 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            <span>Calculating Risk-Weighted A* Path...</span>
          </div>
        )}
      </div>

      {/* Map Legend */}
      <div className="absolute bottom-6 left-6 z-[1000] bg-surface/95 backdrop-blur-sm border border-hairline rounded-md p-3 shadow-md text-xs font-sans max-w-xs pointer-events-auto">
        <div className="font-bold text-ink mb-1.5 pb-1 border-b border-hairline flex items-center justify-between">
          <span>Map Legend</span>
          <span className="text-[10px] text-muted uppercase">CO2 • Layers</span>
        </div>

        <div className="flex flex-col gap-1.5">
          {/* Safe Route */}
          <div className="flex items-center gap-2">
            <div className="w-5 h-1 bg-[#30a83c] rounded" />
            <span className="text-body font-bold text-[11px]">
              Safest Route (Risk-Weighted A*)
            </span>
          </div>

          {/* Fastest Route */}
          {showFastestComparison && (
            <div className="flex items-center gap-2">
              <div className="w-5 h-1 border-t-2 border-dashed border-[#6b6d70]" />
              <span className="text-body font-bold text-[11px]">
                Fastest Route (Dijkstra Baseline)
              </span>
            </div>
          )}

          {/* Risk Zones */}
          <div className="flex items-center gap-2 pt-1 border-t border-hairline/60">
            <div className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#034eb1] opacity-70" title="Cold" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#fb6001] opacity-70" title="Warm" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#ce1736] opacity-70" title="Hot" />
            </div>
            <span className="text-body text-[10px]">
              High-Risk Zones (Cold → Warm → Hot)
            </span>
          </div>
        </div>
      </div>

      {/* React Leaflet Map */}
      <MapContainer
        center={cityCenter}
        zoom={zoom}
        zoomControl={true}
        className="w-full h-full"
      >
        {/* Free standard OpenStreetMap tiles (100% free, no API key required) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <MapClickHandler onCoordSelected={handleCoordinateClick} />
        <MapBoundsController coords={allCoords} />

        {/* High Risk Overlay Zones (Cold -> Warm -> Hot) */}
        {routeData?.high_risk_zones.map((zone) => {
          const zoneColor = getZoneColor(zone.severity);
          return (
            <Circle
              key={zone.id}
              center={[zone.lat, zone.lng]}
              radius={zone.radius}
              pathOptions={{
                fillColor: zoneColor,
                fillOpacity: zone.severity === 'hot' ? 0.35 : 0.22,
                color: zoneColor,
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="font-sans text-xs p-1">
                  <div className="flex items-center gap-1 font-bold text-ink mb-1">
                    <AlertTriangle className="w-3.5 h-3.5" style={{ color: zoneColor }} />
                    <span>{zone.location_name}</span>
                  </div>
                  <div className="text-[11px] text-body mb-1">
                    {zone.cause}
                  </div>
                  <div className="flex justify-between text-[10px] font-mono border-t border-hairline pt-1">
                    <span>Accident Hazard Index:</span>
                    <strong style={{ color: zoneColor }}>
                      {(zone.risk_score * 100).toFixed(0)}%
                    </strong>
                  </div>
                </div>
              </Popup>
            </Circle>
          );
        })}

        {/* Fastest Route (Gray Dashed Line) */}
        {showFastestComparison && fastestCoords.length > 0 && (
          <Polyline
            positions={fastestCoords}
            pathOptions={{
              color: '#6b6d70',
              weight: 4,
              opacity: 0.85,
              dashArray: '8, 8',
              className: 'animated-dashed-line',
            }}
          >
            <Popup>
              <div className="font-sans text-xs">
                <strong className="text-body flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5 text-warm" />
                  Fastest Route (Dijkstra)
                </strong>
                <p className="text-[11px] text-body mt-0.5">
                  Direct distance path through congested I-35 intersections.
                </p>
              </div>
            </Popup>
          </Polyline>
        )}

        {/* Safe Route (Solid #30a83c Deal Green) */}
        {safeCoords.length > 0 && (
          <Polyline
            key={`safe-route-${safeCoords.length}-${safeCoords[0]?.[0]}`}
            positions={safeCoords}
            pathOptions={{
              color: '#30a83c',
              weight: 5.5,
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round',
              className: 'route-polyline-safe',
            }}
          >
            <Popup>
              <div className="font-sans text-xs">
                <strong className="text-brand-strong flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5 text-brand" />
                  Safest Route (Risk-Weighted A*)
                </strong>
                <p className="text-[11px] text-body mt-0.5">
                  Circumvents high-risk collision junctions to minimize accident exposure.
                </p>
              </div>
            </Popup>
          </Polyline>
        )}

        {/* Origin Marker (A) */}
        <Marker position={origin} icon={originIcon}>
          <Popup>
            <div className="font-sans text-xs">
              <strong className="text-brand-strong">Point A (Origin)</strong>
              <div className="text-[10px] text-body font-mono">
                {origin[0].toFixed(5)}, {origin[1].toFixed(5)}
              </div>
            </div>
          </Popup>
        </Marker>

        {/* Destination Marker (B) */}
        <Marker position={destination} icon={destIcon}>
          <Popup>
            <div className="font-sans text-xs">
              <strong className="text-hot">Point B (Destination)</strong>
              <div className="text-[10px] text-body font-mono">
                {destination[0].toFixed(5)}, {destination[1].toFixed(5)}
              </div>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};
