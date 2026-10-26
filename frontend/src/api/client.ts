/**
 * SafeRoute AI API Client
 * Course Outcome Mapping:
 * - CO1: Agent sensor dispatch and telemetry aggregation
 * - CO2: A* route retrieval
 * - CO3: Production rule evaluation dispatch
 * - CO4: Bayesian marginal request dispatch
 * - CO5: ML predictive scoring dispatch
 */

import type {
  EnvironmentalConditions,
  PredictResponse,
  RouteResponse,
  RulesResponse,
  MetaResponse,
  DemoStep,
} from './types';
import {
  mockPredict,
  mockRoute,
  mockRules,
  MOCK_META,
  DEMO_SCENARIOS,
} from './mock';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Live backend mode: Set USE_MOCK to false to connect directly to Django REST API
export const USE_MOCK: boolean = false;

// URL normalizer helper: ensures http://localhost:8000/api/... is targeted cleanly
const normalizeUrl = (endpoint: string): string => {
  const base = API_BASE_URL.replace(/\/+$/, '');
  const path = endpoint.replace(/^\/+/, '');
  const cleanBase = base.endsWith('/api') ? base : `${base}/api`;
  return `${cleanBase}/${path}`;
};

// Helper simulated latency for mock fallback
const simulateLatency = (ms: number = 180) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Fetch city bounds and default slider configurations
 */
export async function getMetadata(): Promise<MetaResponse> {
  if (USE_MOCK) {
    await simulateLatency(100);
    return MOCK_META;
  }

  const response = await fetch(normalizeUrl('meta/'));
  if (!response.ok) {
    throw new Error(`Failed to fetch metadata (${response.status}): ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch seeded demo presentation scenarios
 */
export async function getScenarios(): Promise<DemoStep[]> {
  if (USE_MOCK) {
    return DEMO_SCENARIOS;
  }

  try {
    const response = await fetch(normalizeUrl('scenarios/'));
    if (!response.ok) return DEMO_SCENARIOS;
    const data = await response.json();
    return data.scenarios || DEMO_SCENARIOS;
  } catch {
    return DEMO_SCENARIOS;
  }
}

/**
 * Predict risk score via XGBoost & Bayesian Network marginals
 */
export async function predictRisk(conditions: EnvironmentalConditions): Promise<PredictResponse> {
  if (USE_MOCK) {
    await simulateLatency(160);
    return mockPredict(conditions);
  }

  const response = await fetch(normalizeUrl('predict/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(conditions),
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const err = await response.json();
      detail = err.error || err.details || JSON.stringify(err);
    } catch {}
    throw new Error(`Predict endpoint error: ${detail}`);
  }
  return response.json();
}

/**
 * Calculate risk-weighted A* route vs baseline fastest route
 */
export async function calculateRoute(
  origin: [number, number],
  destination: [number, number],
  conditions: EnvironmentalConditions,
  safetyLambda: number
): Promise<RouteResponse> {
  if (USE_MOCK) {
    await simulateLatency(220);
    return mockRoute(origin, destination, conditions, safetyLambda);
  }

  const response = await fetch(normalizeUrl('route/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin,
      destination,
      conditions,
      safety_lambda: safetyLambda,
    }),
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const err = await response.json();
      detail = err.error || err.details || JSON.stringify(err);
    } catch {}
    throw new Error(`Routing endpoint error: ${detail}`);
  }
  return response.json();
}

/**
 * Evaluate expert rules knowledge base and underwriting tier
 */
export async function evaluateRules(
  conditions: EnvironmentalConditions,
  routeStats?: { distance_miles: number; duration_minutes: number; risk_score: number }
): Promise<RulesResponse> {
  if (USE_MOCK) {
    await simulateLatency(120);
    return mockRules(conditions);
  }

  const response = await fetch(normalizeUrl('rules/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conditions, route_stats: routeStats }),
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const err = await response.json();
      detail = err.error || err.details || JSON.stringify(err);
    } catch {}
    throw new Error(`Rules endpoint error: ${detail}`);
  }
  return response.json();
}

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<{ status: string; project: string }> {
  if (USE_MOCK) {
    return { status: 'healthy (mock active)', project: 'SafeRoute AI - Micro Project 14' };
  }

  const response = await fetch(normalizeUrl('health/'));
  return response.json();
}
