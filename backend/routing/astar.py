"""
SafeRoute AI - Risk-Weighted A* & Graph Search Algorithms
Course Outcome Mapping:
    - CO2 (Informed and Uninformed Search):
      * Custom A* search implementation with admissible haversine heuristic
      * Plain Dijkstra search (uninformed search baseline)
      * Shortest-distance baseline search (lambda = 0)
    - CO1 (Intelligent Agent Models):
      * Goal-Based Utility Agent path planning balancing safety utility against latency

Mathematical Admissibility Proof:
    Edge Cost: c(u, v) = length(u, v) * (1 + lambda * edge_risk * env_multiplier)
    Since lambda >= 0, edge_risk >= 0, and env_multiplier > 0:
        c(u, v) >= length(u, v)
    The straight-line geodesic distance h(u, goal) satisfies:
        h(u, goal) <= distance_road(u, goal) <= true_cost(u, goal)
    Hence, h(u, goal) is strictly ADMISSIBLE and CONSISTENT (monotonic),
    guaranteeing that A* always finds an optimal path.
"""

import math
import heapq
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
import networkx as nx
import osmnx as ox

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
GRAPH_PATH = MODELS_DIR / "graph.graphml"

# Earth radius in meters for haversine heuristic
EARTH_RADIUS_METERS = 6371000.0

# In-memory graph singleton for sub-millisecond query latency
_GRAPH_SINGLETON: Optional[nx.MultiDiGraph] = None


def load_cached_graph(graph_path: Path = GRAPH_PATH, force_reload: bool = False) -> nx.MultiDiGraph:
    """
    Loads and caches the road network graph from models/graph.graphml.
    Pre-processes edge attributes (length, risk_score) to float for fast inner loop execution.
    """
    global _GRAPH_SINGLETON
    if _GRAPH_SINGLETON is not None and not force_reload:
        return _GRAPH_SINGLETON

    if not graph_path.exists():
        raise FileNotFoundError(f"Cached road graph not found at {graph_path}. Run ml/edge_risk.py first.")

    G = ox.load_graphml(graph_path)

    # Cast string attributes to float once during load to maximize search speed
    for _, _, _, data in G.edges(keys=True, data=True):
        try:
            data["length"] = float(data.get("length", 15.0))
        except (ValueError, TypeError):
            data["length"] = 15.0

        try:
            data["risk_score"] = float(data.get("risk_score", data.get("base_risk", 0.15)))
        except (ValueError, TypeError):
            data["risk_score"] = 0.15

        # Speed limit parsing
        maxspeed_raw = str(data.get("maxspeed", "30")).lower().replace("mph", "").strip()
        try:
            speed_mph = float(maxspeed_raw.split()[0])
        except Exception:
            speed_mph = 30.0
        data["speed_mps"] = max(5.0, speed_mph * 0.44704)  # convert mph to m/s

    _GRAPH_SINGLETON = G
    return _GRAPH_SINGLETON


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance (meters) between two points on the sphere.
    Used as an admissible heuristic for A* search.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def find_nearest_node(G: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """Finds closest node in the road network to given coordinates."""
    return int(ox.distance.nearest_nodes(G, X=lon, Y=lat))


def calculate_edge_cost(
    length: float,
    edge_risk: float,
    safety_lambda: float,
    env_multiplier: float
) -> float:
    """
    Calculates risk-weighted edge cost:
        cost = length * (1.0 + safety_lambda * edge_risk * env_multiplier)
    """
    return length * (1.0 + safety_lambda * edge_risk * env_multiplier)


def astar_search(
    G: nx.MultiDiGraph,
    source_node: int,
    target_node: int,
    safety_lambda: float = 1.5,
    env_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    Custom A* search algorithm using priority queue (heapq) and closed set.
    Heuristic: Haversine geodesic distance to target node (strictly admissible).

    Parameters
    ----------
    G : nx.MultiDiGraph
        The road graph.
    source_node : int
        Origin graph node ID.
    target_node : int
        Destination graph node ID.
    safety_lambda : float, default 1.5
        Trade-off parameter weighting risk penalties vs travel distance.
    env_multiplier : float, default 1.0
        Dynamic multiplier derived from live weather/BN risk.

    Returns
    -------
    dict
        Route dictionary with coordinates, GeoJSON, metrics, and nodes expanded.
    """
    target_lat = G.nodes[target_node]["y"]
    target_lon = G.nodes[target_node]["x"]

    # Priority queue storing tuples of (f_score, counter, current_node)
    counter = 0
    start_h = haversine_distance(G.nodes[source_node]["y"], G.nodes[source_node]["x"], target_lat, target_lon)
    open_heap = [(start_h, counter, source_node)]

    # Cost from start along best known path
    g_score: Dict[int, float] = {source_node: 0.0}

    # Tracking predecessors for path reconstruction: node -> (predecessor_node, edge_data)
    came_from: Dict[int, Tuple[int, Dict[str, Any]]] = {}

    closed_set: Set[int] = set()
    nodes_expanded = 0

    while open_heap:
        current_f, _, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue

        closed_set.add(current)
        nodes_expanded += 1

        if current == target_node:
            return _reconstruct_route(G, came_from, source_node, target_node, nodes_expanded, algorithm="A*")

        current_g = g_score[current]

        # Explore outgoing neighbors
        for neighbor in G.neighbors(current):
            if neighbor in closed_set:
                continue

            # Pick edge with minimum cost among multigraph parallel edges
            best_edge_data = None
            min_cost = float("inf")

            for key, data in G[current][neighbor].items():
                e_len = data["length"]
                e_risk = data["risk_score"]
                cost = calculate_edge_cost(e_len, e_risk, safety_lambda, env_multiplier)
                if cost < min_cost:
                    min_cost = cost
                    best_edge_data = data

            if best_edge_data is None:
                continue

            tentative_g = current_g + min_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = (current, best_edge_data)

                n_lat = G.nodes[neighbor]["y"]
                n_lon = G.nodes[neighbor]["x"]
                h_cost = haversine_distance(n_lat, n_lon, target_lat, target_lon)
                f_cost = tentative_g + h_cost

                counter += 1
                heapq.heappush(open_heap, (f_cost, counter, neighbor))

    raise nx.NetworkXNoPath(f"No path found between node {source_node} and {target_node}.")


def dijkstra_search(
    G: nx.MultiDiGraph,
    source_node: int,
    target_node: int,
    safety_lambda: float = 1.5,
    env_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    Plain Dijkstra search algorithm (uninformed baseline with h = 0).
    Uses identical cost function as A* to benchmark search efficiency (nodes expanded).
    """
    counter = 0
    open_heap = [(0.0, counter, source_node)]
    g_score: Dict[int, float] = {source_node: 0.0}
    came_from: Dict[int, Tuple[int, Dict[str, Any]]] = {}
    closed_set: Set[int] = set()
    nodes_expanded = 0

    while open_heap:
        current_g, _, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue

        closed_set.add(current)
        nodes_expanded += 1

        if current == target_node:
            return _reconstruct_route(G, came_from, source_node, target_node, nodes_expanded, algorithm="Dijkstra")

        for neighbor in G.neighbors(current):
            if neighbor in closed_set:
                continue

            best_edge_data = None
            min_cost = float("inf")

            for key, data in G[current][neighbor].items():
                e_len = data["length"]
                e_risk = data["risk_score"]
                cost = calculate_edge_cost(e_len, e_risk, safety_lambda, env_multiplier)
                if cost < min_cost:
                    min_cost = cost
                    best_edge_data = data

            if best_edge_data is None:
                continue

            tentative_g = current_g + min_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = (current, best_edge_data)
                counter += 1
                heapq.heappush(open_heap, (tentative_g, counter, neighbor))

    raise nx.NetworkXNoPath(f"No Dijkstra path found between node {source_node} and {target_node}.")


def shortest_distance_search(
    G: nx.MultiDiGraph,
    source_node: int,
    target_node: int
) -> Dict[str, Any]:
    """
    Shortest-distance baseline search (lambda = 0.0).
    Finds the strictly fastest/shortest path ignoring safety risk scores.
    """
    return astar_search(G, source_node, target_node, safety_lambda=0.0, env_multiplier=1.0)


def _reconstruct_route(
    G: nx.MultiDiGraph,
    came_from: Dict[int, Tuple[int, Dict[str, Any]]],
    source_node: int,
    target_node: int,
    nodes_expanded: int,
    algorithm: str = "A*"
) -> Dict[str, Any]:
    """
    Traces back through came_from dictionary to compile detailed path geometry and metrics.
    """
    curr = target_node
    path_edges: List[Dict[str, Any]] = []
    path_nodes: List[int] = [target_node]

    while curr != source_node:
        if curr not in came_from:
            break
        prev, edge_data = came_from[curr]
        path_edges.append(edge_data)
        path_nodes.append(prev)
        curr = prev

    path_nodes.reverse()
    path_edges.reverse()

    # Build sequence of coordinates: [lat, lon] for Leaflet and [lon, lat] for GeoJSON
    coords_lat_lon: List[List[float]] = []
    coords_lon_lat: List[List[float]] = []

    total_meters = 0.0
    total_travel_time_sec = 0.0
    risk_length_product = 0.0

    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        edge_data = path_edges[i]

        e_len = edge_data["length"]
        e_risk = edge_data["risk_score"]
        speed_mps = edge_data.get("speed_mps", 13.4)

        total_meters += e_len
        total_travel_time_sec += (e_len / speed_mps)
        risk_length_product += (e_len * e_risk)

        # Extract geometry if present, otherwise interpolate endpoints
        if "geometry" in edge_data and edge_data["geometry"] is not None:
            geom = edge_data["geometry"]
            # Shapely LineString coordinates are (x, y) = (lon, lat)
            points = list(geom.coords)
            for x, y in points:
                if not coords_lat_lon or coords_lat_lon[-1] != [y, x]:
                    coords_lat_lon.append([round(y, 6), round(x, 6)])
                    coords_lon_lat.append([round(x, 6), round(y, 6)])
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            if not coords_lat_lon:
                coords_lat_lon.append([round(u_node["y"], 6), round(u_node["x"], 6)])
                coords_lon_lat.append([round(u_node["x"], 6), round(u_node["y"], 6)])
            coords_lat_lon.append([round(v_node["y"], 6), round(v_node["x"], 6)])
            coords_lon_lat.append([round(v_node["x"], 6), round(v_node["y"], 6)])

    distance_miles = round(total_meters / 1609.344, 2)
    duration_minutes = round(total_travel_time_sec / 60.0, 1)
    # Average weighted risk along the route [0.0 - 1.0]
    avg_risk = round(risk_length_product / max(1.0, total_meters), 4)

    # Street summary from major edges
    street_names = [e.get("name") for e in path_edges if e.get("name") and isinstance(e.get("name"), str)]
    summary_street = street_names[0] if street_names else "Urban Corridor"

    geojson_feature = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coords_lon_lat
        },
        "properties": {
            "algorithm": algorithm,
            "distance_meters": round(total_meters, 1),
            "distance_miles": distance_miles,
            "duration_minutes": duration_minutes,
            "total_risk_score": avg_risk,
            "nodes_expanded": nodes_expanded,
            "nodes_count": len(path_nodes)
        }
    }

    return {
        "algorithm": algorithm,
        "coordinates": coords_lat_lon,  # [[lat, lon], ...] matching frontend RoutePath
        "geojson": geojson_feature,
        "distance_meters": round(total_meters, 1),
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
        "total_risk_score": avg_risk,
        "nodes_expanded": nodes_expanded,
        "nodes_count": len(path_nodes),
        "summary_street": summary_street
    }


def get_top_high_risk_zones(
    G: Optional[nx.MultiDiGraph] = None,
    limit: int = 25,
    min_risk_threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Extracts top accident-prone road segments as GeoJSON and HighRiskZone objects
    for map heatmap visualization.
    """
    if G is None:
        G = load_cached_graph()

    extracted = []
    seen_cells = set()

    for u, v, k, data in G.edges(keys=True, data=True):
        risk = float(data.get("risk_score", 0.0))
        if risk < min_risk_threshold:
            continue

        mid_lat = float(data.get("mid_lat", 0.0))
        mid_lng = float(data.get("mid_lng", 0.0))
        if mid_lat == 0.0:
            mid_lat = (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2.0
            mid_lng = (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2.0

        # Discretize to prevent visual clustering clutter
        cell_key = (round(mid_lat, 3), round(mid_lng, 3))
        if cell_key in seen_cells:
            continue
        seen_cells.add(cell_key)

        extracted.append({
            "u": u,
            "v": v,
            "lat": round(mid_lat, 6),
            "lng": round(mid_lng, 6),
            "risk_score": round(risk, 4),
            "name": data.get("name", "High Risk Junction"),
            "highway": data.get("highway", "arterial"),
            "geometry": data.get("geometry")
        })

    # Sort descending by risk score
    extracted.sort(key=lambda x: x["risk_score"], reverse=True)
    top_items = extracted[:limit]

    # Build HighRiskZone list matching frontend types.ts
    high_risk_zones = []
    features = []

    for idx, item in enumerate(top_items):
        risk_val = item["risk_score"]
        if risk_val >= 0.70:
            severity = "hot"
        elif risk_val >= 0.55:
            severity = "warm"
        else:
            severity = "cold"

        loc_name = str(item["name"]) if item["name"] else f"Intersection #{item['u']}"
        cause_desc = f"Historical multi-vehicle collision cluster ({int(risk_val * 100)}% severe risk)"

        zone = {
            "id": f"zone_{idx + 1}",
            "lat": item["lat"],
            "lng": item["lng"],
            "radius": 220,  # meters
            "risk_score": risk_val,
            "severity": severity,
            "cause": cause_desc,
            "location_name": loc_name
        }
        high_risk_zones.append(zone)

        # GeoJSON Point Feature
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [item["lng"], item["lat"]]
            },
            "properties": zone
        })

    return {
        "high_risk_zones": high_risk_zones,
        "geojson": {
            "type": "FeatureCollection",
            "features": features
        }
    }


def find_safe_and_fastest_routes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    conditions: Optional[Dict[str, Any]] = None,
    safety_lambda: float = 1.5,
    live_risk: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main routing facade.
    Calculates both:
    1. Safe Route (Risk-Weighted A*)
    2. Baseline Fastest Route (lambda = 0)
    Along with comparative metrics and high-risk zones.
    """
    G = load_cached_graph()

    # Map origin and destination to nearest nodes
    source_node = find_nearest_node(G, origin[0], origin[1])
    target_node = find_nearest_node(G, destination[0], destination[1])

    if source_node == target_node:
        raise ValueError("Origin and destination snapped to the exact same road node.")

    # Compute environmental multiplier
    if live_risk is None and conditions:
        from ml.edge_risk import predict_risk
        live_risk = predict_risk(conditions)

    if live_risk is not None:
        # Normalize around typical baseline ~0.20
        env_multiplier = max(0.5, min(4.0, float(live_risk) / 0.20))
    else:
        env_multiplier = 1.0

    # 1. Compute Safe Route via A*
    safe_route = astar_search(
        G, source_node, target_node,
        safety_lambda=safety_lambda,
        env_multiplier=env_multiplier
    )

    # 2. Compute Baseline Fastest Route (lambda = 0.0)
    fastest_route = shortest_distance_search(G, source_node, target_node)

    # Compute comparative savings
    f_risk = fastest_route["total_risk_score"]
    s_risk = safe_route["total_risk_score"]
    if f_risk > 0:
        risk_reduction_pct = max(0.0, round(((f_risk - s_risk) / f_risk) * 100.0, 1))
    else:
        risk_reduction_pct = 0.0

    dist_delta = round(safe_route["distance_miles"] - fastest_route["distance_miles"], 2)
    dur_delta = round(safe_route["duration_minutes"] - fastest_route["duration_minutes"], 1)

    # Fetch high-risk zones
    risk_zones_data = get_top_high_risk_zones(G, limit=20)

    return {
        "safe_route": safe_route,
        "fastest_route": fastest_route,
        "comparison": {
            "risk_reduction_percent": risk_reduction_pct,
            "distance_delta_miles": dist_delta,
            "duration_delta_minutes": dur_delta,
            "fastest_risk": f_risk,
            "safest_risk": s_risk
        },
        "high_risk_zones": risk_zones_data["high_risk_zones"],
        "risk_zones_geojson": risk_zones_data["geojson"]
    }
