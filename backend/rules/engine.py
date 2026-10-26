"""
SafeRoute AI - Expert Rule Engine & Insurance Underwriting System
Course Outcome Mapping:
    - CO3 (Knowledge Representation and Reasoning): Forward-chaining production rules,
      conflict resolution, working memory facts, explainability traces.

Description:
    Implements a forward-chaining expert production rule engine in pure Python.
    Evaluates environmental, telemetry, and route facts against declarative safety
    rules and actuarial underwriting models.
    Produces:
    1. Operational Traffic Advisories (speed reduction, lane closure, warnings)
    2. Insurance Underwriting Tier & Dynamic Premium Multipliers
    3. Full fact-level explainability traces for auditability.
"""

from typing import Dict, Any, List, Optional, Callable
import copy


class Fact(dict):
    """
    Working Memory Fact.
    Represents an atomic piece of knowledge or sensor observation.
    Supports both dictionary-style key access and object attribute access.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dict__.update(kwargs)

    def __getattr__(self, name: str) -> Any:
        return self.get(name)

    def __setattr__(self, name: str, value: Any):
        self[name] = value
        self.__dict__[name] = value

    def __copy__(self):
        return Fact(**dict(self))


class RuleDefinition:
    """
    Encapsulates a forward-chaining production rule.
    Condition (LHS) -> Action / Advisory (RHS).
    """
    def __init__(
        self,
        rule_id: str,
        title: str,
        severity: str,
        predicate: Callable[[Fact], bool],
        message_template: str,
        category: str = "advisory",
        priority: int = 10,
    ):
        self.rule_id = rule_id
        self.title = title
        self.severity = severity  # 'critical', 'warning', 'info'
        self.predicate = predicate
        self.message_template = message_template
        self.category = category  # 'advisory' or 'underwriting'
        self.priority = priority


class KnowledgeEngine:
    """
    Production Rule Engine maintaining Working Memory and Agenda.
    Performs forward-chaining evaluation over registered rules.
    """

    def __init__(self):
        self.working_memory: List[Fact] = []
        self.rules: List[RuleDefinition] = []
        self._register_default_rules()

    def add_rule(self, rule: RuleDefinition):
        """Registers a production rule into the rulebase."""
        self.rules.append(rule)
        # Keep rules sorted by descending priority (conflict resolution)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def reset(self):
        """Clears working memory."""
        self.working_memory.clear()

    def declare(self, fact: Fact):
        """Asserts a new fact into working memory."""
        self.working_memory.append(fact)

    def run(self) -> Dict[str, Any]:
        """
        Executes forward chaining cycle.
        Evaluates working memory against rules and returns:
        - advisories: list of fired advisory rules with explainability facts
        - underwriting_tier: determined tier object and premium multiplier
        """
        # Synthesize consolidated facts from working memory
        context = Fact()
        for f in self.working_memory:
            context.update(dict(f))

        fired_advisories = []
        fired_underwriting = None

        risk_prob = float(context.get("risk_probability", 0.0))
        prob_pct = risk_prob * 100.0

        for rule in self.rules:
            try:
                if rule.predicate(context):
                    # Extract only the triggering facts relevant for explainability
                    triggered_facts = self._extract_relevant_facts(rule.rule_id, context)

                    # Build message with dynamic probability formatting
                    message = rule.message_template.format(
                        prob_pct=prob_pct,
                        risk_prob=risk_prob,
                        weather=context.get("weather", "Unknown"),
                        road_surface=context.get("road_surface", "Unknown"),
                        visibility=context.get("visibility", 10.0),
                        time_of_day=context.get("time_of_day", "Day"),
                        traffic_density=context.get("traffic_density", 0),
                        route_length_km=context.get("route_length_km", 0.0),
                        precipitation=context.get("precipitation", 0.0)
                    )

                    record = {
                        "id": rule.rule_id,
                        "rule_code": rule.rule_id,
                        "title": rule.title,
                        "severity": rule.severity,
                        "level": rule.severity,  # alias for frontend
                        "message": message,
                        "description": message,  # alias for frontend
                        "facts": triggered_facts,
                        "triggered_by": ", ".join(f"{k}={v}" for k, v in triggered_facts.items()),
                    }

                    if rule.category == "advisory":
                        fired_advisories.append(record)
                    elif rule.category == "underwriting" and fired_underwriting is None:
                        # Highest priority matching underwriting rule wins
                        fired_underwriting = self._build_underwriting_tier(rule.rule_id, context)

            except Exception:
                # Fault-tolerant evaluation - log and proceed with remaining rules
                continue

        # If no underwriting rule explicitly triggered, fallback to Standard Tier B
        if fired_underwriting is None:
            fired_underwriting = self._build_underwriting_tier("R14_TIER_STANDARD", context)

        return {
            "advisories": fired_advisories,
            "underwriting_tier": fired_underwriting,
            "premium_multiplier": fired_underwriting["premium_multiplier"],
            "fired_count": len(fired_advisories)
        }

    def _extract_relevant_facts(self, rule_id: str, context: Fact) -> Dict[str, Any]:
        """Filters working memory to isolate facts that caused this specific rule to fire."""
        relevant_keys = ["risk_probability"]
        if "HYDROPLANING" in rule_id:
            relevant_keys.extend(["road_surface", "weather", "precipitation"])
        elif "FOG" in rule_id:
            relevant_keys.extend(["visibility", "weather"])
        elif "BLACK_ICE" in rule_id:
            relevant_keys.extend(["road_surface", "weather"])
        elif "LANE_CLOSURE" in rule_id:
            relevant_keys.extend(["traffic_density", "risk_probability"])
        elif "NIGHT" in rule_id:
            relevant_keys.extend(["time_of_day", "visibility"])
        elif "CONGESTION" in rule_id:
            relevant_keys.extend(["traffic_density"])
        elif "STORM" in rule_id:
            relevant_keys.extend(["precipitation", "weather"])
        elif "LONG_ROUTE" in rule_id or "FATIGUE" in rule_id:
            relevant_keys.extend(["route_length_km", "time_of_day"])
        elif "COMPOUND" in rule_id:
            relevant_keys.extend(["weather", "time_of_day", "traffic_density"])
        elif "DUSK" in rule_id:
            relevant_keys.extend(["time_of_day"])
        elif "PEDESTRIAN" in rule_id:
            relevant_keys.extend(["traffic_density", "visibility"])
        elif "OPTIMAL" in rule_id:
            relevant_keys.extend(["weather", "road_surface", "time_of_day"])
        else:
            relevant_keys.extend(["weather", "road_surface", "traffic_density"])

        return {k: context.get(k) for k in relevant_keys if context.get(k) is not None}

    def _build_underwriting_tier(self, rule_id: str, context: Fact) -> Dict[str, Any]:
        """Translates actuarial rule into underwriting tier with multiplier."""
        risk = float(context.get("risk_probability", 0.0))
        prob_pct = risk * 100.0

        if rule_id == "R13_TIER_LOW":
            return {
                "tier": "Tier A",
                "tier_name": "Low",
                "name": "Tier A (Low Risk - Preferred)",
                "premium_multiplier": 0.95,
                "surcharge_percent": -5.0,
                "color_code": "#30a83c",
                "rationale": f"Actuarial baseline risk is low ({prob_pct:.1f}%). Ideal surface conditions qualify for a 5% preferred safe-driver discount."
            }
        elif rule_id == "R14_TIER_STANDARD":
            return {
                "tier": "Tier B",
                "tier_name": "Standard",
                "name": "Tier B (Standard Risk)",
                "premium_multiplier": 1.15,
                "surcharge_percent": 15.0,
                "color_code": "#034eb1",
                "rationale": f"Moderate accident exposure ({prob_pct:.1f}%). Standard comprehensive coverage applies with a 15% risk-adjusted surcharge."
            }
        elif rule_id == "R15_TIER_HIGH":
            return {
                "tier": "Tier C",
                "tier_name": "High",
                "name": "Tier C (High Risk - Elevated Surcharge)",
                "premium_multiplier": 1.45,
                "surcharge_percent": 45.0,
                "color_code": "#fb6001",
                "rationale": f"Elevated loss expectancy ({prob_pct:.1f}%). Substantial claims hazard warrants a 45% policy surcharge and higher deductible."
            }
        else:  # R16_TIER_REFER
            return {
                "tier": "Tier D",
                "tier_name": "Refer",
                "name": "Tier D (Refer to Underwriter)",
                "premium_multiplier": 2.10,
                "surcharge_percent": 110.0,
                "color_code": "#ce1736",
                "rationale": f"Critical danger threshold breached ({prob_pct:.1f}%). Exceeds automated underwriting limit; requires senior underwriting referral."
            }

    def _register_default_rules(self):
        """Registers the 12+ production rules for traffic safety advisories & underwriting."""

        # -------------------------------------------------------------------------
        # (a) TRAFFIC MANAGEMENT ADVISORY RULES (At least 12 distinct operational rules)
        # -------------------------------------------------------------------------

        # Rule 1: Hydroplaning Risk Mandate
        def p_hydro(f: Fact) -> bool:
            wet_surface = str(f.get("road_surface", "")).lower() in ("wet", "standing_water")
            rain_weather = str(f.get("weather", "")).lower() in ("rain", "storm")
            precip = float(f.get("precipitation", 0.0)) > 0.05
            p_sev = float(f.get("risk_probability", 0.0))
            return (wet_surface or rain_weather or precip) and (p_sev >= 0.55)

        self.add_rule(RuleDefinition(
            rule_id="R01_HYDROPLANING",
            title="Mandate Speed Reduction – Hydroplaning Risk",
            severity="critical",
            predicate=p_hydro,
            message_template="Mandate speed reduction to 35 mph – severe hydroplaning hazard active with {prob_pct:.1f}% accident probability on wet asphalt.",
            category="advisory",
            priority=95
        ))

        # Rule 2: Dense Fog Warning
        def p_fog(f: Fact) -> bool:
            vis = float(f.get("visibility", 10.0))
            fog_weather = str(f.get("weather", "")).lower() == "fog"
            return vis < 2.0 or (fog_weather and vis < 4.0)

        self.add_rule(RuleDefinition(
            rule_id="R02_DENSE_FOG",
            title="Dense Fog Sightline Warning",
            severity="warning",
            predicate=p_fog,
            message_template="Severe sightline limitation detected (visibility {visibility} mi, {prob_pct:.1f}% risk). Engage low-beam fog lamps and increase headway.",
            category="advisory",
            priority=85
        ))

        # Rule 3: Black Ice / Loss of Traction
        def p_ice(f: Fact) -> bool:
            icy = str(f.get("road_surface", "")).lower() in ("icy", "ice", "snow")
            snow = str(f.get("weather", "")).lower() in ("snow", "sleet", "freezing_rain")
            p_sev = float(f.get("risk_probability", 0.0))
            return (icy or snow) and (p_sev >= 0.35)

        self.add_rule(RuleDefinition(
            rule_id="R03_BLACK_ICE",
            title="Severe Black Ice & Traction Loss Alert",
            severity="critical",
            predicate=p_ice,
            message_template="Loss of pavement traction danger: black ice conditions with {prob_pct:.1f}% incident probability. Avoid hard braking; bridge decks freeze first.",
            category="advisory",
            priority=98
        ))

        # Rule 4: Lane Closure / Divert Heavy Vehicles
        def p_divert(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            traffic = f.get("traffic_density", 0)
            traffic_val = 80 if str(traffic).lower() == "high" else (float(traffic) if isinstance(traffic, (int, float)) else 0)
            return (p_sev >= 0.65) and (traffic_val >= 70)

        self.add_rule(RuleDefinition(
            rule_id="R04_LANE_CLOSURE_DIVERSION",
            title="Close Lane / Divert Heavy Vehicles",
            severity="critical",
            predicate=p_divert,
            message_template="Critical danger corridor ({prob_pct:.1f}% severe accident risk) under heavy traffic. Close curb lane and divert freight/heavy commercial vehicles.",
            category="advisory",
            priority=90
        ))

        # Rule 5: Night Driving Hazard
        def p_night(f: Fact) -> bool:
            tod = str(f.get("time_of_day", "")).lower()
            vis = float(f.get("visibility", 10.0))
            p_sev = float(f.get("risk_probability", 0.0))
            return (tod in ("night", "dark")) and (vis <= 6.0 or p_sev >= 0.40)

        self.add_rule(RuleDefinition(
            rule_id="R05_NIGHT_HAZARD",
            title="Night Driving Hazard with Reduced Sightline",
            severity="warning",
            predicate=p_night,
            message_template="Nighttime travel risk elevated ({prob_pct:.1f}% probability) with reduced contrast visibility. Watch for unlit obstacles and pedestrians.",
            category="advisory",
            priority=75
        ))

        # Rule 6: Heavy Traffic Gridlock & Shockwave Warning
        def p_congestion(f: Fact) -> bool:
            traffic = f.get("traffic_density", 0)
            traffic_val = 85 if str(traffic).lower() == "high" else (float(traffic) if isinstance(traffic, (int, float)) else 0)
            p_sev = float(f.get("risk_probability", 0.0))
            return (traffic_val >= 75) and (p_sev >= 0.40)

        self.add_rule(RuleDefinition(
            rule_id="R06_HIGH_CONGESTION_GRIDLOCK",
            title="Severe Congestion & Shockwave Warning",
            severity="warning",
            predicate=p_congestion,
            message_template="High vehicle volume detected under {prob_pct:.1f}% accident probability. Anticipate rapid deceleration waves; safe routing recommended.",
            category="advisory",
            priority=70
        ))

        # Rule 7: Torrential Downpour & Flash Flood
        def p_storm(f: Fact) -> bool:
            precip = float(f.get("precipitation", 0.0))
            weather = str(f.get("weather", "")).lower()
            p_sev = float(f.get("risk_probability", 0.0))
            return (precip >= 0.60 or weather in ("storm", "heavy_rain")) and (p_sev >= 0.50)

        self.add_rule(RuleDefinition(
            rule_id="R07_SEVERE_STORM",
            title="Flash Flood & Torrential Downpour Alert",
            severity="critical",
            predicate=p_storm,
            message_template="Heavy precipitation ({precipitation:.2f} in/hr) generating runoff pooling and {prob_pct:.1f}% crash likelihood. Do not enter flooded underpasses.",
            category="advisory",
            priority=92
        ))

        # Rule 8: Long Route Operator Fatigue Advisory
        def p_fatigue(f: Fact) -> bool:
            length = float(f.get("route_length_km", 0.0))
            tod = str(f.get("time_of_day", "")).lower()
            p_sev = float(f.get("risk_probability", 0.0))
            return (length >= 15.0) and (tod in ("night", "dusk") or p_sev >= 0.50)

        self.add_rule(RuleDefinition(
            rule_id="R08_LONG_ROUTE_FATIGUE",
            title="Extended Route Driver Fatigue Advisory",
            severity="info",
            predicate=p_fatigue,
            message_template="Extended transit distance ({route_length_km:.1f} km, {prob_pct:.1f}% trip risk). Operator cognitive fatigue increases collision likelihood; plan rest stops.",
            category="advisory",
            priority=50
        ))

        # Rule 9: Compound Multi-Hazard Danger Zone
        def p_compound(f: Fact) -> bool:
            adverse_weather = str(f.get("weather", "")).lower() in ("rain", "snow", "fog", "storm")
            tod = str(f.get("time_of_day", "")).lower() == "night"
            traffic = f.get("traffic_density", 0)
            high_traffic = str(traffic).lower() in ("high", "med") or (float(traffic) >= 50 if isinstance(traffic, (int, float)) else False)
            p_sev = float(f.get("risk_probability", 0.0))
            return adverse_weather and tod and high_traffic and (p_sev >= 0.50)

        self.add_rule(RuleDefinition(
            rule_id="R09_COMPOUND_HAZARD",
            title="Compound Multi-Factor Danger Zone",
            severity="critical",
            predicate=p_compound,
            message_template="Triple compounding hazard: adverse weather, night darkness, and dense traffic converge with {prob_pct:.1f}% severe accident risk.",
            category="advisory",
            priority=99
        ))

        # Rule 10: Dusk Twilight Glare
        def p_dusk(f: Fact) -> bool:
            tod = str(f.get("time_of_day", "")).lower()
            p_sev = float(f.get("risk_probability", 0.0))
            return (tod in ("dusk", "twilight")) and (p_sev >= 0.30)

        self.add_rule(RuleDefinition(
            rule_id="R10_DUSK_GLARE_CAUTION",
            title="Dusk Transition & Horizon Glare Caution",
            severity="info",
            predicate=p_dusk,
            message_template="Sun angle and twilight transition ({prob_pct:.1f}% risk). Clean windshields of road film and switch to active headlamps.",
            category="advisory",
            priority=60
        ))

        # Rule 11: Urban Intersection / Pedestrian Conflict Point
        def p_pedestrian(f: Fact) -> bool:
            vis = float(f.get("visibility", 10.0))
            traffic = f.get("traffic_density", 0)
            traffic_val = 60 if str(traffic).lower() in ("high", "med") else (float(traffic) if isinstance(traffic, (int, float)) else 0)
            p_sev = float(f.get("risk_probability", 0.0))
            return (vis <= 4.0) and (traffic_val >= 50) and (p_sev >= 0.45)

        self.add_rule(RuleDefinition(
            rule_id="R11_URBAN_PEDESTRIAN_CONFLICT",
            title="Heightened Intersection & Pedestrian Caution",
            severity="warning",
            predicate=p_pedestrian,
            message_template="Heightened pedestrian and cross-traffic conflict index ({prob_pct:.1f}% probability) under reduced sightline. Yield cautiously on permissive turns.",
            category="advisory",
            priority=72
        ))

        # Rule 12: Optimal Clear Conditions
        def p_optimal(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            weather = str(f.get("weather", "")).lower()
            surface = str(f.get("road_surface", "")).lower()
            tod = str(f.get("time_of_day", "")).lower()
            return (p_sev < 0.28) and (weather in ("clear", "sunny", "fair")) and (surface in ("dry", "")) and (tod in ("day", ""))

        self.add_rule(RuleDefinition(
            rule_id="R12_OPTIMAL_CONDITIONS",
            title="Optimal Roadway Conditions",
            severity="info",
            predicate=p_optimal,
            message_template="Favorable navigation conditions ({prob_pct:.1f}% baseline risk). Pavement is dry with unobstructed visibility. Standard speed limits apply.",
            category="advisory",
            priority=30
        ))

        # -------------------------------------------------------------------------
        # (b) INSURANCE UNDERWRITING RULES (4 Tiers with dynamic multipliers)
        # -------------------------------------------------------------------------

        # Rule 13: Tier A (Low Risk - Preferred Multiplier 0.95x)
        def p_tier_low(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            surface = str(f.get("road_surface", "")).lower()
            return (p_sev < 0.28) and (surface in ("dry", ""))

        self.add_rule(RuleDefinition(
            rule_id="R13_TIER_LOW",
            title="Underwriting Tier A (Low Risk - Preferred)",
            severity="info",
            predicate=p_tier_low,
            message_template="Actuarial risk {prob_pct:.1f}% qualifies for Tier A preferred rate.",
            category="underwriting",
            priority=10
        ))

        # Rule 14: Tier B (Standard Risk - Multiplier 1.15x)
        def p_tier_std(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            return 0.28 <= p_sev < 0.50

        self.add_rule(RuleDefinition(
            rule_id="R14_TIER_STANDARD",
            title="Underwriting Tier B (Standard Risk)",
            severity="info",
            predicate=p_tier_std,
            message_template="Actuarial risk {prob_pct:.1f}% falls into Tier B standard coverage.",
            category="underwriting",
            priority=20
        ))

        # Rule 15: Tier C (High Risk - Multiplier 1.45x)
        def p_tier_high(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            return 0.50 <= p_sev < 0.70

        self.add_rule(RuleDefinition(
            rule_id="R15_TIER_HIGH",
            title="Underwriting Tier C (High Risk - Surcharge)",
            severity="warning",
            predicate=p_tier_high,
            message_template="Actuarial risk {prob_pct:.1f}% mandates Tier C surcharge rate.",
            category="underwriting",
            priority=30
        ))

        # Rule 16: Tier D (Refer to Underwriting - Multiplier 2.10x)
        def p_tier_refer(f: Fact) -> bool:
            p_sev = float(f.get("risk_probability", 0.0))
            icy = str(f.get("road_surface", "")).lower() in ("icy", "ice")
            return (p_sev >= 0.70) or (icy and p_sev >= 0.55)

        self.add_rule(RuleDefinition(
            rule_id="R16_TIER_REFER",
            title="Underwriting Tier D (Refer to Underwriter)",
            severity="critical",
            predicate=p_tier_refer,
            message_template="Critical danger ({prob_pct:.1f}%) triggers manual Tier D referral.",
            category="underwriting",
            priority=40
        ))


# Singleton instance for high-throughput rule evaluation
_DEFAULT_ENGINE = None

def get_engine() -> KnowledgeEngine:
    """Returns singleton KnowledgeEngine instance."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = KnowledgeEngine()
    return _DEFAULT_ENGINE


def evaluate_rules(
    conditions: Dict[str, Any],
    route_stats: Optional[Dict[str, Any]] = None,
    risk_probability: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main evaluation entry point.
    Maps inputs to Working Memory Facts and executes the KnowledgeEngine.

    Parameters
    ----------
    conditions : dict
        Environmental observations (weather, road_surface, visibility, time_of_day, traffic_density, etc.)
    route_stats : dict, optional
        Route distance and exposure metrics (route_length_km, distance_miles, duration_minutes, etc.)
    risk_probability : float, optional
        Pre-computed risk probability from ML or BN. If omitted, derived from conditions or BN.

    Returns
    -------
    dict
        {
            "advisories": [...],
            "underwriting_tier": {...},
            "premium_multiplier": float,
            "fired_count": int
        }
    """
    engine = get_engine()
    engine.reset()

    # Determine risk probability
    if risk_probability is not None:
        p_sev = float(risk_probability)
    elif "risk_probability" in conditions:
        p_sev = float(conditions["risk_probability"])
    elif "p_severe" in conditions:
        p_sev = float(conditions["p_severe"])
    elif "xgb_risk" in conditions:
        p_sev = float(conditions["xgb_risk"])
    elif "xgboost_risk" in conditions:
        p_sev = float(conditions["xgboost_risk"])
    else:
        # Fallback heuristic if not provided
        p_sev = 0.20

    # Derive route length in km
    route_km = 0.0
    if route_stats:
        if "route_length_km" in route_stats:
            route_km = float(route_stats["route_length_km"])
        elif "distance_miles" in route_stats:
            route_km = float(route_stats["distance_miles"]) * 1.60934
        elif "distance_meters" in route_stats:
            route_km = float(route_stats["distance_meters"]) / 1000.0

    # Map time of day if hour provided
    tod = conditions.get("time_of_day")
    if not tod and "hour" in conditions:
        hour = int(conditions["hour"])
        if 7 <= hour <= 17:
            tod = "Day"
        elif 18 <= hour <= 20:
            tod = "Dusk"
        else:
            tod = "Night"
    elif not tod:
        tod = "Day"

    # Map road surface if precipitation given but surface not
    surface = conditions.get("road_surface")
    weather = conditions.get("weather", conditions.get("weather_condition", "Clear"))
    precip = float(conditions.get("precipitation", 0.0))
    if not surface:
        if str(weather).lower() == "snow":
            surface = "Icy"
        elif precip > 0.0 or str(weather).lower() in ("rain", "storm"):
            surface = "Wet"
        else:
            surface = "Dry"

    # Map visibility
    vis = float(conditions.get("visibility", 10.0))

    # Map traffic density
    density = conditions.get("traffic_density", 30)

    # Assert unified fact
    unified_fact = Fact(
        risk_probability=round(p_sev, 4),
        weather=weather,
        road_surface=surface,
        visibility=vis,
        time_of_day=tod,
        traffic_density=density,
        route_length_km=round(route_km, 2),
        precipitation=precip
    )

    engine.declare(unified_fact)
    return engine.run()
