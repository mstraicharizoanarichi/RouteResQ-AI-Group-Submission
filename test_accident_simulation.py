import unittest
from real_road_routing import RealRoadRouter


class AccidentSimulationTests(unittest.TestCase):
    def setUp(self):
        self.router = RealRoadRouter.__new__(RealRoadRouter)
        self.router.nodes = {
            "A": {"lat": 25.7800, "lon": 88.9000},
            "B": {"lat": 25.7800, "lon": 88.9010},
            "C": {"lat": 25.7815, "lon": 88.9000},
            "D": {"lat": 25.7815, "lon": 88.9010},
        }
        self.router.graph = {
            "A": {"B": 120, "C": 250},
            "B": {"A": 120, "D": 180},
            "C": {"A": 250, "D": 120},
            "D": {"B": 180, "C": 120},
        }

    def test_accident_penalty_selects_alternative_route(self):
        result = self.router.find_route(
            "A", "D", traffic_level="low",
            accident_roads=[("A", "B")]
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["route"], ["A", "C", "D"])

    def test_accident_does_not_mutate_road_graph(self):
        original = {node: edges.copy() for node, edges in self.router.graph.items()}
        self.router.find_route(
            "A", "D", traffic_level="low",
            accident_roads=[("A", "B")]
        )
        self.assertEqual(self.router.graph, original)

    def test_astar_and_dijkstra_use_same_accident_costs(self):
        result = self.router.compare_algorithms(
            "A", "D", traffic_level="low",
            accident_roads=[("A", "B")]
        )
        self.assertEqual(result["A*"]["route"], result["Dijkstra"]["route"])
        self.assertEqual(result["A*"]["route"], ["A", "C", "D"])
        self.assertEqual(result["accident_roads_count"], 1)

    def test_invalid_accident_segment_is_rejected(self):
        with self.assertRaises(ValueError):
            self.router.find_route(
                "A", "D", traffic_level="low",
                accident_roads=[("A", "UNKNOWN")]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
