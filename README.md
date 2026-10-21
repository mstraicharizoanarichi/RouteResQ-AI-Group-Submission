# RouteResQ AI

## AI-Based Dynamic Emergency Traffic Management Agent

RouteResQ AI is an academic Artificial Intelligence project that uses the **A* search algorithm** to find routes through a road network derived from OpenStreetMap data.

The application provides an interactive map where users can select starting and destination locations, choose simulated traffic conditions, enable emergency-vehicle mode, and calculate routes. It also supports simulated road closures and route recalculation.

The project demonstrates how AI search algorithms can support route planning under changing road and traffic conditions.

## Features

* Interactive map using Leaflet and OpenStreetMap.
* Road-network-based route calculation.
* A* search algorithm for route finding.
* Three simulated traffic levels: Low, Medium, and High.
* Traffic-adjusted route costs.
* Emergency-vehicle mode with reduced simulated congestion penalties.
* Estimated travel time based on assumed traffic conditions.
* Simulated traffic-signal delay estimation.
* Location search using the Nominatim geocoding service.
* Map-based start and destination selection.
* Simulated road closures.
* Automatic route recalculation around closed road segments when an alternative route exists.
* Simulated accident scenarios with accident-aware route recalculation.
* Accident penalties applied to affected road segments during route calculation.
* A* and Dijkstra algorithm comparison with simulated accident costs.
* Input validation and API error handling.
* Automated tests for application functionality and road-closure routing.

## Technologies Used

* Python
* Flask
* A* Search Algorithm
* HTML
* CSS
* JavaScript
* Leaflet
* OpenStreetMap
* Nominatim Geocoding Service
* Python `unittest`

## Project Structure

```text
AI-Project/
├── app.py
├── real_road_routing.py
├── build_road_graph.py
├── download_roads.py
├── requirements.txt
├── README.md
├── .gitignore
├── test_app.py
├── test_real_route.py
├── test_place_connections.py
├── test_api_road_closure.py
├── test_road_closure.py
├── test_accident_simulation.py
├── data/
│   └── saidpur_road_graph.json
└── templates/
    └── index.html
```

The main application is implemented in `app.py`. Routing logic is implemented in `real_road_routing.py`, and the interactive web interface is located in `templates/index.html`.

The road graph is stored locally in `data/saidpur_road_graph.json`.

Additional experimental Python files may exist in the project directory but are not required by the main Flask application.

## Requirements

* Python 3.10 or a compatible newer version.
* pip.
* A modern web browser.
* An internet connection for online map tiles and location searches.

The application uses a locally stored road graph for route calculation. Online map tiles and location searches require an internet connection.

## Installation on Windows

### 1. Open PowerShell

Navigate to the project directory:

```powershell
cd F:\AI-Project\submission\RouteResQ-AI-Group-Submission
```

### 2. Create a Virtual Environment

If the project virtual environment does not already exist, run:

```powershell
python -m venv .venv
```

### 3. Install Dependencies

Install the required Python packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The virtual environment keeps project dependencies separate from the system Python installation.

## Run the Application

Open PowerShell and execute:

```powershell
cd F:\AI-Project\submission\RouteResQ-AI-Group-Submission
.\.venv\Scripts\python.exe app.py
```

When the Flask server starts, open the following address in your browser:

```text
http://127.0.0.1:5000/
```

Keep the PowerShell window open while using the application.

To stop the server, press `Ctrl + C` in PowerShell.

## How to Use the Application

1. Open the application in your browser.
2. Select a starting location and destination using the available location search or map interface.
3. Choose a traffic level: Low, Medium, or High.
4. Enable emergency-vehicle mode if you want to simulate emergency routing.
5. Request a route.
6. Review the displayed route and estimated travel information.
7. If the interface provides road-closure controls, simulate a road closure and recalculate the route.
8. Reopen the closed roads when you want to restore the original routing conditions.
9. Use the simulated accident controls to add, remove, or clear accident scenarios and recalculate the route.
10. Use the algorithm-comparison feature to compare A* and Dijkstra when that control is available in the interface.

The application recalculates routes using the available road graph and current simulated conditions.

## Run Automated Tests

Run the complete automated test suite from the project directory:

```powershell
cd F:\AI-Project\submission\RouteResQ-AI-Group-Submission
.\.venv\Scripts\python.exe -m unittest discover -v
```

The tests cover application responses, route calculation, traffic settings, emergency mode, input validation, road closures, and alternative-route selection.

The road-closure tests also check that the router can return no route when all available exits from a starting node are closed.

A successful test run ends with a summary similar to:

```text
Ran 20 tests
OK
```

The exact test count may change when additional tests are added.

## Routing Method

The application uses the A* search algorithm to find a route through a locally stored road network.

The routing implementation considers road-segment distances and applies simulated congestion penalties to edge costs. A Haversine-based heuristic estimates straight-line geographic distance between coordinates.

The selected route can change according to the configured traffic conditions, emergency mode, and blocked road segments.

If a road is marked as closed, the routing algorithm avoids that segment. If no valid alternative route is available, the application can report that no route was found.

## Emergency-Vehicle Mode

Emergency-vehicle mode changes the simulated routing costs by reducing the congestion penalty. It also reduces the estimated traffic-signal delay.

These adjustments demonstrate how an AI routing system could prioritize emergency travel under simulated conditions.

**Emergency mode is a simulation.** The application does not control real traffic signals, dispatch emergency vehicles, or communicate with actual emergency services.

## Traffic Simulation and Estimated Travel Time

The application supports three simulated traffic levels:

* **Low:** Represents relatively light traffic.
* **Medium:** Represents moderate traffic.
* **High:** Represents heavy traffic.

Traffic levels influence simulated routing costs and estimated travel time. Signal-delay estimates are also simulated.

The estimates are not obtained from live traffic sensors, validated real-world road speeds, or actual traffic-signal systems.

## Road Closures and Dynamic Rerouting

The application supports simulated road closures within its routing system.

When a road segment is marked as closed, the routing algorithm excludes that segment from route calculation. If another valid path exists, the application can calculate an alternative route.

The road-closure tests verify alternative-route selection and handling of situations where no route is available.

These closures are application-level simulations. They do not represent verified live road incidents or automatically detect real-world road closures.

## Simulated Accident Scenarios

The application supports simulated accidents on selected road segments. An accident adds a routing penalty, allowing the route planner to prefer a suitable alternative when one is available.

Users can add simulated accidents, remove selected accidents, or clear the simulated accident list through the interface.

Accidents are simulated scenarios. The application does not detect real accidents or receive verified live accident reports.

Automated tests cover alternative-route selection, graph immutability, consistent accident costs for A* and Dijkstra, and rejection of invalid accident segments.

## Algorithm Comparison

The routing module supports comparison between A* and Dijkstra under the configured routing conditions, including simulated accident penalties. Both algorithms are evaluated using the same road-network and simulated-cost assumptions.

The comparison is intended for academic demonstration and does not establish that either algorithm is universally faster or better for every real-world route.
## Road Data and Attribution

The locally stored road graph is:

```text
data/saidpur_road_graph.json
```

The graph was derived from OpenStreetMap road-network data for the project area.

OpenStreetMap data is available under the Open Database License (ODbL). Consult the OpenStreetMap copyright and attribution page for applicable attribution and licensing requirements:

https://www.openstreetmap.org/copyright

The interface uses Leaflet and OpenStreetMap map tiles.

## Limitations

* Traffic conditions are simulated rather than obtained from live traffic sensors.
* Estimated travel times depend on assumed traffic conditions.
* Traffic-signal priority is simulated; actual signals are not controlled.
* The application does not dispatch emergency vehicles.
* Road closures must be simulated through the application rather than detected automatically from real-world incidents.
* Route quality depends on the coverage and accuracy of the stored road graph.
* Online geocoding and map tiles require an internet connection.
* The application is intended for academic demonstration, not real-world emergency dispatch.

## Future Improvements

* Integrate a reliable live traffic data source.
* Improve travel-time estimates using validated road-speed data.
* Add verified hospital and emergency-service locations.
* Incorporate verified real-world road-closure information.
* Improve road-network coverage and routing validation.
* Develop a more realistic emergency-signal priority simulation.
* Expand automated API and routing tests.
* Evaluate route quality using additional scenarios.

## Project Status

RouteResQ AI is an academic project under development and testing. The current implementation demonstrates road-network routing, A* search, simulated traffic conditions, emergency-vehicle mode, and simulated road-closure handling.

Its simulation results should not be treated as validated real-world emergency-routing recommendations.

## License

The application code has not yet been assigned a separate open-source license. OpenStreetMap data remains subject to its applicable licensing and attribution requirements.



