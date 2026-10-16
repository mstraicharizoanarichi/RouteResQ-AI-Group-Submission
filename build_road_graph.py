import gzip
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OSM_FILE = BASE_DIR / "data" / "planet_88.842,25.692_89.011,25.914.osm.gz"
OUTPUT_FILE = BASE_DIR / "data" / "saidpur_road_graph.json"

# Roads usable by ordinary road vehicles.
ALLOWED_HIGHWAYS = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "unclassified", "residential",
    "living_street", "service", "road", "track"
}

def distance_meters(point_a, point_b):
    """Calculate the distance between two latitude/longitude points."""
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


def main():
    if not OSM_FILE.exists():
        print("ERROR: OSM file not found:")
        print(OSM_FILE)
        return

    print("Reading OpenStreetMap data...")
    print("Input:", OSM_FILE.name)

    nodes = {}
    road_ways = []

    # First pass: collect node coordinates and road-way references.
    with gzip.open(OSM_FILE, "rb") as osm:
        for _, element in ET.iterparse(osm, events=("end",)):
            if element.tag == "node":
                node_id = element.get("id")
                nodes[node_id] = (
                    float(element.get("lat")),
                    float(element.get("lon"))
                )

            elif element.tag == "way":
                tags = {
                    tag.get("k"): tag.get("v")
                    for tag in element.findall("tag")
                }

                highway = tags.get("highway", "")

                if highway in ALLOWED_HIGHWAYS:
                    refs = [
                        nd.get("ref")
                        for nd in element.findall("nd")
                    ]

                    if len(refs) >= 2:
                        road_ways.append({
                            "refs": refs,
                            "highway": highway,
                            "oneway": tags.get("oneway", "").lower(),
                            "junction": tags.get("junction", "").lower()
                        })

            if element.tag in ("node", "way"):
                element.clear()

    print("Nodes found:", len(nodes))
    print("Road ways found:", len(road_ways))

    graph = {}

    def add_edge(source, target, length):
        graph.setdefault(source, {})
        graph[source][target] = round(length, 2)

    missing_refs = 0
    edge_count = 0

    for way in road_ways:
        refs = way["refs"]
        oneway = way["oneway"]
        is_oneway = (
            oneway in {"yes", "true", "1"}
            or way["junction"] == "roundabout"
        )
        reverse_only = oneway == "-1"

        for first, second in zip(refs, refs[1:]):
            if first not in nodes or second not in nodes:
                missing_refs += 1
                continue

            length = distance_meters(nodes[first], nodes[second])

            if length <= 0:
                continue

            if reverse_only:
                add_edge(second, first, length)
                edge_count += 1
            else:
                add_edge(first, second, length)
                edge_count += 1

                if not is_oneway:
                    add_edge(second, first, length)
                    edge_count += 1

    road_graph = {
        "metadata": {
            "source": OSM_FILE.name,
            "distance_unit": "meters",
            "node_count": len(nodes),
            "road_way_count": len(road_ways),
            "graph_node_count": len(graph),
            "directed_edge_count": edge_count,
            "missing_references": missing_refs
        },
        "nodes": {
            node_id: {
                "lat": coords[0],
                "lon": coords[1]
            }
            for node_id, coords in nodes.items()
            if node_id in graph
        },
        "graph": graph
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        json.dump(road_graph, output, ensure_ascii=False)

    print()
    print("Road graph created successfully!")
    print("Output:", OUTPUT_FILE)
    print("Graph nodes:", len(graph))
    print("Directed edges:", edge_count)
    print("Missing node references:", missing_refs)
    print("File size:", OUTPUT_FILE.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

