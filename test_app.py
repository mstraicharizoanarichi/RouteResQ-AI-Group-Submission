import unittest

from app import app


class RouteResQAPITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_valid_route(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "low",
                "emergency": False
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertGreater(data["distance_km"], 0)
        self.assertGreater(data["number_of_route_nodes"], 1)
        self.assertGreaterEqual(len(data["route_coordinates"]), 2)
        self.assertEqual(data["traffic"], "low")
        self.assertFalse(data["emergency_vehicle"])

    def test_all_traffic_levels(self):
        for traffic in ("low", "medium", "high"):
            with self.subTest(traffic=traffic):
                response = self.client.post(
                    "/find-route",
                    json={
                        "start": "University",
                        "destination": "Market",
                        "traffic": traffic,
                        "emergency": False
                    }
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.get_json()["traffic"],
                    traffic
                )

    def test_emergency_mode(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "high",
                "emergency": True
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["emergency_vehicle"])
        self.assertTrue(data["emergency_priority"])

    def test_invalid_traffic(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "extreme",
                "emergency": False
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_emergency_value(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "low",
                "emergency": "yes"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_unknown_place(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "UnknownPlace123",
                "destination": "Market",
                "traffic": "low",
                "emergency": False
            }
        )

        self.assertIn(response.status_code, (400, 404))

    def test_invalid_json_fields(self):
        response = self.client.post(
            "/find-route",
            json={
                "start": "University",
                "destination": "Market",
                "traffic": "low",
                "emergency": False,
                "start_coordinates": [25.78]
            }
        )

        self.assertIn(response.status_code, (400, 404))


    def test_valid_map_coordinates(self):
        response = self.client.post(
            "/find-route",
            json={
                "start_coordinates": [25.786213, 88.901606],
                "destination_coordinates": [25.789833, 88.897290],
                "traffic": "low",
                "emergency": False
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertGreater(data["distance_km"], 0)
        self.assertGreaterEqual(len(data["route_coordinates"]), 2)

    def test_far_away_coordinates_rejected(self):
        response = self.client.post(
            "/find-route",
            json={
                "start_coordinates": [0.0, 0.0],
                "destination_coordinates": [25.789833, 88.897290],
                "traffic": "low",
                "emergency": False
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "too far",
            response.get_json()["error"].lower()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
