
from flask import Flask, render_template, request, jsonify

from real_road_routing import RealRoadRouter

import json
import math

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


app = Flask(__name__)

# Load the locally stored OpenStreetMap road graph.
router = RealRoadRouter()


@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# Search for a location using OpenStreetMap Nominatim
# --------------------------------------------------

@app.route("/search-location", methods=["GET"])
def search_location():
    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify({
            "error": "Please enter at least two characters."
        }), 400

    params = {
        "q": f"{query}, Saidpur, Nilphamari, Bangladesh",
        "format": "jsonv2",
        "limit": 5,
        "viewbox": "88.82,25.97,89.04,25.67",
        "bounded": 1
    }

    url = (
        "https://nominatim.openstreetmap.org/search?"
        + urlencode(params)
    )

    req = Request(
        url,
        headers={
            "User-Agent": "RouteResQAI/1.0 (academic project)",
            "Accept-Language": "en"
        }
    )

    try:
        with urlopen(req, timeout=15) as response:
            places = json.loads(
                response.read().decode("utf-8")
            )

        results = []

        for place in places:
            results.append({
                "name": place.get("display_name", query),
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"])
            })

        return jsonify({
            "results": results,
            "count": len(results)
        })

    except HTTPError as error:
        app.logger.warning(
            "Nominatim returned HTTP status %s",
            error.code
        )

        return jsonify({
            "error": (
                "The location search service is temporarily unavailable."
            )
        }), 502

    except (
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
        KeyError
    ):
        return jsonify({
            "error": (
                "Location search failed. Check your internet "
                "connection and try again."
            )
        }), 502


# --------------------------------------------------
# Validate simulated road closures
# --------------------------------------------------

def validate_blocked_roads(blocked_roads):
    """
    Validate road segments supplied by the client.

    Expected format:
    [
        ["node_id_1", "node_id_2"],
        ["node_id_3", "node_id_4"]
    ]

    A closed segment is treated as unavailable in both directions.
    """

    if not isinstance(blocked_roads, list):
        raise ValueError(
            "blocked_roads must be a list of road-node pairs."
        )

    if len(blocked_roads) > 100:
        raise ValueError(
            "A maximum of 100 road closures is allowed per request."
        )

    validated_roads = []
    seen_roads = set()

    for road in blocked_roads:

        if not isinstance(road, (list, tuple)) or len(road) != 2:
            raise ValueError(
                "Each blocked road must contain exactly two node IDs."
            )

        source, target = road

        if (
            not isinstance(source, (str, int))
            or isinstance(source, bool)
            or not isinstance(target, (str, int))
            or isinstance(target, bool)
        ):
            raise ValueError(
                "Road node IDs must be strings or integers."
            )

        source = str(source)
        target = str(target)

        if source not in router.nodes or target not in router.nodes:
            raise ValueError(
                "A blocked road contains an unknown node ID."
            )

        if source == target:
            raise ValueError(
                "A road closure must connect two different nodes."
            )

        # Confirm that the requested segment exists in the graph.
        forward_exists = target in router.graph.get(source, {})
        reverse_exists = source in router.graph.get(target, {})

        if not forward_exists and not reverse_exists:
            raise ValueError(
                f"No mapped road segment exists between "
                f"nodes {source} and {target}."
            )

        # Deduplicate the same physical segment.
        road_key = frozenset((source, target))

        if road_key not in seen_roads:
            seen_roads.add(road_key)
            validated_roads.append((source, target))

    return validated_roads


# --------------------------------------------------
# Calculate traffic-aware routes using A*
# --------------------------------------------------

@app.route("/find-route", methods=["POST"])
def find_route():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a valid JSON object."
        }), 400

    start_name = data.get("start", "University")
    destination_name = data.get("destination", "Market")

    traffic_level = str(data.get("traffic", "low")).lower()
    emergency_vehicle = data.get("emergency", False)

    # Validate emergency flag.
    if not isinstance(emergency_vehicle, bool):
        return jsonify({
            "error": "Emergency must be true or false."
        }), 400

    # Validate traffic level.
    if traffic_level not in {"low", "medium", "high"}:
        return jsonify({
            "error": "Traffic must be low, medium, or high."
        }), 400

    try:
        # Validate requested road closures.
        blocked_roads = validate_blocked_roads(
            data.get("blocked_roads", [])
        )

        # Coordinates may come from map clicks or search results.
        start_coordinates = data.get("start_coordinates")

        destination_coordinates = data.get(
            "destination_coordinates"
        )

        if (
            start_coordinates is not None
            or destination_coordinates is not None
        ):
            if (
                not isinstance(start_coordinates, (list, tuple))
                or len(start_coordinates) != 2
            ):
                return jsonify({
                    "error": (
                        "start_coordinates must be "
                        "[latitude, longitude]."
                    )
                }), 400

            if (
                not isinstance(destination_coordinates, (list, tuple))
                or len(destination_coordinates) != 2
            ):
                return jsonify({
                    "error": (
                        "destination_coordinates must be "
                        "[latitude, longitude]."
                    )
                }), 400

            try:
                start_lat, start_lon = map(
                    float, start_coordinates
                )

                dest_lat, dest_lon = map(
                    float, destination_coordinates
                )

            except (TypeError, ValueError):
                return jsonify({
                    "error": "Coordinates must be numeric."
                }), 400

            # Reject NaN and infinity.
            if not all(map(math.isfinite, (
                start_lat,
                start_lon,
                dest_lat,
                dest_lon
            ))):
                return jsonify({
                    "error": "Coordinates must be finite numbers."
                }), 400

            # Validate geographic coordinate ranges.
            if not (
                -90 <= start_lat <= 90
                and -180 <= start_lon <= 180
                and -90 <= dest_lat <= 90
                and -180 <= dest_lon <= 180
            ):
                return jsonify({
                    "error": (
                        "Coordinates are outside valid "
                        "geographic ranges."
                    )
                }), 400

            # Snap selected coordinates to nearby road nodes.
            start_nearest = router.find_nearest_node(
                start_lat,
                start_lon
            )

            destination_nearest = router.find_nearest_node(
                dest_lat,
                dest_lon
            )

            # Reject locations too far from mapped roads.
            max_snap_distance_meters = 2000

            if (
                start_nearest["distance_meters"]
                > max_snap_distance_meters
            ):
                return jsonify({
                    "error": (
                        "The selected start location is too far "
                        "from a mapped road. Please select a "
                        "location closer to a road."
                    )
                }), 400

            if (
                destination_nearest["distance_meters"]
                > max_snap_distance_meters
            ):
                return jsonify({
                    "error": (
                        "The selected destination is too far "
                        "from a mapped road. Please select a "
                        "location closer to a road."
                    )
                }), 400

            start_node = start_nearest["node_id"]
            destination_node = destination_nearest["node_id"]

            # Run A* while avoiding closed road segments.
            result = router.find_route(
                start_node,
                destination_node,
                traffic_level=traffic_level,
                emergency_vehicle=emergency_vehicle,
                blocked_roads=blocked_roads
            )

            start_name = (
                f"Selected location ({start_node})"
            )

            destination_name = (
                f"Selected location ({destination_node})"
            )

        else:
            # Named locations use the same routing algorithm.
            result = router.find_route(
                start_name,
                destination_name,
                traffic_level=traffic_level,
                emergency_vehicle=emergency_vehicle,
                blocked_roads=blocked_roads
            )

        # No available route.
        if result is None:
            return jsonify({
                "error": (
                    "No road route is available between these "
                    "locations with the selected road closures."
                ),
                "blocked_roads_count": len(blocked_roads)
            }), 404

        # Describe the routing mode.
        if emergency_vehicle:
            message = (
                "Emergency routing enabled. The algorithm uses a "
                "reduced simulated congestion penalty. Real traffic "
                "signals are not controlled, and live traffic is "
                "not integrated."
            )
        else:
            message = (
                "Traffic-aware A* route calculated using simulated "
                "congestion. Live traffic is not integrated."
            )

        if blocked_roads:
            message += (
                f" {len(blocked_roads)} road closure(s) applied "
                "to this route calculation."
            )

        # ------------------------------------------
        # Simulated travel-time model
        # ------------------------------------------

        average_speed_kmh = {
            "low": 30.0,
            "medium": 18.0,
            "high": 8.0,
        }[traffic_level]

        base_travel_time = (
            result["distance_km"] / average_speed_kmh
        ) * 60.0

        signal_delay_per_km = {
            "low": 0.3,
            "medium": 0.8,
            "high": 1.5,
        }[traffic_level]

        simulated_signal_delay = (
            result["distance_km"] * signal_delay_per_km
        )

        # Emergency mode changes the simulated delay only.
        if emergency_vehicle:
            simulated_signal_delay *= 0.35

        estimated_travel_time = (
            base_travel_time + simulated_signal_delay
        )

        # ------------------------------------------
        # API response
        # ------------------------------------------

        return jsonify({
            "route": [
                start_name,
                destination_name
            ],

            # A* road-graph route.
            "route_nodes": result["route"],
            "route_coordinates": result["coordinates"],
            "number_of_route_nodes": result["route_nodes"],

            # Physical distance.
            "distance_meters": result["distance_meters"],
            "distance_km": result["distance_km"],

            # Simulated traffic information.
            "traffic": traffic_level,
            "traffic_cost": result["traffic_cost"],
            "estimated_travel_time_minutes": round(
                estimated_travel_time, 2
            ),
            "simulated_signal_delay_minutes": round(
                simulated_signal_delay, 2
            ),
            "estimated_average_speed_kmh": average_speed_kmh,

            # Emergency status.
            "emergency_priority": emergency_vehicle,
            "emergency_vehicle": result["emergency_vehicle"],

            # Road closure status.
            "blocked_roads_count": len(blocked_roads),
            "blocked_roads": [
                list(road) for road in blocked_roads
            ],
            "blocked_roads_avoided": len(blocked_roads),

            # Important limitation notice.
            "message": message
        })

    except (ValueError, KeyError, TypeError) as error:
        return jsonify({
            "error": str(error)
        }), 400


if __name__ == "__main__":
    app.run(debug=True)
