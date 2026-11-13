# 🚁 SkyRoute 3D — Autonomous Drone Delivery Simulator

An interactive 3D web application simulating an autonomous urban drone delivery service. The simulator features dynamic 3D obstacle avoidance using **3D A\*** pathfinding with line-of-sight shortcutting, smooth **Catmull-Rom spline trajectory generation**, physical quadcopter banking and rotor mechanics, interactive building and restricted airspace construction, and real-time flight telemetry.

---

## 🌟 Key Features

1. **Interactive Element Placement & Real-Time Dragging**:
   - 📦 **Place & Drag Package**: Click to position or click-and-drag the package cargo across the map.
   - 🎯 **Place & Drag Drop-off**: Click to position or drag the landing target pad with pulsing concentric rings and beacon.
   - 🏢 **Add Buildings (Obstacles)**: Click to place buildings directly in between the drone and its delivery destination.
   - ✋ **Select / Edit / Drag / Delete**: Click any building to view its dimensions, dynamically slide its height ($10\text{m} - 110\text{m}$), drag it across the grid to watch the flight path re-route in real-time, or press `Delete` to remove it.

2. **3D Quadcopter Mechanics & Delivery Lifecycle**:
   - **Phase 1: Dispatch**: The autonomous quadcopter deploys and swoops down directly over the package starting point.
   - **Phase 2: Precision Winch Pickup**: The drone hovers stably, extends a motorized winch cable down to the package, latches with a magnetic clamp (with authentic audio and visual latch effect), and reels the cargo up to transport position.
   - **Phase 3: Autonomous 3D Trajectory Navigation**: The quadcopter accelerates and follows the optimal collision-free 3D flight corridor, smoothly banking into turns, tilting with velocity, crabbing into crosswinds, and modulating rotor RPM and searchlights.
   - **Phase 4: Target Hover & Delivery**: Upon reaching the destination coordinate, the drone enters a stable hover, lowers the winch cable gently to deposit the parcel onto the center of the landing pad, and releases the magnetic clamp.
   - **Phase 5: Mission Success**: The landing pad pulses with celebration effects, plays a delivery fanfare, and presents a comprehensive post-flight mission analytics report.

3. **Optimal 3D Pathfinding Engine**:
   - **3D A\* Algorithm**: Searches across continuous $XZ$ coordinates and discretized altitude tiers with horizontal and vertical clearance buffers so the drone never grazes walls.
   - **Dynamic Climb vs. Detour Optimization**: Balances the energy cost of climbing over low buildings against horizontal detours around skyscrapers.
   - **Flight Profiles**:
     - *Smart 3D Optimal*: Balances distance and climb energy.
     - *Street Canyon (Low)*: Penalizes altitude changes, weaving between buildings at street level.
     - *Skyway Flyover (High)*: Climbs safely above all obstacles for straight-line express transit.
     - *Euclidean Shortest*: Geometric 3D shortest path.
   - **String-Pulling (Line-of-Sight Raycasting)**: Prunes grid zig-zags to generate straight flight corridors.
   - **Catmull-Rom 3D Splines**: Produces silky smooth curved flight trajectories.
   - **Live Altitude Profile Chart**: Dynamic 2D elevation cross-section graph in the HUD showing the flight corridor and live drone position!

4. **Environment, Lighting & Wind Vector Simulation**:
   - ☀️ **Daylight**, 🌅 **Golden Hour / Sunset**, and 🌙 **Cyberpunk Night** with illuminated building windows and dynamic searchlights!
   - 💨 **Live Wind Simulation**: Adjustable wind speed ($0-45\text{ km/h}$) causing physical crosswind crab-tilting and headwind/tailwind power effects.
   - 🛡️ **Safety Buffer Zones Overlay**: Visualizes the clearance standoff margins around structures.
   - 🌀 **3D Flight Tunnel**: Renders a glowing translucent aerial tube along the computed trajectory.

5. **Multi-Camera Director**:
   - 🌐 **Free Orbit**: Rotate, zoom, and pan freely around the city.
   - 🚁 **Chase Cam**: Smooth 3rd-person follow camera tracking behind the drone.
   - 👁️ **Drone POV**: Forward nose-mounted cockpit camera.
   - 🗺️ **Top-Down**: Orthographic 2D tactical map view.
   - 📐 **Isometric**: Classic $45^\circ$ strategic view.

6. **Audio Synthesizer (Web Audio API)**:
   - Real-time procedural brushless motor hum modulated by throttle and climb rate.
   - Winch spooling whir.
   - Magnetic latch click.
   - Delivery fanfare and waypoint pings.
   - One-click mute/unmute toggle.

7. **Pre-made Urban Scenarios & City Generator**:
   - 🏙️ **Urban Canyons**: Dense grid of high-rises with narrow avenues.
   - 🏢 **Skyscraper Wall**: A towering wall between start and target testing climb vs. detour tradeoffs.
   - 🌀 **Maze Challenge**: An intricate S-bend labyrinth.
   - 🏡 **Suburban Homes**: Low residential houses.
   - ⛔ **Restricted Airspace**: Glowing red cylindrical No-Fly Zones.
   - 🎲 **Randomize**: Instant 1-click procedural city generator.

---

## 🚀 How to Run the Website

### Method 1: Instant Local Python Server (Recommended)
From the project folder, run:
```bash
python server.py
```
This starts the local web server and opens `http://localhost:8080/index.html` in your default web browser automatically.

### Method 2: Direct Browser Launch
You can also directly open `index.html` in any modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari).

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Space` | Launch Delivery / Pause / Resume |
| `R` | Reset Flight Simulation |
| `Delete` / `Backspace` | Delete selected building |
| Left Click + Drag | Rotate 3D Camera (Orbit mode) |
| Right Click + Drag | Pan 3D Camera |
| Scroll Wheel | Zoom In / Out |

---

## 📁 Project Architecture

```
drone-delivery-simulator/
├── index.html            # Main HTML layout, HUD overlay, and controls
├── css/
│   └── style.css         # Glassmorphism dark cyberpunk UI theme
├── js/
│   ├── audio.js          # Web Audio API procedural synthesizer
│   ├── pathfinder.js     # 3D A*, raycast shortcutting, Catmull-Rom spline
│   ├── city.js           # 3D buildings, textures, beacons, scenarios
│   ├── drone.js          # Quadcopter model, physics, winch, package, target
│   ├── simulation.js     # State machine (Spawning -> Pickup -> En Route -> Delivery)
│   ├── ui.js             # Event listeners, telemetry updates, modals
│   └── main.js           # Three.js scene, lighting, camera director, raycasting
└── server.py             # One-click local web server launcher
```

