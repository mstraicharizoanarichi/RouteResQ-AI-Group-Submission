
import unittest

from real_road_routing import RealRoadRouter


class RoadClosureTestCase(unittest.TestCase):

    def setUp(self):
        # Create a small road network for testing.
        # No need to load the complete Saidpur road graph.
        self.router = RealRoadRouter.__new__(RealRoadRouter)

        self.router.nodes = {
            "A": {"lat": 25.7800, "lon": 88.9000},
            "B": {"lat": 25.7800, "lon": 88.9010},
            "C": {"lat": 25.7815, "lon": 88.9000},
            "D": {"lat": 25.7815, "lon": 88.9010},
        }

        # Two possible routes:
        #
        # A -> B -> D  (normal shortest route)
        # A -> C -> D  (alternative route)
        #
        # The road distances are in meters.
        self.router.graph = {
            "A": {"B": 120, "C": 250},
            "B": {"A": 120, "D": 180},
            "C": {"A": 250, "D": 120},
            "D": {"B": 180, "C": 120},
        }

    def test_normal_route(self):
        """The router should find the normal shortest route."""

        result = self.router.find_route(
            "A",
            "D",
            traffic_level="low"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["route"], ["A", "B", "D"])

        print("\nPASS: Normal route selected:", result["route"])

    def test_closed_road_uses_alternative(self):
        """The router should avoid a closed road."""

        result = self.router.find_route(
            "A",
            "D",
            traffic_level="low",
            blocked_roads=[("A", "B")]
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["route"], ["A", "C", "D"])

        # Confirm the closed road was not used.
        route_edges = {
            frozenset((result["route"][i], result["route"][i + 1]))
            for i in range(len(result["route"]) - 1)
        }

        self.assertNotIn(
            frozenset(("A", "B")),
            route_edges
        )

        print("\nPASS: Alternative route selected:", result["route"])

    def test_no_route_when_all_start_roads_closed(self):
        """The router should return None when no route is available."""

        result = self.router.find_route(
            "A",
            "D",
            traffic_level="low",
            blocked_roads=[
                ("A", "B"),
                ("A", "C"),
            ]
        )

        self.assertIsNone(result)

        print("\nPASS: No route returned when all exits are closed.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
