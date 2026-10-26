/**
 * SafeRoute AI — Responsive Mobile Bottom Sheet (< 768px)
 * Below 768px, transforms the right column into an expandable bottom drawer with tabs.
 */

import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Activity, Network, BookOpen, GitCompare } from 'lucide-react';

interface BottomSheetProps {
  children: {
    risk: React.ReactNode;
    bayesian: React.ReactNode;
    rules: React.ReactNode;
    comparison: React.ReactNode;
  };
}

export const BottomSheet: React.FC<BottomSheetProps> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'risk' | 'bayesian' | 'rules' | 'comparison'>('risk');

  return (
    <div
      className={`md:hidden fixed bottom-0 left-0 right-0 z-40 bg-surface rounded-t-xl border-t border-hairline shadow-2xl transition-all duration-300 flex flex-col font-sans ${
        isOpen ? 'h-[75vh]' : 'h-16'
      }`}
    >
      {/* Drawer Handle & Tab Bar */}
      <div
        className="px-4 py-2 border-b border-hairline flex items-center justify-between cursor-pointer select-none bg-canvas/50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-1 bg-muted rounded-full mx-auto" />
          <span className="text-xs font-bold text-ink">
            {isOpen ? 'Tap to Collapse Drawer' : 'View AI Analytics & Route Comparison'}
          </span>
        </div>
        <button className="text-body p-1 hover:text-ink">
          {isOpen ? <ChevronDown className="w-5 h-5" /> : <ChevronUp className="w-5 h-5" />}
        </button>
      </div>

      {/* Tabs navigation when open */}
      {isOpen && (
        <div className="grid grid-cols-4 border-b border-hairline bg-surface text-xs font-bold">
          <button
            onClick={() => setActiveTab('risk')}
            className={`py-2 px-1 flex flex-col items-center gap-1 border-b-2 transition-colors ${
              activeTab === 'risk'
                ? 'border-brand text-brand'
                : 'border-transparent text-body hover:text-ink'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="text-[10px]">Risk</span>
          </button>
          <button
            onClick={() => setActiveTab('bayesian')}
            className={`py-2 px-1 flex flex-col items-center gap-1 border-b-2 transition-colors ${
              activeTab === 'bayesian'
                ? 'border-brand text-brand'
                : 'border-transparent text-body hover:text-ink'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span className="text-[10px]">Bayes DAG</span>
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`py-2 px-1 flex flex-col items-center gap-1 border-b-2 transition-colors ${
              activeTab === 'rules'
                ? 'border-brand text-brand'
                : 'border-transparent text-body hover:text-ink'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span className="text-[10px]">Rules</span>
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`py-2 px-1 flex flex-col items-center gap-1 border-b-2 transition-colors ${
              activeTab === 'comparison'
                ? 'border-brand text-brand'
                : 'border-transparent text-body hover:text-ink'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span className="text-[10px]">Compare</span>
          </button>
        </div>
      )}

      {/* Tab Content Panel */}
      {isOpen && (
        <div className="flex-1 overflow-y-auto p-4 bg-canvas/40">
          {activeTab === 'risk' && children.risk}
          {activeTab === 'bayesian' && children.bayesian}
          {activeTab === 'rules' && children.rules}
          {activeTab === 'comparison' && children.comparison}
        </div>
      )}
    </div>
  );
};
