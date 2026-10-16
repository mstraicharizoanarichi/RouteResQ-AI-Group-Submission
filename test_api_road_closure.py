
import unittest

from app import app, router


class RoadClosureAPITestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_api_reroutes_around_closed_road(self):
        """Find a road segment whose closure allows an alternative route."""

        normal_result = router.find_route(
            "University",
            "Market",
            traffic_level="low"
        )

        self.assertIsNotNone(normal_result)

        normal_route = normal_result["route"]

        self.assertGreaterEqual(len(normal_route), 2)

        successful_reroute = False

        # Test different road segments.
        # Some closures may disconnect the route entirely.
        for index in range(len(normal_route) - 1):

            first_node = normal_route[index]
            second_node = normal_route[index + 1]

            response = self.client.post(
                "/find-route",
                json={
                    "start": "University",
                    "destination": "Market",
                    "traffic": "low",
                    "emergency": False,
                    "blocked_roads": [
                        [first_node, second_node]
                    ]
                }
            )

            # No route is possible with this closure.
            # Try another road segment.
            if response.status_code == 404:
                continue

            self.assertEqual(
                response.status_code,
                200,
                msg=response.get_data(as_text=True)
            )

            data = response.get_json()
            alternative_route = data["route_nodes"]

            alternative_edges = {
                frozenset((
                    alternative_route[i],
                    alternative_route[i + 1]
                ))
                for i in range(len(alternative_route) - 1)
            }

            # The selected route must avoid the closed segment.
            self.assertNotIn(
                frozenset((first_node, second_node)),
                alternative_edges
            )

            self.assertEqual(data["blocked_roads_count"], 1)

            successful_reroute = True

            print("\nPASS: Flask API successfully rerouted.")
            print("Closed road:", first_node, "->", second_node)
            print("Original route nodes:", len(normal_route))
            print("Alternative route nodes:", len(alternative_route))
            print("Alternative distance:", data["distance_km"], "km")

            break

        self.assertTrue(
            successful_reroute,
            "No tested road closure produced an alternative route."
        )

    def test_api_rejects_unknown_road_nodes(self):
        """Unknown road-node IDs must be rejected."""

        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "low",
                "emergency": False,
                "blocked_roads": [
                    ["UNKNOWN_NODE_A", "UNKNOWN_NODE_B"]
                ]
            }
        )

        self.assertEqual(response.status_code, 400)

        print("\nPASS: Unknown road nodes correctly rejected.")

    def test_api_rejects_invalid_blocked_roads(self):
        """Malformed road closures must be rejected."""

        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "low",
                "emergency": False,
                "blocked_roads": [
                    ["only_one_node"]
                ]
            }
        )

        self.assertEqual(response.status_code, 400)

        print("\nPASS: Invalid road closure correctly rejected.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
