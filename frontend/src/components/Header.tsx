/**
 * SafeRoute AI — Header Navigation Bar
 * Course Outcome Mapping:
 * - CO1: Goal-Based Agent PEAS Controls & System Status
 * - CO2-CO5: Viva topic indicators and presentation triggers
 */

import React from 'react';
import { Shield, Sparkles, RefreshCw, GitCompare, Pause, Square } from 'lucide-react';
import { USE_MOCK } from '../api/client';

interface HeaderProps {
  compareRoutes: boolean;
  onToggleCompare: (val: boolean) => void;
  isDemoActive: boolean;
  demoStepIndex: number;
  demoTotalSteps: number;
  demoStepName?: string;
  onToggleDemo: () => void;
  onStopDemo: () => void;
  onReset: () => void;
  isCalculating: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  compareRoutes,
  onToggleCompare,
  isDemoActive,
  demoStepIndex,
  demoTotalSteps,
  demoStepName,
  onToggleDemo,
  onStopDemo,
  onReset,
  isCalculating,
}) => {
  return (
    <header className="relative z-30 bg-surface border-b border-hairline px-4 md:px-6 py-3 flex flex-wrap items-center justify-between gap-3 shadow-sm">
      {/* Brand & Title */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-brand flex items-center justify-center text-white shadow-sm ring-2 ring-brand-surface">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-ink font-sans">
              SafeRoute <span className="text-brand">AI</span>
            </h1>
            <span className="hidden sm:inline-block px-2 py-0.5 text-[11px] font-bold rounded-sm bg-canvas text-body border border-hairline">
              Micro Project 14
            </span>
            <span
              className={`px-2 py-0.5 text-[11px] font-bold rounded-sm border ${
                USE_MOCK
                  ? 'bg-discount-surface text-brand-strong border-brand-strong/30'
                  : 'bg-warm/10 text-warm border-warm/30'
              }`}
              title={USE_MOCK ? 'Simulated API Mock Engine Active (src/api/mock.ts)' : 'Live Django REST API'}
            >
              {USE_MOCK ? 'Mock API Engine' : 'Live Django API'}
            </span>
          </div>
          <p className="text-xs text-body font-medium hidden md:block">
            Risk-Aware Routing via Causal Inference & Dynamic Pathfinding
          </p>
        </div>
      </div>

      {/* CO Badges for Viva presentation */}
      <div className="hidden lg:flex items-center gap-1.5">
        <span
          className="px-2 py-0.5 text-[10px] font-bold rounded-sm bg-canvas text-body border border-hairline hover:bg-brand-surface hover:text-brand-strong transition-colors cursor-help"
          title="CO1: Goal-Based Utility Agent with PEAS profile balancing travel time and accident risk"
        >
          CO1: PEAS Agent
        </span>
        <span
          className="px-2 py-0.5 text-[10px] font-bold rounded-sm bg-canvas text-body border border-hairline hover:bg-brand-surface hover:text-brand-strong transition-colors cursor-help"
          title="CO2: Risk-Aware A* Search with Admissible Haversine Heuristic vs Dijkstra Baseline"
        >
          CO2: A* Search
        </span>
        <span
          className="px-2 py-0.5 text-[10px] font-bold rounded-sm bg-canvas text-body border border-hairline hover:bg-brand-surface hover:text-brand-strong transition-colors cursor-help"
          title="CO3: Forward-Chaining Production Rules for Speed Advisories & Underwriting Tiers"
        >
          CO3: Expert Rules
        </span>
        <span
          className="px-2 py-0.5 text-[10px] font-bold rounded-sm bg-canvas text-body border border-hairline hover:bg-brand-surface hover:text-brand-strong transition-colors cursor-help"
          title="CO4: Bayesian Network DAG with pgmpy for Causal Marginal Inference under Uncertainty"
        >
          CO4: Bayesian DAG
        </span>
        <span
          className="px-2 py-0.5 text-[10px] font-bold rounded-sm bg-canvas text-body border border-hairline hover:bg-brand-surface hover:text-brand-strong transition-colors cursor-help"
          title="CO5: Supervised XGBoost Classifier trained on US Accidents dataset for calibrated baseline probability"
        >
          CO5: XGBoost
        </span>
      </div>

      {/* Action Controls & Toggles */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* Compare Toggle Pill */}
        <button
          onClick={() => onToggleCompare(!compareRoutes)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all border ${
            compareRoutes
              ? 'bg-ink text-surface border-ink shadow-sm'
              : 'bg-surface text-body border-hairline hover:border-body'
          }`}
          title="Toggle display of Fastest Route (gray dashed) alongside Safest Route (solid green)"
        >
          <GitCompare className="w-3.5 h-3.5" />
          <span>Compare: Fastest vs Safest</span>
          <span
            className={`w-2 h-2 rounded-full ${compareRoutes ? 'bg-brand' : 'bg-muted'}`}
          />
        </button>

        {/* Demo Mode Button */}
        <div className="flex items-center rounded-full border border-hairline bg-surface p-0.5 shadow-sm">
          <button
            onClick={onToggleDemo}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold transition-all ${
              isDemoActive
                ? 'bg-warm text-white animate-pulse'
                : 'bg-canvas text-ink hover:bg-brand-surface hover:text-brand-strong'
            }`}
            title="Auto-play presentation demo: Clear Day → Heavy Rain → Dense Fog at Night"
          >
            {isDemoActive ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Demo ({demoStepIndex + 1}/{demoTotalSteps})</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-warm" />
                <span>Demo mode</span>
              </>
            )}
          </button>
          {isDemoActive && (
            <button
              onClick={onStopDemo}
              className="p-1 text-body hover:text-hot hover:bg-canvas rounded-full transition-colors ml-1"
              title="Stop Demo"
            >
              <Square className="w-3 h-3 fill-current" />
            </button>
          )}
        </div>

        {/* Reset Button */}
        <button
          onClick={onReset}
          disabled={isCalculating}
          className="flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold bg-surface text-body border border-hairline hover:text-ink hover:border-body transition-colors disabled:opacity-50"
          title="Reset environmental sliders and origin/destination coordinates"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isCalculating ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>

      {/* Demo Active Sub-banner */}
      {isDemoActive && demoStepName && (
        <div className="w-full bg-warning-surface border border-warning-text/20 rounded-md px-3 py-1.5 flex items-center justify-between text-xs text-warning-text font-bold animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-warm animate-ping" />
            <span>Active Demo Scenario: {demoStepName}</span>
          </div>
          <span className="text-[11px] font-medium opacity-80">
            Auto-stepping every 4.5 seconds for viva evaluator
          </span>
        </div>
      )}
    </header>
  );
};
