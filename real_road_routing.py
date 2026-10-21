
import hashlib
import heapq
import json
import math
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
GRAPH_FILE = BASE_DIR / "data" / "saidpur_road_graph.json"


PLACES = {
    "University": "14184130502",
    "Main Road": "9062232091",
    "Hospital": "11411731976",
    "Market": "5463464040",
}


# Simulated congestion severity.
# These are simulation parameters, not real traffic measurements.
TRAFFIC_LEVELS = {
    "low": 0.15,
    "medium": 0.80,
    "high": 2.00,
}


def haversine(point_a, point_b):
    """Calculate straight-line distance between coordinates in meters."""

    lat1, lon1 = map(math.radians, point_a)
    lat2, lon2 = map(math.radians, point_b)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 6371000 * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(max(0.0, 1.0 - a))
    )


class RealRoadRouter:

    def __init__(self):
        if not GRAPH_FILE.exists():
            raise FileNotFoundError(
                f"Road graph not found: {GRAPH_FILE}"
            )

        with GRAPH_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self.graph = data["graph"]
        self.nodes = data["nodes"]

    @staticmethod
    def congestion_factor(source, target, traffic_level):
        """Generate repeatable simulated road congestion."""

        severity = TRAFFIC_LEVELS[traffic_level]

        road_key = ":".join(
            sorted((str(source), str(target)))
        )

        digest = hashlib.sha256(
            road_key.encode("utf-8")
        ).hexdigest()

        congestion = int(digest[:8], 16) / 0xFFFFFFFF

        return 1.0 + congestion * severity

    def find_nearest_node(self, latitude, longitude):
        """Find the nearest road-graph node to a map coordinate."""

        latitude = float(latitude)
        longitude = float(longitude)

        if (
            not math.isfinite(latitude)
            or not math.isfinite(longitude)
        ):
            raise ValueError(
                "Coordinates must be finite numbers."
            )

        if not -90 <= latitude <= 90:
            raise ValueError("Invalid latitude.")

        if not -180 <= longitude <= 180:
            raise ValueError("Invalid longitude.")

        selected_point = (latitude, longitude)

        nearest_node = min(
            self.nodes.items(),
            key=lambda item: haversine(
                selected_point,
                (
                    item[1]["lat"],
                    item[1]["lon"]
                )
            )
        )

        node_id, node_data = nearest_node

        distance = haversine(
            selected_point,
            (
                node_data["lat"],
                node_data["lon"]
            )
        )

        return {
            "node_id": node_id,
            "latitude": node_data["lat"],
            "longitude": node_data["lon"],
            "distance_meters": round(distance, 2),
        }

    def find_route(
        self,
        start_name,
        destination_name,
        traffic_level="low",
        emergency_vehicle=False,
        blocked_roads=None,
        accident_roads=None
    ):
        """
        Find a traffic-adjusted A* route.

        blocked_roads:
            Optional collection of road segments to avoid.
            Each segment is a pair of road-node IDs, for example:
            [("node_A", "node_B")].

        Road closures are simulated. The original graph is never changed.
        Emergency mode reduces the simulated congestion penalty.
        """

        # Allow either a named place or a road-graph node ID.
        start_key = str(start_name)
        destination_key = str(destination_name)

        start = PLACES.get(start_key, start_key)
        destination = PLACES.get(
            destination_key,
            destination_key
        )

        traffic_level = str(traffic_level).lower()

        if not isinstance(emergency_vehicle, bool):
            raise ValueError(
                "emergency_vehicle must be True or False."
            )

        if traffic_level not in TRAFFIC_LEVELS:
            raise ValueError(
                "Traffic level must be low, medium, or high."
            )

        # Normalize simulated accident segments.
        normalized_accident_roads = set()
        for road in accident_roads or []:
            if not isinstance(road, (list, tuple)) or len(road) != 2:
                raise ValueError(
                    "Each accident road must contain two node IDs."
                )
            source_node, target_node = map(str, road)
            if (
                source_node not in self.nodes
                or target_node not in self.nodes
            ):
                raise ValueError(
                    "An accident road contains an unknown node ID."
                )
            if source_node == target_node:
                raise ValueError(
                    "An accident road must connect two different nodes."
                )
            normalized_accident_roads.add(
                frozenset((source_node, target_node))
            )

        # Normalize closed road segments.
        # A segment is considered closed in both directions.
        if blocked_roads is None:
            blocked_roads = []

        normalized_blocked_roads = set()

        for road in blocked_roads:
            if not isinstance(road, (list, tuple)) or len(road) != 2:
                raise ValueError(
                    "Each blocked road must contain two node IDs."
                )

            source_node, target_node = map(str, road)

            if (
                source_node not in self.nodes
                or target_node not in self.nodes
            ):
                raise ValueError(
                    "A blocked road contains an unknown node ID."
                )

            normalized_blocked_roads.add(
                frozenset((source_node, target_node))
            )

        if start not in self.nodes:
            raise ValueError(
                f"Start road node not found: {start}"
            )

        if destination not in self.nodes:
            raise ValueError(
                f"Destination road node not found: {destination}"
            )

        if start == destination:
            node = self.nodes[start]

            return {
                "route": [start],
                "coordinates": [[node["lat"], node["lon"]]],
                "distance_meters": 0.0,
                "distance_km": 0.0,
                "route_nodes": 1,
                "traffic_level": traffic_level,
                "traffic_cost": 0.0,
                "emergency_vehicle": emergency_vehicle,
                "blocked_roads_avoided": len(
                    normalized_blocked_roads
                ),
            }

        destination_point = (
            self.nodes[destination]["lat"],
            self.nodes[destination]["lon"]
        )

        # A* queue:
        # (estimated total cost, actual cost, node ID)
        initial_point = (
            self.nodes[start]["lat"],
            self.nodes[start]["lon"]
        )

        initial_heuristic = haversine(
            initial_point,
            destination_point
        )

        queue = [(initial_heuristic, 0.0, start)]

        costs = {start: 0.0}
        distances = {start: 0.0}
        previous = {start: None}

        while queue:
            _, current_cost, current = heapq.heappop(queue)

            if current_cost > costs.get(
                current, float("inf")
            ):
                continue

            if current == destination:
                break

            for neighbor, road_distance in self.graph.get(
                current, {}
            ).items():

                # Skip closed road segments in either direction.
                if frozenset(
                    (str(current), str(neighbor))
                ) in normalized_blocked_roads:
                    continue

                road_distance = float(road_distance)

                if (
                    not math.isfinite(road_distance)
                    or road_distance < 0
                ):
                    continue

                factor = self.congestion_factor(
                    current,
                    neighbor,
                    traffic_level
                )

                # Emergency routing reduces the simulated
                # congestion penalty on each road.
                if emergency_vehicle:
                    factor = 1.0 + (factor - 1.0) * 0.35

                # Simulated accident: triple this segment cost.
                if frozenset((str(current), str(neighbor))) in normalized_accident_roads:
                    factor *= 3.0

                edge_cost = road_distance * factor
                new_cost = current_cost + edge_cost

                if new_cost < costs.get(
                    neighbor, float("inf")
                ):
                    costs[neighbor] = new_cost

                    distances[neighbor] = (
                        distances[current] + road_distance
                    )

                    previous[neighbor] = current

                    neighbor_point = (
                        self.nodes[neighbor]["lat"],
                        self.nodes[neighbor]["lon"]
                    )

                    heuristic = haversine(
                        neighbor_point,
                        destination_point
                    )

                    heapq.heappush(
                        queue,
                        (
                            new_cost + heuristic,
                            new_cost,
                            neighbor
                        )
                    )

        # No available route after avoiding closed roads.
        if destination not in costs:
            return None

        # Reconstruct the route.
        path = []
        current = destination

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        coordinates = [
            [
                self.nodes[node]["lat"],
                self.nodes[node]["lon"]
            ]
            for node in path
        ]

        total_distance = distances[destination]
        total_traffic_cost = costs[destination]

        return {
            "route": path,
            "coordinates": coordinates,
            "distance_meters": round(total_distance, 2),
            "distance_km": round(total_distance / 1000, 3),
            "route_nodes": len(path),
            "traffic_level": traffic_level,
            "traffic_cost": round(total_traffic_cost, 2),
            "emergency_vehicle": emergency_vehicle,
            "blocked_roads_avoided": len(
                normalized_blocked_roads
            ),
        }


    def compare_algorithms(
        self, start_name, destination_name,
        traffic_level="low", emergency_vehicle=False,
        blocked_roads=None, accident_roads=None
    ):
        """Compare A* and Dijkstra using identical edge costs."""
        import time

        start = PLACES.get(str(start_name), str(start_name))
        goal = PLACES.get(str(destination_name), str(destination_name))
        traffic_level = str(traffic_level).lower()

        if traffic_level not in TRAFFIC_LEVELS:
            raise ValueError("Traffic level must be low, medium, or high.")
        if not isinstance(emergency_vehicle, bool):
            raise ValueError("emergency_vehicle must be True or False.")
        if start not in self.nodes or goal not in self.nodes:
            raise ValueError("Start or destination road node not found.")

        blocked = set()
        for road in blocked_roads or []:
            if not isinstance(road, (list, tuple)) or len(road) != 2:
                raise ValueError("Each blocked road must contain two node IDs.")
            a, b = map(str, road)
            if a not in self.nodes or b not in self.nodes:
                raise ValueError("A blocked road contains an unknown node ID.")
            blocked.add(frozenset((a, b)))

        accident = set()
        for road in accident_roads or []:
            if not isinstance(road, (list, tuple)) or len(road) != 2:
                raise ValueError("Each accident road must contain two node IDs.")
            a, b = map(str, road)
            if a not in self.nodes or b not in self.nodes:
                raise ValueError("An accident road contains an unknown node ID.")
            if a == b:
                raise ValueError("An accident road must connect two different nodes.")
            accident.add(frozenset((a, b)))

        goal_point = (self.nodes[goal]["lat"], self.nodes[goal]["lon"])

        def search(use_heuristic):
            started = time.perf_counter()
            queue = [(0.0, 0.0, start)]
            costs = {start: 0.0}
            distances = {start: 0.0}
            previous = {start: None}
            expanded = 0

            while queue:
                _, cost, current = heapq.heappop(queue)
                if cost > costs.get(current, float("inf")):
                    continue

                expanded += 1
                if current == goal:
                    break

                for neighbor, raw_distance in self.graph.get(current, {}).items():
                    if frozenset((str(current), str(neighbor))) in blocked:
                        continue

                    distance = float(raw_distance)
                    if not math.isfinite(distance) or distance < 0:
                        continue

                    factor = self.congestion_factor(
                        current, neighbor, traffic_level
                    )
                    if emergency_vehicle:
                        factor = 1.0 + (factor - 1.0) * 0.35

                    # Both A* and Dijkstra use the same accident penalty.
                    if frozenset((str(current), str(neighbor))) in accident:
                        factor *= 3.0

                    new_cost = cost + distance * factor
                    if new_cost >= costs.get(neighbor, float("inf")):
                        continue

                    costs[neighbor] = new_cost
                    distances[neighbor] = distances[current] + distance
                    previous[neighbor] = current

                    heuristic = 0.0
                    if use_heuristic:
                        point = (
                            self.nodes[neighbor]["lat"],
                            self.nodes[neighbor]["lon"]
                        )
                        heuristic = haversine(point, goal_point)

                    heapq.heappush(
                        queue, (new_cost + heuristic, new_cost, neighbor)
                    )

            elapsed_ms = (time.perf_counter() - started) * 1000

            if goal not in costs:
                return {
                    "found": False,
                    "execution_time_ms": round(elapsed_ms, 3),
                    "expanded_nodes": expanded,
                    "route": [],
                    "distance_km": None,
                    "traffic_cost": None,
                }

            route = []
            node = goal
            while node is not None:
                route.append(node)
                node = previous[node]
            route.reverse()

            return {
                "found": True,
                "execution_time_ms": round(elapsed_ms, 3),
                "expanded_nodes": expanded,
                "route": route,
                "distance_km": round(distances[goal] / 1000, 3),
                "traffic_cost": round(costs[goal], 2),
            }

        return {
            "A*": search(True),
            "Dijkstra": search(False),
            "traffic_level": traffic_level,
            "emergency_vehicle": emergency_vehicle,
            "blocked_roads_count": len(blocked),
            "accident_roads_count": len(accident),
        }


if __name__ == "__main__":
    router = RealRoadRouter()

    for level in ("low", "medium", "high"):
        for emergency in (False, True):
            result = router.find_route(
                "University",
                "Market",
                traffic_level=level,
                emergency_vehicle=emergency
            )

            print(
                f"\nTraffic: {level} | "
                f"Emergency: {emergency}"
            )

            if result is None:
                print("No route found.")
            else:
                print("Distance:", result["distance_km"], "km")
                print("Route nodes:", result["route_nodes"])
                print("Traffic cost:", result["traffic_cost"])

    print("\nEmergency-priority routing test completed.")
