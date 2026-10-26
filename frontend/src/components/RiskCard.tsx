/**
 * SafeRoute AI — Live Accident Risk Card (Right Column 1)
 * Course Outcome Mapping:
 * - CO5: Supervised ML (XGBoost) Risk Probability & Feature Importance
 * - DESIGN.md: Temperature-Control Pill (Cold Blue #034eb1 → Hot Red #ce1736 with live risk %)
 */

import React from 'react';
import { ArrowDown, ArrowUp, AlertTriangle, ShieldCheck, Flame, Info } from 'lucide-react';
import type { PredictResponse } from '../api/types';

interface RiskCardProps {
  predict: PredictResponse | null;
  isLoading: boolean;
}

export const RiskCard: React.FC<RiskCardProps> = ({ predict, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 animate-pulse flex flex-col gap-3 font-sans">
        <div className="flex items-center justify-between pb-2 border-b border-hairline">
          <div className="h-4 bg-canvas rounded w-1/3" />
          <div className="h-4 bg-canvas rounded w-16" />
        </div>
        <div className="h-12 bg-canvas rounded-full w-3/4 mx-auto" />
        <div className="h-3 bg-canvas rounded w-2/3 mx-auto" />
        <div className="grid grid-cols-2 gap-2 mt-2">
          <div className="h-10 bg-canvas rounded" />
          <div className="h-10 bg-canvas rounded" />
        </div>
      </div>
    );
  }

  if (!predict) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col items-center justify-center text-center gap-2 font-sans text-xs">
        <AlertTriangle className="w-8 h-8 text-warm opacity-80" />
        <h4 className="font-bold text-ink">No Risk Prediction Available</h4>
        <p className="text-body text-[11px]">
          Adjust environmental sensors or click &quot;Recalculate Route &amp; Risk&quot; to evaluate.
        </p>
      </div>
    );
  }

  const { risk_percentage, xgboost_risk, risk_level, feature_contributions } = predict;

  // Temperature color logic: cold-blue (#034eb1) -> warm (#fb6001) -> hot-red (#ce1736)
  const getTempColor = (pct: number) => {
    if (pct < 30) return '#034eb1'; // cold blue
    if (pct < 65) return '#fb6001'; // warm orange
    return '#ce1736'; // hot red
  };

  const tempColor = getTempColor(risk_percentage);

  // Status icon based on severity
  const getStatusIcon = () => {
    if (risk_percentage < 30) {
      return <ShieldCheck className="w-4 h-4 text-brand" />;
    }
    if (risk_percentage < 65) {
      return <AlertTriangle className="w-4 h-4 text-warm" />;
    }
    return <Flame className="w-4 h-4 text-hot" />;
  };

  return (
    <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col gap-3 text-ink font-sans">
      {/* Card Header with CO badge */}
      <div className="flex items-center justify-between pb-2 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          {getStatusIcon()}
          <h3 className="text-sm font-bold text-ink">Live Accident Risk Score</h3>
        </div>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-brand-surface text-brand-strong"
          title="CO5: Supervised XGBoost Classifier with Platt Calibration"
        >
          CO5 XGBoost
        </span>
      </div>

      {/* Signature Temperature-Control Pill from DESIGN.md */}
      <div className="flex flex-col items-center justify-center py-2">
        <div
          className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-hairline bg-surface shadow-sm transition-all duration-300"
          style={{ borderColor: `${tempColor}40` }}
        >
          {/* Cold Blue Arrow Down */}
          <div
            className="flex items-center text-cold"
            title="Cold baseline (< 30% risk)"
          >
            <ArrowDown className="w-4 h-4 text-cold stroke-[2.5]" />
          </div>

          {/* Live Risk % Metric with Dynamic Temperature Color */}
          <div className="flex items-baseline gap-1">
            <span
              className="text-2xl font-bold tracking-tight transition-colors duration-300"
              style={{ color: tempColor }}
            >
              {risk_percentage}°
            </span>
            <span
              className="text-xs font-bold uppercase tracking-wider"
              style={{ color: tempColor }}
            >
              {risk_level} Risk
            </span>
          </div>

          {/* Hot Red Arrow Up */}
          <div
            className="flex items-center text-hot"
            title="Hot high-danger peak (> 65% risk)"
          >
            <ArrowUp className="w-4 h-4 text-hot stroke-[2.5]" />
          </div>
        </div>

        {/* Temperature Spectrum Bar */}
        <div className="w-full mt-3">
          <div className="w-full h-2 rounded-full bg-canvas border border-hairline overflow-hidden p-0.5">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${risk_percentage}%`,
                background: `linear-gradient(90deg, #034eb1 0%, #fb6001 50%, #ce1736 100%)`,
              }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-muted mt-1 font-mono">
            <span>0° (Safe)</span>
            <span>50° (Elevated)</span>
            <span>100° (Severe)</span>
          </div>
        </div>
      </div>

      {/* Probability Calibration Metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-canvas rounded-sm p-2 border border-hairline">
          <span className="text-[10px] text-muted uppercase font-bold block">
            Calibrated P(Accident)
          </span>
          <span className="text-sm font-bold text-ink font-mono">
            {xgboost_risk.toFixed(3)}
          </span>
        </div>
        <div className="bg-canvas rounded-sm p-2 border border-hairline">
          <span className="text-[10px] text-muted uppercase font-bold block">
            Risk Tier Category
          </span>
          <span
            className="text-sm font-bold font-mono"
            style={{ color: tempColor }}
          >
            {risk_level} Severity
          </span>
        </div>
      </div>

      {/* Top Feature Contributions */}
      {feature_contributions && (
        <div className="flex flex-col gap-1 pt-1 border-t border-hairline text-xs">
          <div className="flex items-center justify-between text-[11px] text-muted font-bold">
            <span>SHAP Impact Factors</span>
            <Info className="w-3 h-3 text-muted" />
          </div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(feature_contributions).map(([feature, weight]) => (
              <span
                key={feature}
                className="px-2 py-0.5 rounded-sm bg-canvas border border-hairline text-[10px] font-bold text-body"
              >
                {feature}: <span className="text-ink font-mono">{weight > 0 ? `+${weight}` : weight}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
