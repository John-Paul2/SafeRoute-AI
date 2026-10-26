/**
 * SafeRoute AI — Expert Rule Advisories & Underwriting Card (Right Column 3)
 * Course Outcome Mapping:
 * - CO3: Forward-chaining expert knowledge base (Experta) production rules
 * - DESIGN.md: Warning-badge chips (critical = hot red #ce1736, warning = amber #9f5c0c) & Underwriting Tier badge
 */

import React from 'react';
import { BookOpen, AlertOctagon, AlertTriangle, CheckCircle, Award } from 'lucide-react';
import type { RulesResponse } from '../api/types';

interface RuleAdvisoriesCardProps {
  rules: RulesResponse | null;
  isLoading: boolean;
}

export const RuleAdvisoriesCard: React.FC<RuleAdvisoriesCardProps> = ({ rules, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 animate-pulse flex flex-col gap-3 font-sans">
        <div className="flex items-center justify-between pb-2 border-b border-hairline">
          <div className="h-4 bg-canvas rounded w-1/2" />
          <div className="h-4 bg-canvas rounded w-16" />
        </div>
        <div className="h-12 bg-canvas rounded" />
        <div className="h-10 bg-canvas rounded" />
      </div>
    );
  }

  if (!rules) {
    return (
      <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col items-center justify-center text-center gap-2 font-sans text-xs">
        <AlertTriangle className="w-6 h-6 text-warm opacity-80" />
        <h4 className="font-bold text-ink">Rules Knowledge Base Offline</h4>
        <p className="text-body text-[11px]">
          Unable to retrieve production rule advisories. Check backend connection.
        </p>
      </div>
    );
  }

  const { advisories, underwriting_tier } = rules;

  return (
    <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col gap-3 text-ink font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          <BookOpen className="w-4 h-4 text-brand" />
          <h3 className="text-sm font-bold text-ink">Rule Advisories & Underwriting</h3>
        </div>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-brand-surface text-brand-strong"
          title="CO3: Knowledge Representation & Forward-Chaining Inference Rules"
        >
          CO3 Experta
        </span>
      </div>

      {/* Underwriting Tier Badge */}
      <div
        className="rounded-md p-3 border flex items-center justify-between transition-all"
        style={{
          backgroundColor: `${underwriting_tier.color_code}0D`,
          borderColor: `${underwriting_tier.color_code}40`,
        }}
      >
        <div className="flex items-start gap-2.5">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5"
            style={{
              backgroundColor: `${underwriting_tier.color_code}20`,
              color: underwriting_tier.color_code,
            }}
          >
            <Award className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span
                className="font-bold text-sm tracking-tight"
                style={{ color: underwriting_tier.color_code }}
              >
                {underwriting_tier.tier}: {underwriting_tier.name}
              </span>
            </div>
            <p className="text-[11px] text-body mt-0.5 leading-tight">
              {underwriting_tier.rationale}
            </p>
          </div>
        </div>

        {/* Premium Multiplier Pill */}
        <div className="flex flex-col items-end shrink-0 pl-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-sm font-mono"
            style={{
              backgroundColor: underwriting_tier.color_code,
              color: '#ffffff',
            }}
          >
            {underwriting_tier.premium_multiplier.toFixed(2)}x
          </span>
          <span className="text-[10px] text-body font-mono mt-0.5">
            {underwriting_tier.surcharge_percent > 0
              ? `+${underwriting_tier.surcharge_percent}% Premium`
              : 'Base Rate'}
          </span>
        </div>
      </div>

      {/* Production Rule Advisories (Warning-Badge Style Chips) */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-bold text-body">
          Active Production Rule Dispatches ({advisories.length})
        </label>

        <div className="flex flex-col gap-1.5">
          {advisories.length === 0 ? (
            <div className="p-3 rounded-sm bg-discount-surface/60 border border-brand/20 text-xs flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-brand shrink-0" />
              <span className="text-brand-strong font-medium">
                All parameters optimal. No hazardous weather, visibility, or congestion advisories triggered.
              </span>
            </div>
          ) : (
            advisories.map((advisory) => {
            const isCritical = advisory.level === 'critical';
            const isWarning = advisory.level === 'warning';

            return (
              <div
                key={advisory.id}
                className={`p-2.5 rounded-sm border transition-all text-xs flex flex-col gap-1 ${
                  isCritical
                    ? 'bg-[#fde8eb] text-hot border-[#f8b4bc]'
                    : isWarning
                    ? 'bg-warning-surface text-warning-text border-[#f4ea8f]'
                    : 'bg-canvas text-ink border-hairline'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 font-bold">
                    {isCritical ? (
                      <AlertOctagon className="w-4 h-4 text-hot shrink-0" />
                    ) : isWarning ? (
                      <AlertTriangle className="w-4 h-4 text-warning-text shrink-0" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-brand shrink-0" />
                    )}
                    <span className="leading-snug">{advisory.title}</span>
                  </div>

                  <span
                    className={`text-[9px] font-mono font-bold px-1 py-0.2 rounded-xs shrink-0 ${
                      isCritical
                        ? 'bg-hot text-white'
                        : isWarning
                        ? 'bg-[#9f5c0c] text-white'
                        : 'bg-muted text-white'
                    }`}
                  >
                    {advisory.rule_code}
                  </span>
                </div>

                <p className="text-[11px] opacity-90 leading-relaxed pl-5">
                  {advisory.description}
                </p>
              </div>
            );
          }))}
        </div>
      </div>
    </div>
  );
};
