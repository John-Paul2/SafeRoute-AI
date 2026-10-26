/**
 * SafeRoute AI — Mock API Engine
 * Course Outcome Mapping:
 * - CO1: Agent state simulation and environment sensor inputs
 * - CO2: A* vs Dijkstra route paths with risk-weighted cost
 * - CO3: Forward-chaining expert rule firing & insurance tier scoring
 * - CO4: Bayesian DAG marginal distribution calculation
 * - CO5: XGBoost calibrated probability simulation
 */

import type {
  EnvironmentalConditions,
  PredictResponse,
  RouteResponse,
  RulesResponse,
  MetaResponse,
  DemoStep,
  HighRiskZone,
} from './types';

// Default metadata for Austin, TX
export const MOCK_META: MetaResponse = {
  city: 'Austin',
  state: 'TX',
  map_center: [30.2672, -97.7431],
  default_zoom: 13,
  bounds: {
    south: 30.15,
    west: -97.90,
    north: 30.40,
    east: -97.60,
  },
  default_sliders: {
    precipitation: 0.0,
    visibility: 10.0,
    traffic_density: 35,
    hour: 14,
    weather_condition: 'Clear',
    safety_lambda: 1.5,
    temperature: 74,
    humidity: 48,
    wind_speed: 6,
  },
  supported_weather_conditions: ['Clear', 'Rain', 'Fog', 'Snow', 'Other'],
};

// Preset locations in Austin, TX
export const PRESET_LOCATIONS = {
  austin_downtown: {
    name: 'Downtown Austin (6th & Congress)',
    coords: [30.2687, -97.7428] as [number, number],
  },
  austin_ut: {
    name: 'UT Austin (Tower / Guadalupe)',
    coords: [30.2862, -97.7394] as [number, number],
  },
  zilker_park: {
    name: 'Zilker Metropolitan Park',
    coords: [30.2669, -97.7728] as [number, number],
  },
  mueller_district: {
    name: 'Mueller Urban District',
    coords: [30.3012, -97.7061] as [number, number],
  },
};

// Pre-computed high fidelity Austin road networks
const FASTEST_ROUTE_COORDS: [number, number][] = [
  [30.2687, -97.7428], // Origin: Downtown
  [30.2688, -97.7375], // East to I-35 access
  [30.2715, -97.7348], // On-ramp I-35 North
  [30.2762, -97.7335], // I-35 corridor near 12th St
  [30.2805, -97.7328], // I-35 near MLK Jr Blvd (Major accident blackspot)
  [30.2842, -97.7324], // I-35 off-ramp to Dean Keeton
  [30.2858, -97.7360], // West Dean Keeton
  [30.2862, -97.7394], // Dest: UT Austin Campus
];

// Safe detour route via West Downtown / Guadalupe & Lavaca avoiding I-35 accident bottlenecks
const SAFEST_ROUTE_COORDS: [number, number][] = [
  [30.2687, -97.7428], // Origin: Downtown
  [30.2692, -97.7455], // West to Lavaca St
  [30.2735, -97.7448], // North on Lavaca (Protected Urban Corridor)
  [30.2782, -97.7438], // Lavaca past Texas Capitol
  [30.2825, -97.7425], // North past MLK Blvd on Guadalupe Blvd
  [30.2852, -97.7410], // The Drag / West Mall
  [30.2862, -97.7394], // Dest: UT Austin Campus
];

// Alternative route for longer queries (e.g. Zilker to Mueller)
const ALT_FASTEST_ROUTE: [number, number][] = [
  [30.2669, -97.7728], // Zilker
  [30.2625, -97.7550], // Barton Springs Rd
  [30.2635, -97.7355], // Riverside Dr to I-35
  [30.2770, -97.7330], // I-35 North high risk
  [30.2920, -97.7210], // I-35 near Airport Blvd
  [30.3012, -97.7061], // Mueller
];

const ALT_SAFEST_ROUTE: [number, number][] = [
  [30.2669, -97.7728], // Zilker
  [30.2750, -97.7650], // MoPac Expressway feeder
  [30.2860, -97.7560], // Enfield Rd / Exposition
  [30.2950, -97.7380], // 38th St Protected Parkway
  [30.2990, -97.7220], // 51st St East
  [30.3012, -97.7061], // Mueller
];

/**
 * Predict Mock API: Calculates XGBoost probability and Bayesian marginals
 */
export function mockPredict(conditions: EnvironmentalConditions): PredictResponse {
  const { precipitation, visibility, traffic_density, hour, weather_condition } = conditions;

  // 1. XGBoost-like calibrated probability estimation
  let riskScore = 0.08; // Baseline sunny afternoon risk in Austin urban grid

  // Precipitation penalty
  riskScore += Math.min(0.35, precipitation * 0.32);

  // Visibility penalty (10mi down to 0mi)
  riskScore += ((10 - Math.min(10, Math.max(0, visibility))) / 10) * 0.28;

  // Traffic density penalty
  riskScore += (traffic_density / 100) * 0.24;

  // Nocturnal penalty (21:00 to 05:00)
  if (hour >= 21 || hour <= 5) {
    riskScore += 0.16;
  } else if (hour >= 17 && hour <= 19) {
    // Evening rush hour
    riskScore += 0.10;
  }

  // Weather discrete impact
  if (weather_condition === 'Rain') riskScore += 0.12;
  if (weather_condition === 'Fog') riskScore += 0.18;
  if (weather_condition === 'Snow') riskScore += 0.28;

  // Clamped probability between 0.05 (5%) and 0.98 (98%)
  const calibratedProb = Math.min(0.98, Math.max(0.05, riskScore));
  const riskPercent = Math.round(calibratedProb * 100);

  let riskLevel: 'Low' | 'Moderate' | 'High' | 'Critical' = 'Low';
  if (riskPercent >= 75) riskLevel = 'Critical';
  else if (riskPercent >= 50) riskLevel = 'High';
  else if (riskPercent >= 28) riskLevel = 'Moderate';

  // 2. Bayesian Network Marginals (CO4)
  // Causal simulation: Weather & Time -> Visibility, Road Surface -> Accident Severity
  const wetProb = Math.min(0.95, Math.max(0.04, precipitation * 0.8 + (weather_condition === 'Rain' ? 0.4 : 0.0)));
  const dryProb = Math.max(0.05, 1 - wetProb);

  const lowVisProb = Math.min(0.95, Math.max(0.05, (10 - visibility) / 10 * 0.7 + (weather_condition === 'Fog' ? 0.45 : 0)));
  const highVisProb = Math.max(0.05, 1 - lowVisProb);

  const nightProb = (hour >= 20 || hour <= 5) ? 0.85 : 0.10;
  const dayProb = 1 - nightProb;

  const heavyTrafficProb = Math.min(0.95, Math.max(0.05, traffic_density / 100));
  const lightTrafficProb = Math.max(0.05, 1 - heavyTrafficProb);

  const severeAccidentProb = Math.min(0.92, Math.max(0.06, calibratedProb * 0.85));
  const moderateAccidentProb = Math.min(0.60, Math.max(0.15, (1 - severeAccidentProb) * 0.6));
  const lowAccidentProb = Math.max(0.04, 1 - severeAccidentProb - moderateAccidentProb);

  return {
    xgboost_risk: Number(calibratedProb.toFixed(3)),
    risk_percentage: riskPercent,
    risk_level: riskLevel,
    bayesian_marginals: {
      weather: {
        'Clear': weather_condition === 'Clear' ? 0.82 : 0.08,
        'Rain': weather_condition === 'Rain' ? 0.78 : (precipitation > 0 ? 0.65 : 0.10),
        'Fog': weather_condition === 'Fog' ? 0.75 : (visibility < 3 ? 0.55 : 0.06),
        'Other': 0.06,
      },
      road_surface: {
        'Dry Surface': Number(dryProb.toFixed(2)),
        'Wet / Hydroplaning': Number(wetProb.toFixed(2)),
      },
      visibility: {
        'Nominal (>6 mi)': Number(highVisProb.toFixed(2)),
        'Impaired (<3 mi)': Number(lowVisProb.toFixed(2)),
      },
      time_of_day: {
        'Daylight': Number(dayProb.toFixed(2)),
        'Nocturnal / Twilight': Number(nightProb.toFixed(2)),
      },
      traffic_density: {
        'Free Flow': Number(lightTrafficProb.toFixed(2)),
        'Congested Stop-and-Go': Number(heavyTrafficProb.toFixed(2)),
      },
      accident_risk: {
        'Low Risk': Number(lowAccidentProb.toFixed(2)),
        'Moderate Hazard': Number(moderateAccidentProb.toFixed(2)),
        'Severe Crash Probability': Number(severeAccidentProb.toFixed(2)),
      },
    },
    feature_contributions: {
      'Precipitation': Number((precipitation * 0.4).toFixed(2)),
      'Visibility Reduction': Number(((10 - visibility) * 0.08).toFixed(2)),
      'Traffic Congestion': Number(((traffic_density / 100) * 0.35).toFixed(2)),
      'Time of Day': hour >= 21 || hour <= 5 ? 0.25 : 0.05,
    },
  };
}

/**
 * Route Mock API: Computes risk-aware A* route vs Dijkstra fastest route
 */
export function mockRoute(
  origin: [number, number],
  _destination: [number, number],
  conditions: EnvironmentalConditions,
  safetyLambda: number = 1.5
): RouteResponse {
  const predict = mockPredict(conditions);
  const risk = predict.xgboost_risk;

  // Decide which coordinates set to use (Downtown vs Alternative)
  const isAlt = Math.abs(origin[0] - PRESET_LOCATIONS.zilker_park.coords[0]) < 0.02;
  const baseFastest = isAlt ? ALT_FASTEST_ROUTE : FASTEST_ROUTE_COORDS;
  const baseSafest = isAlt ? ALT_SAFEST_ROUTE : SAFEST_ROUTE_COORDS;

  // High risk zones dynamically generated based on live environmental stress
  const hotThreshold = risk > 0.55 ? 'hot' : (risk > 0.30 ? 'warm' : 'cold');
  const highRiskZones: HighRiskZone[] = [
    {
      id: 'hrz-1',
      lat: 30.2805,
      lng: -97.7328,
      radius: 350 + Math.round(risk * 250),
      risk_score: Number(Math.min(0.96, risk * 1.25).toFixed(2)),
      severity: hotThreshold,
      cause: conditions.precipitation > 0.3 ? 'Hydroplaning & elevated merge collision rate' : 'High volume merging bottleneck',
      location_name: 'I-35 & MLK Jr Blvd Intermodal Nexus',
    },
    {
      id: 'hrz-2',
      lat: 30.2762,
      lng: -97.7335,
      radius: 300 + Math.round(risk * 200),
      risk_score: Number(Math.min(0.92, risk * 1.15).toFixed(2)),
      severity: risk > 0.65 ? 'hot' : (risk > 0.35 ? 'warm' : 'cold'),
      cause: conditions.visibility < 3.0 ? 'Zero-buffer braking & limited line-of-sight' : 'Multi-lane weave congestion',
      location_name: 'I-35 & 12th St Underpass',
    },
    {
      id: 'hrz-3',
      lat: 30.2642,
      lng: -97.7380,
      radius: 280,
      risk_score: Number(Math.min(0.85, risk * 1.05).toFixed(2)),
      severity: risk > 0.50 ? 'warm' : 'cold',
      cause: conditions.hour >= 21 ? 'Night entertainment corridor pedestrian density' : 'Signals queue spillback',
      location_name: 'E Riverside Dr & Congress Junction',
    },
  ];

  // Route Metrics Calculation
  // Fastest route is shorter in distance, but accumulates heavy risk penalty
  const fastestDistance = isAlt ? 4.9 : 2.8;
  const fastestDuration = Number((fastestDistance * 2.8 * (1 + conditions.traffic_density / 120)).toFixed(1));
  const fastestTotalRisk = Number((risk * 1.35).toFixed(2));

  // Safest route adds slight detour (+0.3 to +0.6 miles) to circumvent the high-risk hazard zones
  const safeDetourDist = Number((0.25 + (safetyLambda * 0.12)).toFixed(2));
  const safestDistance = Number((fastestDistance + safeDetourDist).toFixed(1));
  const safestDuration = Number((fastestDuration + 1.2 + (safetyLambda * 0.4)).toFixed(1));
  // Safest route risk is dramatically mitigated by routing through safer urban arterials
  const safestTotalRisk = Number((risk * Math.max(0.28, 0.65 - safetyLambda * 0.08)).toFixed(2));

  // Risk reduction formula
  const riskReductionPct = Math.min(
    78,
    Math.max(22, Math.round(((fastestTotalRisk - safestTotalRisk) / fastestTotalRisk) * 100))
  );

  return {
    safe_route: {
      coordinates: baseSafest,
      distance_miles: safestDistance,
      duration_minutes: safestDuration,
      total_risk_score: safestTotalRisk,
      nodes_count: baseSafest.length + 18,
      summary_street: 'Via Lavaca & Guadalupe Protected Corridors',
    },
    fastest_route: {
      coordinates: baseFastest,
      distance_miles: fastestDistance,
      duration_minutes: fastestDuration,
      total_risk_score: fastestTotalRisk,
      nodes_count: baseFastest.length + 6,
      summary_street: 'Via I-35 Central Expressway Corridor',
    },
    comparison: {
      risk_reduction_percent: riskReductionPct,
      distance_delta_miles: safeDetourDist,
      duration_delta_minutes: Number((safestDuration - fastestDuration).toFixed(1)),
      fastest_risk: fastestTotalRisk,
      safest_risk: safestTotalRisk,
    },
    high_risk_zones: highRiskZones,
  };
}

/**
 * Rules Mock API: Forward-chaining expert rules engine (CO3)
 */
export function mockRules(conditions: EnvironmentalConditions): RulesResponse {
  const predict = mockPredict(conditions);
  const risk = predict.xgboost_risk;
  const advisories: RulesResponse['advisories'] = [];

  // Rule 1: Hydroplaning Critical Hazard
  if (conditions.precipitation >= 0.5) {
    advisories.push({
      id: 'adv-hydro-01',
      level: 'critical',
      title: 'Mandate 15mph Speed Reduction: Severe Hydroplaning Risk',
      description: `Precipitation rate of ${conditions.precipitation.toFixed(2)} in/hr on asphalt surfaces exceeds friction threshold (water film > 0.12 in). High potential for dynamic hydroplaning.`,
      rule_code: 'R-HYDRO-01',
      triggered_by: 'Precipitation >= 0.5 in/hr',
    });
  } else if (conditions.precipitation > 0.05) {
    advisories.push({
      id: 'adv-hydro-02',
      level: 'warning',
      title: 'Roadway Friction Degradation',
      description: 'Damp road surface detected. Increase following headway to 4 seconds minimum.',
      rule_code: 'R-WET-02',
      triggered_by: 'Precipitation > 0.05 in/hr',
    });
  }

  // Rule 2: Impaired Visibility
  if (conditions.visibility <= 2.0) {
    advisories.push({
      id: 'adv-vis-01',
      level: 'critical',
      title: 'Critical Fog / Low Visibility Alert',
      description: `Sight distance restricted to ${conditions.visibility.toFixed(1)} miles. Require automated low-beam headlights and hazard beacon activation.`,
      rule_code: 'R-VIS-04',
      triggered_by: 'Visibility <= 2.0 mi',
    });
  } else if (conditions.visibility <= 5.0) {
    advisories.push({
      id: 'adv-vis-02',
      level: 'warning',
      title: 'Reduced Visual Horizon Warning',
      description: 'Moderate haze/mist reducing driver recognition distance.',
      rule_code: 'R-VIS-02',
      triggered_by: 'Visibility <= 5.0 mi',
    });
  }

  // Rule 3: Heavy Traffic Multi-Vehicle Shunts
  if (conditions.traffic_density >= 70) {
    advisories.push({
      id: 'adv-traf-01',
      level: conditions.traffic_density >= 85 ? 'critical' : 'warning',
      title: 'Severe Traffic Density & Queue Shockwave Alert',
      description: `Traffic volume at ${conditions.traffic_density}% capacity. Rapid deceleration shockwaves expected along major merges.`,
      rule_code: 'R-TRAF-03',
      triggered_by: 'Traffic Density >= 70%',
    });
  }

  // Rule 4: Nocturnal Risk Factor
  if (conditions.hour >= 21 || conditions.hour <= 5) {
    advisories.push({
      id: 'adv-night-01',
      level: 'warning',
      title: 'Nocturnal Driving Vigilance Active',
      description: 'Night conditions restrict peripheral visual acuity; high correlation with impaired driver interactions.',
      rule_code: 'R-NIGHT-01',
      triggered_by: 'Hour in [21:00 - 05:00]',
    });
  }

  // Default baseline advisory if weather is optimal
  if (advisories.length === 0) {
    advisories.push({
      id: 'adv-opt-01',
      level: 'info',
      title: 'Nominal Operating Conditions',
      description: 'Atmospheric and road friction metrics within standard safe baseline limits.',
      rule_code: 'R-NOMINAL-00',
      triggered_by: 'All sensory metrics nominal',
    });
  }

  // Underwriting Tier Assignment (CO3 production rules)
  let tier: RulesResponse['underwriting_tier'];
  if (risk >= 0.75) {
    tier = {
      tier: 'Tier D',
      name: 'High Hazard Surcharge',
      premium_multiplier: 1.85,
      surcharge_percent: 85,
      rationale: 'Severe cumulative environmental hazard and friction loss.',
      color_code: '#ce1736',
    };
  } else if (risk >= 0.50) {
    tier = {
      tier: 'Tier C',
      name: 'Elevated Risk Tier',
      premium_multiplier: 1.45,
      surcharge_percent: 45,
      rationale: 'Heightened accident probability requiring underwriting adjustment.',
      color_code: '#fb6001',
    };
  } else if (risk >= 0.25) {
    tier = {
      tier: 'Tier B',
      name: 'Standard Commercial Tier',
      premium_multiplier: 1.15,
      surcharge_percent: 15,
      rationale: 'Moderate traffic density or light moisture profile.',
      color_code: '#9f5c0c',
    };
  } else {
    tier = {
      tier: 'Tier A',
      name: 'Preferred Safe Driver Tier',
      premium_multiplier: 1.00,
      surcharge_percent: 0,
      rationale: 'Optimal roadway conditions; baseline insurance rates apply.',
      color_code: '#30a83c',
    };
  }

  return {
    advisories,
    underwriting_tier: tier,
  };
}

// Demo mode scripted presentation sequence
export const DEMO_SCENARIOS: DemoStep[] = [
  {
    id: 'demo-clear',
    name: 'Scenario 1: Optimal Daylight',
    badge: 'Sunny Afternoon',
    description: 'Dry surface, 10 mi visibility, free-flowing traffic. Minimal risk, nominal route with Tier A baseline.',
    conditions: {
      precipitation: 0.0,
      visibility: 10.0,
      traffic_density: 25,
      hour: 14,
      weather_condition: 'Clear',
      safety_lambda: 1.0,
      temperature: 78,
      humidity: 42,
      wind_speed: 5,
    },
  },
  {
    id: 'demo-rain',
    name: 'Scenario 2: Heavy Rainstorm',
    badge: 'Severe Downpour',
    description: '0.85 in/hr precipitation, 3.5 mi visibility, 65% traffic. Hydroplaning rule fires; A* detours around I-35 hazard.',
    conditions: {
      precipitation: 0.85,
      visibility: 3.5,
      traffic_density: 65,
      hour: 17,
      weather_condition: 'Rain',
      safety_lambda: 2.5,
      temperature: 64,
      humidity: 92,
      wind_speed: 16,
    },
  },
  {
    id: 'demo-fog-night',
    name: 'Scenario 3: Dense Fog at Midnight',
    badge: 'Zero-Visibility Night',
    description: '0.8 mi visibility, nighttime 23:00, 80% congestion. Bayesian net predicts 88% risk; Tier D hazard surcharge.',
    conditions: {
      precipitation: 0.20,
      visibility: 0.8,
      traffic_density: 80,
      hour: 23,
      weather_condition: 'Fog',
      safety_lambda: 3.8,
      temperature: 52,
      humidity: 98,
      wind_speed: 4,
    },
  },
];
