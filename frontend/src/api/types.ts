/**
 * SafeRoute AI API Type Definitions
 * Course Outcome Mapping:
 * - CO1: Goal-Based Agent PEAS inputs/outputs & state definitions
 * - CO2: Route pathfinding (A* vs Dijkstra) GeoJSON & comparison schemas
 * - CO3: Forward-chaining expert rule advisories & underwriting tier schemas
 * - CO4: Bayesian Network DAG marginal distribution structures
 * - CO5: Supervised ML calibrated risk probabilities & feature metrics
 */

export interface EnvironmentalConditions {
  precipitation: number;      // 0.0 - 1.5 in/hr
  visibility: number;         // 0.0 - 10.0 miles
  traffic_density: number;    // 0 - 100 %
  hour: number;               // 0 - 23 hr
  weather_condition: 'Clear' | 'Rain' | 'Fog' | 'Snow' | 'Other';
  safety_lambda: number;      // 0.0 - 5.0 (trade-off weight)
  temperature?: number;       // Fahrenheit
  humidity?: number;          // %
  wind_speed?: number;        // mph
}

export interface BayesianMarginals {
  weather: Record<string, number>;
  visibility: Record<string, number>;
  road_surface: Record<string, number>;
  traffic_density: Record<string, number>;
  time_of_day: Record<string, number>;
  accident_risk: Record<string, number>;
}

export interface PredictResponse {
  xgboost_risk: number;        // 0.0 - 1.0 calibrated probability
  risk_percentage: number;    // 0 - 100
  risk_level: 'Low' | 'Moderate' | 'High' | 'Critical';
  bayesian_marginals: BayesianMarginals;
  feature_contributions?: Record<string, number>;
}

export interface RouteCoordinate {
  lat: number;
  lng: number;
}

export interface RoutePath {
  coordinates: [number, number][]; // [lat, lng] pairs
  distance_miles: number;
  duration_minutes: number;
  total_risk_score: number;
  nodes_count: number;
  summary_street?: string;
}

export interface HighRiskZone {
  id: string;
  lat: number;
  lng: number;
  radius: number;           // in meters
  risk_score: number;       // 0.0 - 1.0
  severity: 'cold' | 'warm' | 'hot';
  cause: string;
  location_name: string;
}

export interface RouteResponse {
  safe_route: RoutePath;
  fastest_route: RoutePath;
  comparison: {
    risk_reduction_percent: number; // e.g. 48.5%
    distance_delta_miles: number;   // e.g. +0.4 mi
    duration_delta_minutes: number; // e.g. +2.1 min
    fastest_risk: number;
    safest_risk: number;
  };
  high_risk_zones: HighRiskZone[];
}

export interface RuleAdvisory {
  id: string;
  level: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  rule_code: string;
  triggered_by: string;
}

export interface UnderwritingTier {
  tier: 'Tier A' | 'Tier B' | 'Tier C' | 'Tier D';
  name: string;
  premium_multiplier: number;
  surcharge_percent: number;
  rationale: string;
  color_code: string;
}

export interface RulesResponse {
  advisories: RuleAdvisory[];
  underwriting_tier: UnderwritingTier;
}

export interface MetaResponse {
  city: string;
  state: string;
  map_center: [number, number];
  default_zoom: number;
  bounds: {
    south: number;
    west: number;
    north: number;
    east: number;
  };
  default_sliders: EnvironmentalConditions;
  supported_weather_conditions: string[];
  demo_scenarios?: DemoStep[];
}

export interface DemoStep {
  id: string;
  name: string;
  badge: string;
  description: string;
  conditions: EnvironmentalConditions;
}
