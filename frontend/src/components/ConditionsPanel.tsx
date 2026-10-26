/**
 * SafeRoute AI — Conditions Control Panel (Left Column)
 * Course Outcome Mapping:
 * - CO1: Goal-Based Agent Environment Perception & Actuator Inputs
 * - CO2: Safety vs Speed Trade-off Parameter (Lambda λ) configuration
 * - CO4: Bayesian Network evidence injection
 * - CO5: Real-time feature vectors for XGBoost predictive inference
 */

import React from 'react';
import {
  CloudRain,
  Eye,
  Activity,
  Clock,
  SlidersHorizontal,
  Navigation,
  MapPin,
  Compass,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import type { EnvironmentalConditions, DemoStep } from '../api/types';
import { PRESET_LOCATIONS, DEMO_SCENARIOS } from '../api/mock';

interface ConditionsPanelProps {
  conditions: EnvironmentalConditions;
  onChange: (updated: Partial<EnvironmentalConditions>) => void;
  onCalculateRoute: () => void;
  onReset: () => void;
  origin: [number, number];
  destination: [number, number];
  originName?: string;
  destinationName?: string;
  onSelectPreset: (
    origin: [number, number],
    dest: [number, number],
    originName: string,
    destName: string
  ) => void;
  onSelectScenario?: (scenario: DemoStep) => void;
  isCalculating: boolean;
}

export const ConditionsPanel: React.FC<ConditionsPanelProps> = ({
  conditions,
  onChange,
  onCalculateRoute,
  onReset,
  origin,
  destination,
  originName = 'Downtown Austin',
  destinationName = 'UT Austin Campus',
  onSelectPreset,
  onSelectScenario,
  isCalculating,
}) => {
  const weatherOptions: EnvironmentalConditions['weather_condition'][] = [
    'Clear',
    'Rain',
    'Fog',
    'Snow',
    'Other',
  ];

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 === 0 ? 12 : hour % 12;
    return `${hour.toString().padStart(2, '0')}:00 (${displayHour} ${period})`;
  };

  return (
    <aside className="w-full md:w-[350px] lg:w-[380px] bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col gap-4 text-ink font-sans max-h-[calc(100vh-100px)] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-hairline">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-brand" />
          <h2 className="text-sm font-bold tracking-tight text-ink">
            Environmental Sensors & Controls
          </h2>
        </div>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-brand-surface text-brand-strong"
          title="CO1 Agent Perception Vector"
        >
          CO1 • CO5
        </span>
      </div>

      {/* Saved Demo Scenarios Seed (1-Click Evaluation) */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-bold text-body flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-brand" />
            <span>Saved Demo Scenarios</span>
          </span>
          <span className="text-[10px] text-brand-strong font-bold bg-brand-surface px-1 rounded">
            3 Seeds
          </span>
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          {DEMO_SCENARIOS.map((scen, idx) => (
            <button
              key={scen.id}
              type="button"
              onClick={() => {
                if (onSelectScenario) {
                  onSelectScenario(scen);
                } else {
                  onChange(scen.conditions);
                }
              }}
              className="p-1.5 text-[10px] font-bold rounded-sm border border-hairline bg-canvas hover:bg-discount-surface hover:border-brand text-ink text-center transition-all truncate shadow-2xs"
              title={`${scen.name}: ${scen.description}`}
            >
              {idx === 0 ? '☀️ Clear' : idx === 1 ? '🌧️ Heavy Rain' : '🌫️ Fog Night'}
            </button>
          ))}
        </div>
      </div>

      {/* Preset Corridors in Target City (Austin, TX) */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-bold text-body flex items-center gap-1">
          <Compass className="w-3.5 h-3.5 text-brand" />
          <span>Austin, TX Preset Corridors</span>
        </label>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            type="button"
            onClick={() =>
              onSelectPreset(
                PRESET_LOCATIONS.austin_downtown.coords,
                PRESET_LOCATIONS.austin_ut.coords,
                'Downtown Austin',
                'UT Austin Campus'
              )
            }
            className="px-2.5 py-1.5 text-[11px] font-bold rounded-sm border border-hairline bg-canvas hover:bg-surface hover:border-brand text-ink text-left transition-colors truncate"
            title="Downtown 6th St to UT Austin (I-35 bottleneck vs Lavaca Safe Corridor)"
          >
            Downtown → UT Campus
          </button>
          <button
            type="button"
            onClick={() =>
              onSelectPreset(
                PRESET_LOCATIONS.zilker_park.coords,
                PRESET_LOCATIONS.mueller_district.coords,
                'Zilker Park',
                'Mueller District'
              )
            }
            className="px-2.5 py-1.5 text-[11px] font-bold rounded-sm border border-hairline bg-canvas hover:bg-surface hover:border-brand text-ink text-left transition-colors truncate"
            title="Zilker Park to Mueller District via MoPac Expressway bypass"
          >
            Zilker → Mueller
          </button>
        </div>
      </div>

      {/* Origin & Destination Display */}
      <div className="bg-canvas rounded-md p-2.5 border border-hairline flex flex-col gap-2 text-xs">
        <div className="flex items-start gap-2">
          <span className="w-5 h-5 rounded-full bg-brand text-white flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
            A
          </span>
          <div className="flex-1 min-w-0">
            <span className="text-[10px] uppercase font-bold text-muted block">Origin</span>
            <div className="font-bold text-ink truncate">{originName}</div>
            <div className="text-[10px] text-body font-mono">
              {origin[0].toFixed(4)}, {origin[1].toFixed(4)}
            </div>
          </div>
        </div>

        <div className="h-[1px] bg-hairline" />

        <div className="flex items-start gap-2">
          <span className="w-5 h-5 rounded-full bg-hot text-white flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
            B
          </span>
          <div className="flex-1 min-w-0">
            <span className="text-[10px] uppercase font-bold text-muted block">Destination</span>
            <div className="font-bold text-ink truncate">{destinationName}</div>
            <div className="text-[10px] text-body font-mono">
              {destination[0].toFixed(4)}, {destination[1].toFixed(4)}
            </div>
          </div>
        </div>

        <div className="text-[10px] text-body italic pt-1 border-t border-hairline/60 flex items-center gap-1">
          <MapPin className="w-3 h-3 text-muted shrink-0" />
          <span>Click anywhere on the map to re-pin Origin & Destination.</span>
        </div>
      </div>

      {/* Weather Select Chips */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-bold text-body">Weather Condition</label>
        <div className="grid grid-cols-5 gap-1">
          {weatherOptions.map((w) => {
            const isSelected = conditions.weather_condition === w;
            return (
              <button
                key={w}
                type="button"
                onClick={() => onChange({ weather_condition: w })}
                className={`py-1.5 text-xs font-bold rounded-sm border transition-all text-center ${
                  isSelected
                    ? 'bg-ink text-surface border-ink shadow-sm'
                    : 'bg-surface text-body border-hairline hover:border-body'
                }`}
              >
                {w}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sliders Container */}
      <div className="flex flex-col gap-3.5">
        {/* Precipitation Slider */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-body flex items-center gap-1.5">
              <CloudRain className="w-3.5 h-3.5 text-cold" />
              <span>Precipitation</span>
            </span>
            <span className="font-bold text-ink font-mono text-[11px] bg-canvas px-1.5 py-0.5 rounded-sm border border-hairline">
              {conditions.precipitation.toFixed(2)} in/hr
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.05}
            value={conditions.precipitation}
            onChange={(e) => onChange({ precipitation: parseFloat(e.target.value) })}
            className="w-full accent-brand h-1.5 bg-canvas rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>0.00 (Dry)</span>
            <span>0.50 (Moderate)</span>
            <span>1.50 (Deluge)</span>
          </div>
        </div>

        {/* Visibility Slider */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-body flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-body" />
              <span>Visibility</span>
            </span>
            <span className="font-bold text-ink font-mono text-[11px] bg-canvas px-1.5 py-0.5 rounded-sm border border-hairline">
              {conditions.visibility.toFixed(1)} miles
            </span>
          </div>
          <input
            type="range"
            min={0.1}
            max={10.0}
            step={0.1}
            value={conditions.visibility}
            onChange={(e) => onChange({ visibility: parseFloat(e.target.value) })}
            className="w-full accent-brand h-1.5 bg-canvas rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>0.1 mi (Dense Fog)</span>
            <span>5.0 mi</span>
            <span>10.0 mi (Clear Horizon)</span>
          </div>
        </div>

        {/* Traffic Density Slider */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-body flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-warm" />
              <span>Traffic Density</span>
            </span>
            <span className="font-bold text-ink font-mono text-[11px] bg-canvas px-1.5 py-0.5 rounded-sm border border-hairline">
              {conditions.traffic_density}%
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            step={1}
            value={conditions.traffic_density}
            onChange={(e) => onChange({ traffic_density: parseInt(e.target.value, 10) })}
            className="w-full accent-brand h-1.5 bg-canvas rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>0% (Empty)</span>
            <span>50% (Standard)</span>
            <span>100% (Gridlock)</span>
          </div>
        </div>

        {/* Time of Day Slider */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-body flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-body" />
              <span>Time of Day</span>
            </span>
            <span className="font-bold text-ink font-mono text-[11px] bg-canvas px-1.5 py-0.5 rounded-sm border border-hairline">
              {formatHour(conditions.hour)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={23}
            step={1}
            value={conditions.hour}
            onChange={(e) => onChange({ hour: parseInt(e.target.value, 10) })}
            className="w-full accent-brand h-1.5 bg-canvas rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>00:00 (Midnight)</span>
            <span>12:00 (Noon)</span>
            <span>23:00</span>
          </div>
        </div>

        {/* Safety vs Speed Trade-off (Lambda λ) Slider */}
        <div className="flex flex-col gap-1 p-2 bg-brand-surface/40 rounded-md border border-brand/20">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1">
              <span className="font-bold text-brand-strong">Safety Weight (λ)</span>
              <span
                className="text-[9px] font-bold px-1 py-0.2 bg-brand text-white rounded-sm"
                title="CO2 Parameter: edge cost = length * (1 + lambda * edge_risk * env_multiplier)"
              >
                CO2
              </span>
            </div>
            <span className="font-bold text-brand-strong font-mono text-[11px] bg-surface px-1.5 py-0.5 rounded-sm border border-brand/30">
              λ = {conditions.safety_lambda.toFixed(1)}
            </span>
          </div>
          <input
            type="range"
            min={0.0}
            max={5.0}
            step={0.1}
            value={conditions.safety_lambda}
            onChange={(e) => onChange({ safety_lambda: parseFloat(e.target.value) })}
            className="w-full accent-brand-strong h-1.5 bg-brand-surface rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-brand-strong font-medium">
            <span>0.0 (Fastest only)</span>
            <span>1.5 (Balanced)</span>
            <span>5.0 (Max Safe Detour)</span>
          </div>
          <div className="text-[10px] text-body italic font-mono pt-0.5">
            cost = length × (1 + λ × risk × env)
          </div>
        </div>
      </div>

      {/* Pill Buttons: Primary Green & Neutral Outline */}
      <div className="flex flex-col gap-2 pt-2 border-t border-hairline mt-auto">
        <button
          type="button"
          onClick={onCalculateRoute}
          disabled={isCalculating}
          className="w-full py-2.5 px-4 rounded-full bg-brand text-white font-bold text-sm tracking-wide shadow-sm hover:bg-brand-strong active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isCalculating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Calculating A* Route...</span>
            </>
          ) : (
            <>
              <Navigation className="w-4 h-4 fill-current" />
              <span>Find safest route</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onReset}
          disabled={isCalculating}
          className="w-full py-2 px-4 rounded-full bg-surface text-ink border border-hairline font-bold text-xs tracking-wide hover:bg-canvas hover:border-body active:scale-[0.99] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          <RotateCcw className="w-3.5 h-3.5 text-body" />
          <span>Reset</span>
        </button>
      </div>
    </aside>
  );
};
