import json
from collections import deque
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GRAPH_FILE = BASE_DIR / "data" / "saidpur_road_graph.json"

PLACES = {
    "University": "14184130502",
    "Main Road": "9062232091",
    "Hospital": "11411731976",
    "Market": "5463464040",
}


def is_reachable(graph, start, destination):
    queue = deque([start])
    visited = {start}

    while queue:
        current = queue.popleft()

        if current == destination:
            return True

        for neighbor in graph.get(current, {}):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False


def main():
    with GRAPH_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    graph = data["graph"]

    print("Real Road Graph: Location Connectivity Test")
    print("-" * 45)

    for start_name, start_node in PLACES.items():
        for end_name, end_node in PLACES.items():
            if start_name == end_name:
                continue

            result = is_reachable(graph, start_node, end_node)
            status = "Reachable" if result else "NO ROUTE"

            print(f"{start_name} -> {end_name}: {status}")


if __name__ == "__main__":
    main()