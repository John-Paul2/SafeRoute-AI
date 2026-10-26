/**
 * SafeRoute AI — Route Comparison Card (Right Column 4)
 * Course Outcome Mapping:
 * - CO2: Informed A* Search vs Uninformed Dijkstra Baseline
 * - DESIGN.md: Mint Discount-Badge (#defde4 / #197e25) showing "−X% risk exposure" and deltas
 */

import React from 'react';
import { GitCompare, Shield, Zap, TrendingDown, Clock, Navigation } from 'lucide-react';
import type { RouteResponse } from '../api/types';

interface RouteComparisonCardProps {
  routeData: RouteResponse | null;
  isLoading: boolean;
}

export const RouteComparisonCard: React.FC<RouteComparisonCardProps> = ({
  routeData,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 animate-pulse flex flex-col gap-3 font-sans">
        <div className="flex items-center justify-between pb-2 border-b border-hairline">
          <div className="h-4 bg-canvas rounded w-1/3" />
          <div className="h-4 bg-canvas rounded w-20" />
        </div>
        <div className="h-12 bg-canvas rounded" />
        <div className="grid grid-cols-2 gap-2">
          <div className="h-20 bg-canvas rounded" />
          <div className="h-20 bg-canvas rounded" />
        </div>
      </div>
    );
  }

  if (!routeData) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col items-center justify-center text-center gap-2 font-sans text-xs">
        <Navigation className="w-6 h-6 text-brand opacity-80" />
        <h4 className="font-bold text-ink">No Navigable Route Calculated</h4>
        <p className="text-body text-[11px]">
          Select an Origin and Destination on the Austin map to run the risk-weighted A* algorithm.
        </p>
      </div>
    );
  }

  const { safe_route, fastest_route, comparison } = routeData;

  return (
    <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col gap-3 text-ink font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          <GitCompare className="w-4 h-4 text-brand" />
          <h3 className="text-sm font-bold text-ink">Route Comparison</h3>
        </div>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-brand-surface text-brand-strong"
          title="CO2: Admissible A* Search with Haversine Heuristic"
        >
          CO2 A* vs Dijkstra
        </span>
      </div>

      {/* Signature Mint Discount-Badge from DESIGN.md */}
      <div className="flex items-center justify-between bg-discount-surface border border-brand/20 rounded-sm p-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-brand-strong text-white flex items-center justify-center shrink-0">
            <TrendingDown className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-strong block">
              Safety Advantage
            </span>
            <span className="text-lg font-bold text-brand-strong tracking-tight">
              −{comparison.risk_reduction_percent}% Risk Exposure
            </span>
          </div>
        </div>

        {/* Trade-off summary */}
        <div className="text-right text-[11px] font-medium text-brand-strong">
          <div className="font-bold">+{comparison.distance_delta_miles} mi</div>
          <div className="text-[10px] opacity-80">+{comparison.duration_delta_minutes} min</div>
        </div>
      </div>

      {/* Side-by-Side Route Metrics */}
      <div className="grid grid-cols-2 gap-2.5 text-xs">
        {/* Safest Route (A*) */}
        <div className="bg-canvas rounded-md p-2.5 border border-brand/40 flex flex-col gap-2 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-brand" />
          <div className="flex items-center gap-1.5 pt-0.5">
            <span className="w-2.5 h-2.5 rounded-full bg-brand shrink-0" />
            <span className="font-bold text-ink truncate">Safest (A*)</span>
          </div>

          <div className="flex flex-col gap-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Navigation className="w-3 h-3 text-brand" /> Dist:
              </span>
              <span className="font-bold font-mono">{safe_route.distance_miles} mi</span>
            </div>
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Clock className="w-3 h-3 text-brand" /> Time:
              </span>
              <span className="font-bold font-mono">{safe_route.duration_minutes} min</span>
            </div>
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Shield className="w-3 h-3 text-brand" /> Risk:
              </span>
              <span className="font-bold font-mono text-brand-strong">
                {safe_route.total_risk_score.toFixed(2)}
              </span>
            </div>
          </div>

          {safe_route.summary_street && (
            <div className="text-[10px] text-body italic truncate border-t border-hairline pt-1">
              {safe_route.summary_street}
            </div>
          )}
        </div>

        {/* Fastest Route (Dijkstra) */}
        <div className="bg-canvas rounded-md p-2.5 border border-hairline flex flex-col gap-2 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-body" />
          <div className="flex items-center gap-1.5 pt-0.5">
            <span className="w-2.5 h-2.5 rounded-full bg-body border border-surface shrink-0" />
            <span className="font-bold text-body truncate">Fastest (Dijkstra)</span>
          </div>

          <div className="flex flex-col gap-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Navigation className="w-3 h-3 text-body" /> Dist:
              </span>
              <span className="font-bold font-mono">{fastest_route.distance_miles} mi</span>
            </div>
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Clock className="w-3 h-3 text-body" /> Time:
              </span>
              <span className="font-bold font-mono">{fastest_route.duration_minutes} min</span>
            </div>
            <div className="flex justify-between">
              <span className="text-body flex items-center gap-1">
                <Zap className="w-3 h-3 text-warm" /> Risk:
              </span>
              <span className="font-bold font-mono text-hot">
                {fastest_route.total_risk_score.toFixed(2)}
              </span>
            </div>
          </div>

          {fastest_route.summary_street && (
            <div className="text-[10px] text-body italic truncate border-t border-hairline pt-1">
              {fastest_route.summary_street}
            </div>
          )}
        </div>
      </div>

      {/* Delta explanation */}
      <div className="text-[11px] text-body leading-relaxed bg-canvas/50 p-2 rounded-sm border border-hairline">
        The A* agent accepted a minor <strong className="text-ink">+{comparison.distance_delta_miles} mi</strong> detour to circumvent the I-35 accident bottlenecks, slashing collision risk by <strong className="text-brand-strong">{comparison.risk_reduction_percent}%</strong>.
      </div>
    </div>
  );
};
