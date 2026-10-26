/**
 * SafeRoute AI — Bayesian Network Card (Right Column 2)
 * Course Outcome Mapping:
 * - CO4: Probabilistic Reasoning with DAG and animated marginal probability bars
 */

import React, { useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
} from 'reactflow';
import type { Node, Edge } from 'reactflow';
import { Network } from 'lucide-react';
import type { BayesianMarginals } from '../api/types';
import { BayesianNode } from './BayesianNode';

interface BayesianNetworkCardProps {
  marginals: BayesianMarginals | null;
  isLoading: boolean;
}

const nodeTypes = {
  bayesianNode: BayesianNode,
};

export const BayesianNetworkCard: React.FC<BayesianNetworkCardProps> = ({
  marginals,
  isLoading,
}) => {
  // Construct DAG nodes based on live marginal distributions
  const nodes: Node[] = useMemo(() => {
    // Normalization helper accepting both lower_case and PascalCase keys
    const raw = (marginals || {}) as Record<string, Record<string, number>>;
    const weather = raw.weather || raw.Weather || { Clear: 0.8, Rain: 0.2 };
    const visibility = raw.visibility || raw.Visibility || { Nominal: 0.9, Impaired: 0.1 };
    const roadSurface = raw.road_surface || raw.RoadSurface || { Dry: 0.85, Wet: 0.15 };
    const timeOfDay = raw.time_of_day || raw.TimeOfDay || { Daylight: 0.85, Night: 0.15 };
    const trafficDensity = raw.traffic_density || raw.TrafficDensity || { Free: 0.7, Congested: 0.3 };
    const accidentRisk = raw.accident_risk || raw.Severity || raw.severity || { Low: 0.7, Moderate: 0.2, Severe: 0.1 };

    return [
      {
        id: 'node-weather',
        type: 'bayesianNode',
        position: { x: 10, y: 10 },
        data: {
          title: 'Weather Condition',
          category: 'Causal Root',
          marginals: weather,
          colorTheme: '#034eb1',
        },
      },
      {
        id: 'node-time',
        type: 'bayesianNode',
        position: { x: 210, y: 10 },
        data: {
          title: 'Time of Day',
          category: 'Temporal',
          marginals: timeOfDay,
          colorTheme: '#7457dd',
        },
      },
      {
        id: 'node-traffic',
        type: 'bayesianNode',
        position: { x: 410, y: 10 },
        data: {
          title: 'Traffic Volume',
          category: 'Demand',
          marginals: trafficDensity,
          colorTheme: '#fb6001',
        },
      },
      {
        id: 'node-road',
        type: 'bayesianNode',
        position: { x: 10, y: 160 },
        data: {
          title: 'Road Surface Friction',
          category: 'Intermediate',
          marginals: roadSurface,
          colorTheme: '#034eb1',
        },
      },
      {
        id: 'node-visibility',
        type: 'bayesianNode',
        position: { x: 210, y: 160 },
        data: {
          title: 'Sight Visibility',
          category: 'Intermediate',
          marginals: visibility,
          colorTheme: '#6b6d70',
        },
      },
      {
        id: 'node-risk',
        type: 'bayesianNode',
        position: { x: 210, y: 310 },
        data: {
          title: 'Accident Risk Hypothesis',
          category: 'Target Query',
          isTarget: true,
          marginals: accidentRisk,
          colorTheme: '#ce1736',
        },
      },
    ];
  }, [marginals]);

  // Directed edges connecting causal nodes in DAG
  const edges: Edge[] = useMemo(() => [
    {
      id: 'e-weather-road',
      source: 'node-weather',
      target: 'node-road',
      animated: true,
      style: { stroke: '#034eb1', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#034eb1' },
    },
    {
      id: 'e-weather-vis',
      source: 'node-weather',
      target: 'node-visibility',
      style: { stroke: '#a7a9ac', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#a7a9ac' },
    },
    {
      id: 'e-time-vis',
      source: 'node-time',
      target: 'node-visibility',
      style: { stroke: '#7457dd', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#7457dd' },
    },
    {
      id: 'e-road-risk',
      source: 'node-road',
      target: 'node-risk',
      animated: true,
      style: { stroke: '#ce1736', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#ce1736' },
    },
    {
      id: 'e-vis-risk',
      source: 'node-visibility',
      target: 'node-risk',
      style: { stroke: '#ce1736', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#ce1736' },
    },
    {
      id: 'e-traffic-risk',
      source: 'node-traffic',
      target: 'node-risk',
      animated: true,
      style: { stroke: '#fb6001', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#fb6001' },
    },
  ], []);

  return (
    <div className="bg-surface rounded-md border border-hairline shadow-sm p-4 flex flex-col gap-2 text-ink font-sans">
      {/* Card Header */}
      <div className="flex items-center justify-between pb-2 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          <Network className="w-4 h-4 text-brand" />
          <h3 className="text-sm font-bold text-ink">Bayesian Causal Network</h3>
        </div>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-brand-surface text-brand-strong"
          title="CO4: pgmpy Causal DAG Marginal Inference & What-If Interventions"
        >
          CO4 pgmpy
        </span>
      </div>

      <p className="text-[11px] text-body">
        Live belief propagation under environmental uncertainty. Node probability bars animate dynamically.
      </p>

      {/* React Flow Container */}
      <div className="w-full h-[270px] bg-canvas rounded-md border border-hairline relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 z-20 bg-surface/60 backdrop-blur-[1px] flex items-center justify-center">
            <span className="text-xs font-bold text-body animate-pulse">
              Propagating causal marginals...
            </span>
          </div>
        )}

        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          zoomOnScroll={false}
          panOnDrag={true}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#dfe1e4" gap={16} size={1} />
          <Controls showInteractive={false} className="!bottom-2 !right-2 !shadow-sm !border !border-hairline !rounded-md" />
        </ReactFlow>
      </div>
    </div>
  );
};
