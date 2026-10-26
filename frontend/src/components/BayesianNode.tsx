/**
 * SafeRoute AI — Custom React Flow Node for Bayesian Network
 * Course Outcome Mapping:
 * - CO4: Displays CPT marginal distributions with CSS animated probability bars
 */

import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';

export interface BayesianNodeData {
  title: string;
  category: string;
  isTarget?: boolean;
  marginals: Record<string, number>;
  colorTheme?: string;
}

export const BayesianNode: React.FC<NodeProps<BayesianNodeData>> = memo(({ data }) => {
  const { title, category, isTarget = false, marginals, colorTheme = '#30a83c' } = data;

  return (
    <div
      className={`rounded-md bg-surface border transition-all duration-300 shadow-sm w-44 font-sans text-xs ${
        isTarget
          ? 'border-hot ring-2 ring-hot/20'
          : 'border-hairline hover:border-body'
      }`}
    >
      {/* Target input handle (top) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !bg-body !border-surface"
      />

      {/* Node Header */}
      <div className="px-2.5 py-1.5 border-b border-hairline flex items-center justify-between bg-canvas/60 rounded-t-md">
        <span className="font-bold text-ink truncate text-[11px]">{title}</span>
        <span
          className="text-[9px] font-bold px-1 py-0.2 rounded-xs uppercase tracking-wider"
          style={{
            backgroundColor: `${colorTheme}18`,
            color: colorTheme,
          }}
        >
          {category}
        </span>
      </div>

      {/* Marginals Animated Bars */}
      <div className="p-2 flex flex-col gap-1.5">
        {Object.entries(marginals || {}).map(([stateName, prob]) => {
          const percent = Math.round(prob * 100);
          return (
            <div key={stateName} className="flex flex-col gap-0.5">
              <div className="flex justify-between text-[10px]">
                <span className="text-body font-medium truncate max-w-[85px]">{stateName}</span>
                <span className="font-mono font-bold text-ink">{percent}%</span>
              </div>
              <div className="w-full h-1.5 bg-canvas rounded-full overflow-hidden border border-hairline/60">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${percent}%`,
                    backgroundColor: isTarget
                      ? percent > 60
                        ? '#ce1736'
                        : percent > 30
                        ? '#fb6001'
                        : '#30a83c'
                      : colorTheme,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Source output handle (bottom) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-body !border-surface"
      />
    </div>
  );
});
