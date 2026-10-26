/**
 * SafeRoute AI — Main Dashboard Application
 * Course Outcome Mapping:
 * - CO1: Goal-Based Agent PEAS Orchestration (Perception, Environment, Actuators, Sensors)
 * - CO2: Risk-Aware A* Search vs Dijkstra Shortest Path Planning
 * - CO3: Forward-Chaining Expert Rule Engine & Insurance Underwriting
 * - CO4: Bayesian DAG Causal Inference & Marginal Uncertainty
 * - CO5: Supervised ML XGBoost Accident Risk Scoring
 *
 * DESIGN.md Compliance:
 * - App Name: "SafeRoute AI" (No German/deals/mydealz elements)
 * - Typography: Mulish 500/700 font tokens
 * - Full-bleed react-leaflet map with floating 8px white cards
 * - Temperature-control pill (cold-blue #034eb1 -> hot-red #ce1736 with live risk %)
 * - Bayesian Network React Flow DAG with animated marginal bars
 * - Warning-badge chips (critical hot-red, warning amber) & Underwriting Tier badge
 * - Route comparison with mint discount-badge ("−X% risk exposure") and deltas
 * - Compare toggle & scripted presentation Demo Mode (Clear -> Rain -> Fog+Night)
 * - Debounced sliders (300ms) with skeletons and toasts
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AlertOctagon } from 'lucide-react';
import { Header } from './components/Header';
import { ConditionsPanel } from './components/ConditionsPanel';
import { RiskCard } from './components/RiskCard';
import { BayesianNetworkCard } from './components/BayesianNetworkCard';
import { RuleAdvisoriesCard } from './components/RuleAdvisoriesCard';
import { RouteComparisonCard } from './components/RouteComparisonCard';
import { MapView } from './components/MapView';
import { BottomSheet } from './components/BottomSheet';
import { ToastContainer } from './components/Toast';
import type { ToastMessage } from './components/Toast';
import { useDebounce } from './hooks/useDebounce';
import {
  predictRisk,
  calculateRoute,
  evaluateRules,
  getMetadata,
} from './api/client';
import type {
  EnvironmentalConditions,
  PredictResponse,
  RouteResponse,
  RulesResponse,
  MetaResponse,
} from './api/types';
import { PRESET_LOCATIONS, DEMO_SCENARIOS } from './api/mock';

export const App: React.FC = () => {
  // Metadata state
  const [meta, setMeta] = useState<MetaResponse | null>(null);

  // Conditions slider state
  const [conditions, setConditions] = useState<EnvironmentalConditions>({
    precipitation: 0.0,
    visibility: 10.0,
    traffic_density: 35,
    hour: 14,
    weather_condition: 'Clear',
    safety_lambda: 1.5,
    temperature: 74,
    humidity: 48,
    wind_speed: 6,
  });

  // Debounce conditions (300ms) to prevent unnecessary rapid API recalculations
  const debouncedConditions = useDebounce<EnvironmentalConditions>(conditions, 300);

  // Origin & Destination coordinates (Default: Downtown Austin -> UT Austin)
  const [origin, setOrigin] = useState<[number, number]>(
    PRESET_LOCATIONS.austin_downtown.coords
  );
  const [destination, setDestination] = useState<[number, number]>(
    PRESET_LOCATIONS.austin_ut.coords
  );
  const [originName, setOriginName] = useState<string>('Downtown Austin');
  const [destinationName, setDestinationName] = useState<string>('UT Austin Campus');
  const [isOriginNext, setIsOriginNext] = useState<boolean>(false);

  // API response states
  const [predictData, setPredictData] = useState<PredictResponse | null>(null);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [rulesData, setRulesData] = useState<RulesResponse | null>(null);

  // Loading, Comparison & Error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [compareRoutes, setCompareRoutes] = useState<boolean>(true);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  // Toast notifications
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Demo Mode state
  const [isDemoActive, setIsDemoActive] = useState<boolean>(false);
  const [demoStepIndex, setDemoStepIndex] = useState<number>(0);
  const demoTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const addToast = useCallback((message: string, type: ToastMessage['type'] = 'info') => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev.slice(-3), { id, message, type }]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Initialize metadata
  useEffect(() => {
    getMetadata()
      .then((data) => {
        setMeta(data);
        if (data.default_sliders) {
          setConditions((prev) => ({ ...prev, ...data.default_sliders }));
        }
      })
      .catch((err) => {
        console.error('Meta load failed:', err);
        addToast('Connected to fallback offline metadata', 'info');
      });
  }, [addToast]);

  // Main evaluation trigger: calls /predict, /route, /rules
  const executeEvaluation = useCallback(
    async (
      evalConditions: EnvironmentalConditions,
      orig: [number, number],
      dest: [number, number]
    ) => {
      setIsLoading(true);
      try {
        // Parallel API calls
        const [predRes, routeRes, rulesRes] = await Promise.all([
          predictRisk(evalConditions),
          calculateRoute(orig, dest, evalConditions, evalConditions.safety_lambda),
          evaluateRules(evalConditions),
        ]);

        setPredictData(predRes);
        setRouteData(routeRes);
        setRulesData(rulesRes);
        setEvaluationError(null);
      } catch (err: unknown) {
        console.error('Evaluation failed:', err);
        const errMsg = err instanceof Error ? err.message : 'Unknown evaluation error';
        setEvaluationError(errMsg);
        addToast(`Inference Error: ${errMsg}`, 'error');
      } finally {
        setIsLoading(false);
      }
    },
    [addToast]
  );

  // Trigger evaluation whenever debounced sliders or points change
  useEffect(() => {
    executeEvaluation(debouncedConditions, origin, destination);
  }, [debouncedConditions, origin, destination, executeEvaluation]);

  // Handle condition updates from UI sliders
  const handleConditionChange = (updated: Partial<EnvironmentalConditions>) => {
    // If user manually moves a slider during demo mode, pause demo
    if (isDemoActive) {
      stopDemo();
      addToast('Demo mode paused: Manual slider interaction detected', 'info');
    }
    setConditions((prev) => ({ ...prev, ...updated }));
  };

  // Map click handler: alternating Point A and Point B
  const handleMapCoordClick = (lat: number, lng: number) => {
    if (isOriginNext) {
      setOrigin([lat, lng]);
      setOriginName(`Custom Pin A (${lat.toFixed(3)}, ${lng.toFixed(3)})`);
      setIsOriginNext(false);
      addToast('Point A (Origin) re-pinned', 'success');
    } else {
      setDestination([lat, lng]);
      setDestinationName(`Custom Pin B (${lat.toFixed(3)}, ${lng.toFixed(3)})`);
      setIsOriginNext(true);
      addToast('Point B (Destination) re-pinned', 'success');
    }
  };

  // Preset location selector
  const handleSelectPreset = (
    orig: [number, number],
    dest: [number, number],
    origName: string,
    destName: string
  ) => {
    setOrigin(orig);
    setDestination(dest);
    setOriginName(origName);
    setDestinationName(destName);
    addToast(`Loaded preset corridor: ${origName} → ${destName}`, 'info');
  };

  // Reset to default
  const handleReset = () => {
    stopDemo();
    const defaults = meta?.default_sliders || {
      precipitation: 0.0,
      visibility: 10.0,
      traffic_density: 35,
      hour: 14,
      weather_condition: 'Clear' as const,
      safety_lambda: 1.5,
      temperature: 74,
      humidity: 48,
      wind_speed: 6,
    };
    setConditions(defaults);
    setOrigin(PRESET_LOCATIONS.austin_downtown.coords);
    setDestination(PRESET_LOCATIONS.austin_ut.coords);
    setOriginName('Downtown Austin');
    setDestinationName('UT Austin Campus');
    addToast('Reset to default Austin baseline conditions', 'info');
  };

  // Demo Mode Playback Engine
  const stopDemo = useCallback(() => {
    setIsDemoActive(false);
    if (demoTimerRef.current) {
      clearInterval(demoTimerRef.current);
      demoTimerRef.current = null;
    }
  }, []);

  const toggleDemo = () => {
    if (isDemoActive) {
      stopDemo();
      addToast('Presentation Demo stopped', 'info');
    } else {
      setIsDemoActive(true);
      setDemoStepIndex(0);
      const firstScenario = DEMO_SCENARIOS[0];
      setConditions(firstScenario.conditions);
      addToast(`Playing Demo: ${firstScenario.name}`, 'info');
    }
  };

  // Step advancement timer for demo mode
  useEffect(() => {
    if (!isDemoActive) return;

    demoTimerRef.current = setInterval(() => {
      setDemoStepIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % DEMO_SCENARIOS.length;
        const scenario = DEMO_SCENARIOS[nextIndex];
        setConditions(scenario.conditions);
        addToast(`Demo step ${nextIndex + 1}/${DEMO_SCENARIOS.length}: ${scenario.name}`, 'info');
        return nextIndex;
      });
    }, 4500);

    return () => {
      if (demoTimerRef.current) {
        clearInterval(demoTimerRef.current);
      }
    };
  }, [isDemoActive, addToast]);

  const activeDemoScenario = isDemoActive ? DEMO_SCENARIOS[demoStepIndex] : null;

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-canvas text-ink flex flex-col font-sans">
      {/* Top Header Navbar */}
      <Header
        compareRoutes={compareRoutes}
        onToggleCompare={setCompareRoutes}
        isDemoActive={isDemoActive}
        demoStepIndex={demoStepIndex}
        demoTotalSteps={DEMO_SCENARIOS.length}
        demoStepName={activeDemoScenario?.badge}
        onToggleDemo={toggleDemo}
        onStopDemo={stopDemo}
        onReset={handleReset}
        isCalculating={isLoading}
      />

      {/* Main Container: Full-Bleed Map with Floating Cards */}
      <div className="relative flex-1 w-full h-[calc(100vh-60px)] overflow-hidden">
        {/* Layer 1: Full Bleed Leaflet Map */}
        <MapView
          routeData={routeData}
          origin={origin}
          destination={destination}
          onMapClickCoordinates={handleMapCoordClick}
          showFastestComparison={compareRoutes}
          cityCenter={meta?.map_center || [30.2672, -97.7431]}
          zoom={meta?.default_zoom || 13}
          isCalculating={isLoading}
        />

        {/* Layer 2: Left Column Floating Card (Conditions Panel) */}
        <div className="hidden md:block absolute top-4 left-4 z-20 pointer-events-auto">
          <ConditionsPanel
            conditions={conditions}
            onChange={handleConditionChange}
            onCalculateRoute={() => executeEvaluation(conditions, origin, destination)}
            onReset={handleReset}
            origin={origin}
            destination={destination}
            originName={originName}
            destinationName={destinationName}
            onSelectPreset={handleSelectPreset}
            onSelectScenario={(scen) => {
              stopDemo();
              setConditions(scen.conditions);
              addToast(`Loaded Demo: ${scen.name}`, 'info');
            }}
            isCalculating={isLoading}
          />
        </div>

        {/* Layer 3: Right Column Floating Cards */}
        <div className="hidden md:flex absolute top-4 right-4 z-20 w-[380px] lg:w-[420px] max-h-[calc(100vh-90px)] overflow-y-auto flex-col gap-3 pointer-events-auto pr-1">
          {/* Optional Evaluation Error Card */}
          {evaluationError && (
            <div className="bg-[#fde8eb] border border-[#f8b4bc] rounded-md p-3 flex items-start justify-between gap-2 text-hot text-xs font-sans shadow-sm">
              <div className="flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block">Backend Communication Error</span>
                  <span className="text-[11px] opacity-90">{evaluationError}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => executeEvaluation(debouncedConditions, origin, destination)}
                className="px-2 py-1 bg-hot text-white font-bold rounded-xs text-[10px] shrink-0 hover:bg-[#a6132b] transition-colors cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* Card 1: Risk Card with Temperature-Control Pill */}
          <RiskCard predict={predictData} isLoading={isLoading} />

          {/* Card 2: Bayesian Network Card with animated marginal bars */}
          <BayesianNetworkCard
            marginals={predictData?.bayesian_marginals || null}
            isLoading={isLoading}
          />

          {/* Card 3: Rule Advisories & Underwriting Tier */}
          <RuleAdvisoriesCard rules={rulesData} isLoading={isLoading} />

          {/* Card 4: Route Comparison with Mint Discount-Badge */}
          <RouteComparisonCard routeData={routeData} isLoading={isLoading} />
        </div>

        {/* Layer 4: Mobile Responsive Bottom Sheet (< 768px) */}
        <BottomSheet>
          {{
            risk: <RiskCard predict={predictData} isLoading={isLoading} />,
            bayesian: (
              <BayesianNetworkCard
                marginals={predictData?.bayesian_marginals || null}
                isLoading={isLoading}
              />
            ),
            rules: <RuleAdvisoriesCard rules={rulesData} isLoading={isLoading} />,
            comparison: <RouteComparisonCard routeData={routeData} isLoading={isLoading} />,
          }}
        </BottomSheet>

        {/* Mobile floating conditions button when on small screens */}
        <div className="md:hidden absolute top-3 left-3 z-30 pointer-events-auto">
          <div className="bg-surface/95 backdrop-blur-sm border border-hairline rounded-md p-2 shadow-md max-w-[260px]">
            <div className="text-[11px] font-bold text-ink mb-1">Quick Conditions:</div>
            <div className="grid grid-cols-2 gap-1 text-[10px]">
              <button
                onClick={() => handleConditionChange({ weather_condition: 'Rain', precipitation: 0.8 })}
                className="px-2 py-1 rounded bg-canvas border border-hairline font-bold"
              >
                Rain (0.8")
              </button>
              <button
                onClick={() => handleConditionChange({ weather_condition: 'Fog', visibility: 0.8 })}
                className="px-2 py-1 rounded bg-canvas border border-hairline font-bold"
              >
                Fog (0.8 mi)
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Toast Notifications Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};

export default App;
