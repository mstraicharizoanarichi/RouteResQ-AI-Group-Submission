import json
import heapq
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GRAPH_FILE = BASE_DIR / "data" / "saidpur_road_graph.json"


def haversine(point_a, point_b):
    """Estimate straight-line distance between two coordinates in meters."""
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
        math.sqrt(a), math.sqrt(max(0.0, 1.0 - a))
    )


def astar(graph, coordinates, start, destination):
    """Find a shortest-distance route using A*."""
    destination_coords = (
        coordinates[destination]["lat"],
        coordinates[destination]["lon"]
    )

    queue = [(0, start)]
    distance = {start: 0}
    previous = {start: None}

    while queue:
        _, current = heapq.heappop(queue)

        if current == destination:
            break

        for neighbor, road_distance in graph[current].items():
            new_distance = distance[current] + road_distance

            if new_distance < distance.get(neighbor, float("inf")):
                distance[neighbor] = new_distance
                previous[neighbor] = current

                neighbor_coords = (
                    coordinates[neighbor]["lat"],
                    coordinates[neighbor]["lon"]
                )

                heuristic = haversine(
                    neighbor_coords, destination_coords
                )

                priority = new_distance + heuristic
                heapq.heappush(queue, (priority, neighbor))

    if destination not in distance:
        return None, float("inf")

    path = []
    current = destination

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()
    return path, distance[destination]


def main():
    if not GRAPH_FILE.exists():
        print("ERROR: Road graph JSON file not found.")
        print(GRAPH_FILE)
        return

    print("Loading real OpenStreetMap road graph...")

    with GRAPH_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    graph = data["graph"]
    coordinates = data["nodes"]

    start = "5199558830"
    destination = "5443651886"

    if start not in graph or destination not in graph:
        print("ERROR: Start or destination node is missing.")
        return

    print("Start node:", start)
    print("Start coordinates:", coordinates[start])
    print("Destination node:", destination)
    print("Destination coordinates:", coordinates[destination])
    print("\nRunning A*...")

    path, total_distance = astar(
        graph, coordinates, start, destination
    )

    if path is None:
        print("\nNo directed route found between these nodes.")
        return

    print("\nA* route found successfully!")
    print("Number of route nodes:", len(path))
    print("Total road distance:", round(total_distance, 2), "meters")
    print("Total road distance:", round(total_distance / 1000, 3), "km")
    print("\nFirst 10 route nodes:")

    for node in path[:10]:
        print(
            node,
            coordinates[node]["lat"],
            coordinates[node]["lon"]
        )

    if len(path) > 10:
        print("...")

    print("\nA* test completed.")


if __name__ == "__main__":
    main()