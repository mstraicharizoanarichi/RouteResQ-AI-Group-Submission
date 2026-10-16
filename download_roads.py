import json
import urllib.parse
import urllib.request
from pathlib import Path

south = 25.79
west = 88.89
north = 25.80
east = 88.91

query = f"""
[out:json][timeout:25];
way["highway"]({south},{west},{north},{east});
out geom;
"""

servers = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

output_dir = Path(__file__).parent / "data"
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "saidpur_roads.json"

for server in servers:
    try:
        print(f"\nTrying server: {server}")

        data = urllib.parse.urlencode(
            {"data": query}
        ).encode("utf-8")

        request = urllib.request.Request(
            server,
            data=data,
            headers={
                "User-Agent": "RouteResQ-AI-Academic-Project/1.0"
            },
        )

        with urllib.request.urlopen(request, timeout=45) as response:
            road_data = json.loads(
                response.read().decode("utf-8")
            )

        ways = [
            item for item in road_data.get("elements", [])
            if item.get("type") == "way"
        ]

        with output_file.open("w", encoding="utf-8") as file:
            json.dump(road_data, file)

        print("\nDownload successful!")
        print("Road segments:", len(ways))
        print("Saved file:", output_file)
        print("File size:", output_file.stat().st_size, "bytes")
        break

    except Exception as error:
        print("This server failed:", error)

else:
    print("\nBoth servers failed. No need to keep retrying now.")