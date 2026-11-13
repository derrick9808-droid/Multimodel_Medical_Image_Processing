/**
 * Simulation Controller - State Machine for Autonomous Drone Delivery
 * Manages states: IDLE -> SPAWNING -> PICKUP -> ASCENT -> EN_ROUTE -> DESCENT -> DELIVERED
 */

class SimulationController {
  constructor(scene, drone, packageObj, targetObj, cityManager, pathfinder) {
    this.scene = scene;
    this.drone = drone;
    this.packageObj = packageObj;
    this.targetObj = targetObj;
    this.city = cityManager;
    this.pathfinder = pathfinder;

    // State machine
    this.state = 'IDLE'; // 'IDLE', 'SPAWNING', 'PICKUP', 'ASCENT', 'EN_ROUTE', 'DESCENT', 'DELIVERED', 'PAUSED'
    this.previousState = 'IDLE';

    // Current flight plan
    this.currentPlan = null;
    this.pathSpline = null;
    this.pathLineMesh = null;
    this.waypointMarkers = [];

    // Flight progress parameters
    this.splineProgress = 0; // 0 to 1
    this.flightSpeed = 16.0; // Base speed in meters / second
    this.simSpeedMultiplier = 1.0;
    this.totalDistance = 0;
    this.distanceTraveled = 0;
    this.elapsedFlightTime = 0;

    // Environmental Wind
    this.windSpeedKmh = 15;
    this.windDirectionDeg = 45;

    // Visual corridor tunnel
    this.showFlightTunnel = true;
    this.pathTunnelMesh = null;

    // Battery system
    this.batteryMaxWh = 180;
    this.batteryCurrentWh = 180;
    this.batteryPercentage = 100;

    // Animation sub-timers
    this.stateTimer = 0;
    this.pickupDuration = 2.5; // Seconds to lower winch and grab
    this.dropDuration = 2.2;   // Seconds to lower winch and place

    // Elevation chart canvas
    this.elevationCanvas = document.getElementById('elevation-canvas');
    this.elevationCtx = this.elevationCanvas ? this.elevationCanvas.getContext('2d') : null;

    // Telemetry callbacks
    this.onTelemetryUpdate = null;
    this.onMissionLog = null;
    this.onStateChange = null;
    this.onMissionComplete = null;

    // Initial path generation
    this.recalculateFlightPath();
  }

  setWind(speedKmh, directionDeg) {
    this.windSpeedKmh = speedKmh;
    if (directionDeg !== undefined) this.windDirectionDeg = directionDeg;
  }

  toggleFlightTunnel(visible) {
    this.showFlightTunnel = visible;
    if (this.pathTunnelMesh) {
      this.pathTunnelMesh.visible = visible;
    } else if (visible) {
      this.renderFlightPathVisuals();
    }
  }

  setSpeedMultiplier(multiplier) {
    this.simSpeedMultiplier = multiplier;
  }

  // Recalculates 3D path based on current package, target, and buildings
  recalculateFlightPath() {
    const startPos = this.packageObj.getPosition();
    const targetPos = this.targetObj.getPosition();

    this.currentPlan = this.pathfinder.findPath(startPos, targetPos, this.city.buildings);
    this.pathSpline = this.currentPlan.spline;
    this.totalDistance = parseFloat(this.currentPlan.metrics.distance);

    this.renderFlightPathVisuals();
    this.drawElevationProfile(0);

    if (this.onTelemetryUpdate) {
      this.onTelemetryUpdate({
        distance: this.totalDistance,
        eta: this.currentPlan.metrics.etaSeconds,
        energy: this.currentPlan.metrics.energyWh,
        calcMs: this.currentPlan.metrics.calculationMs
      });
    }
  }

  renderFlightPathVisuals() {
    // 1. Remove old visualizer line, tunnel & waypoints
    if (this.pathLineMesh) {
      this.scene.remove(this.pathLineMesh);
      this.pathLineMesh.geometry.dispose();
      this.pathLineMesh.material.dispose();
      this.pathLineMesh = null;
    }
    if (this.pathTunnelMesh) {
      this.scene.remove(this.pathTunnelMesh);
      this.pathTunnelMesh.geometry.dispose();
      this.pathTunnelMesh.material.dispose();
      this.pathTunnelMesh = null;
    }
    for (const marker of this.waypointMarkers) {
      this.scene.remove(marker);
      marker.geometry.dispose();
      marker.material.dispose();
    }
    this.waypointMarkers = [];

    if (!this.pathSpline) return;

    // 2. Draw smooth glowing flight corridor curve including vertical climb & descent
    const startPos = this.packageObj.getPosition();
    const targetPos = this.targetObj.getPosition();
    const takeoffPt = this.currentPlan.cruiseWaypoints[0];
    const descentPt = this.currentPlan.cruiseWaypoints[this.currentPlan.cruiseWaypoints.length - 1];

    const splinePoints = this.pathSpline.getPoints(120);
    const fullFlightPoints = [
      new THREE.Vector3(startPos.x, startPos.y + 0.4, startPos.z),
      takeoffPt,
      ...splinePoints,
      descentPt,
      new THREE.Vector3(targetPos.x, targetPos.y + 0.4, targetPos.z)
    ];

    const lineGeo = new THREE.BufferGeometry().setFromPoints(fullFlightPoints);
    const lineMat = new THREE.LineDashedMaterial({
      color: 0x06b6d4,
      dashSize: 2.0,
      gapSize: 0.8,
      linewidth: 3,
      transparent: true,
      opacity: 0.85
    });
    this.pathLineMesh = new THREE.Line(lineGeo, lineMat);
    this.pathLineMesh.computeLineDistances();
    this.scene.add(this.pathLineMesh);

    // 2b. 3D Flight Corridor Tunnel Mesh
    if (this.showFlightTunnel) {
      try {
        const tunnelGeo = new THREE.TubeGeometry(this.pathSpline, 64, 1.4, 8, false);
        const tunnelMat = new THREE.MeshBasicMaterial({
          color: 0x06b6d4,
          transparent: true,
          opacity: 0.12,
          wireframe: true
        });
        this.pathTunnelMesh = new THREE.Mesh(tunnelGeo, tunnelMat);
        this.scene.add(this.pathTunnelMesh);
      } catch (e) {}
    }

    // 3. Waypoint beacon nodes
    const wpMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true });
    const wpGeo = new THREE.OctahedronGeometry(0.8, 0);

    for (let i = 0; i < this.currentPlan.cruiseWaypoints.length; i++) {
      const pt = this.currentPlan.cruiseWaypoints[i];
      const marker = new THREE.Mesh(wpGeo, wpMat);
      marker.position.copy(pt);
      this.scene.add(marker);
      this.waypointMarkers.push(marker);
    }
  }

  drawElevationProfile(droneProgress = 0) {
    if (!this.elevationCtx || !this.pathSpline) return;
    const ctx = this.elevationCtx;
    const w = this.elevationCanvas.width;
    const h = this.elevationCanvas.height;

    ctx.clearRect(0, 0, w, h);

    // Background horizontal grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h * 0.33); ctx.lineTo(w, h * 0.33);
    ctx.moveTo(0, h * 0.66); ctx.lineTo(w, h * 0.66);
    ctx.stroke();

    // Sample altitude points from spline
    const samples = 50;
    const points = [];
    let maxY = 30;
    for (let i = 0; i <= samples; i++) {
      const pt = this.pathSpline.getPoint(i / samples);
      points.push(pt.y);
      if (pt.y > maxY) maxY = pt.y;
    }
    maxY = Math.max(35, maxY * 1.15);

    // Draw altitude curve
    ctx.beginPath();
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 2;
    for (let i = 0; i <= samples; i++) {
      const px = (i / samples) * (w - 24) + 12;
      const py = h - (points[i] / maxY) * (h - 16) - 6;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Fill gradient below curve
    ctx.lineTo(w - 12, h - 4);
    ctx.lineTo(12, h - 4);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(6, 182, 212, 0.3)');
    grad.addColorStop(1, 'rgba(6, 182, 212, 0.01)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw Drone Position Indicator
    const droneNorm = Math.min(1.0, Math.max(0, droneProgress));
    const droneX = droneNorm * (w - 24) + 12;
    const droneYVal = this.pathSpline.getPoint(Math.min(0.999, droneNorm)).y;
    const droneY = h - (droneYVal / maxY) * (h - 16) - 6;

    ctx.beginPath();
    ctx.arc(droneX, droneY, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Text labels
    ctx.fillStyle = '#9ca3af';
    ctx.font = '9px monospace';
    ctx.fillText(`${maxY.toFixed(0)}m`, 2, 10);
    ctx.fillText('0m', 2, h - 3);
  }

  startMission() {
    if (this.state === 'IDLE' || this.state === 'DELIVERED') {
      window.soundEngine.init();
      this.setState('SPAWNING');
      this.stateTimer = 0;
      this.splineProgress = 0;
      this.distanceTraveled = 0;
      this.elapsedFlightTime = 0;
      this.batteryCurrentWh = this.batteryMaxWh;
      this.batteryPercentage = 100;

      // Position drone at spawn location above package
      const startPos = this.packageObj.getPosition();
      this.packageObj.setPosition(startPos.x, 0.4, startPos.z);
      this.drone.setWinchExtension(0);
      this.drone.group.position.set(startPos.x, 18, startPos.z);
      this.drone.group.rotation.set(0, 0, 0);
      this.drone.group.visible = true;

      window.soundEngine.startMotor();
      this.logMission(`Autopilot initiated. Dispatching quadcopter to package depot at (${startPos.x.toFixed(0)}, ${startPos.z.toFixed(0)})...`);
    } else if (this.state === 'PAUSED') {
      this.setState(this.previousState);
      this.logMission("Mission resumed.");
    }
  }

  pauseMission() {
    if (this.state !== 'IDLE' && this.state !== 'DELIVERED' && this.state !== 'PAUSED') {
      this.previousState = this.state;
      this.setState('PAUSED');
      this.logMission("Simulation paused.");
    }
  }

  resetMission() {
    this.setState('IDLE');
    this.stateTimer = 0;
    this.splineProgress = 0;
    this.distanceTraveled = 0;
    this.elapsedFlightTime = 0;

    // Reset drone
    this.drone.group.visible = false;
    this.drone.setWinchExtension(0);
    if (this.drone.isCarryingPackage) {
      this.drone.releasePackage(this.packageObj.getPosition());
    }

    // Reset package back to start
    const startPos = this.packageObj.getPosition();
    this.packageObj.setPosition(startPos.x, 0.4, startPos.z);
    this.packageObj.group.visible = true;

    window.soundEngine.stopMotor();
    this.logMission("Simulation reset. System standing by.");

    this.recalculateFlightPath();
  }

  setState(newState) {
    this.state = newState;
    if (this.onStateChange) {
      this.onStateChange(newState);
    }
  }

  logMission(text) {
    if (this.onMissionLog) {
      const timeStr = this.formatTime(this.elapsedFlightTime);
      this.onMissionLog(timeStr, text);
    }
  }

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Main simulation update loop
  update(delta) {
    if (this.state === 'IDLE' || this.state === 'PAUSED') {
      return;
    }

    const simDelta = delta * this.simSpeedMultiplier;
    this.elapsedFlightTime += simDelta;
    this.stateTimer += simDelta;

    const startPos = this.packageObj.getPosition();
    const targetPos = this.targetObj.getPosition();

    switch (this.state) {
      case 'SPAWNING': {
        // Drone descends smoothly from sky to hover directly above the package
        const hoverAltitude = 6.0;
        const targetHoverY = startPos.y + hoverAltitude;
        
        this.drone.group.position.x = startPos.x;
        this.drone.group.position.z = startPos.z;
        this.drone.group.position.y = THREE.MathUtils.lerp(this.drone.group.position.y, targetHoverY, simDelta * 3.0);

        window.soundEngine.updateMotorThrottle(0.3, 0);

        if (Math.abs(this.drone.group.position.y - targetHoverY) < 0.2 || this.stateTimer > 2.0) {
          this.setState('PICKUP');
          this.stateTimer = 0;
          this.logMission("Aligned above cargo. Extending magnetic winch clamp...");
          window.soundEngine.playWinch();
        }
        break;
      }

      case 'PICKUP': {
        // Lower winch cable to ground level to latch onto package
        const droneY = this.drone.group.position.y;
        const targetWinchLen = Math.max(0.2, droneY - 0.4);
        const progress = Math.min(1.0, this.stateTimer / (this.pickupDuration * 0.5));
        
        this.drone.setWinchExtension(progress * targetWinchLen);

        if (this.stateTimer >= this.pickupDuration * 0.5 && !this.drone.isCarryingPackage) {
          // Latch onto package!
          this.drone.attachPackage(this.packageObj.group);
          window.soundEngine.playLatch();
          this.logMission("Package magnetically secured! Commencing optimal climb...");
        }

        if (this.stateTimer >= this.pickupDuration) {
          // Retract winch to transport position
          this.drone.setWinchExtension(0);
          this.setState('ASCENT');
          this.stateTimer = 0;
        }
        break;
      }

      case 'ASCENT': {
        // Climb to initial flight trajectory altitude
        const takeoffWP = this.currentPlan.cruiseWaypoints[0];
        this.drone.group.position.y = THREE.MathUtils.lerp(this.drone.group.position.y, takeoffWP.y, simDelta * 2.5);
        this.drone.group.position.x = THREE.MathUtils.lerp(this.drone.group.position.x, takeoffWP.x, simDelta * 2.5);
        this.drone.group.position.z = THREE.MathUtils.lerp(this.drone.group.position.z, takeoffWP.z, simDelta * 2.5);

        window.soundEngine.updateMotorThrottle(0.7, 1.0);

        if (this.drone.group.position.distanceTo(takeoffWP) < 0.8 || this.stateTimer > 2.2) {
          this.drone.group.position.copy(takeoffWP);
          this.setState('EN_ROUTE');
          this.stateTimer = 0;
          this.splineProgress = 0;
          this.logMission(`Optimal 3D corridor acquired. Cruising along spline to destination...`);
        }
        break;
      }

      case 'EN_ROUTE': {
        // Wind drift calculation
        const windRad = (this.windDirectionDeg * Math.PI) / 180;
        const windVec = new THREE.Vector2(Math.sin(windRad), Math.cos(windRad)).multiplyScalar(this.windSpeedKmh / 3.6);

        const tangent = this.pathSpline.getTangent(this.splineProgress);
        const flightHeading = new THREE.Vector2(tangent.x, tangent.z).normalize();

        // Wind alignment: headwind vs tailwind
        const dotWind = windVec.dot(flightHeading);
        const effectiveSpeed = Math.max(8.0, this.flightSpeed + dotWind * 0.35);

        // Crosswind component for physical crab angle
        const crossWind = (windVec.x * flightHeading.y - windVec.y * flightHeading.x);

        const stepDist = effectiveSpeed * simDelta;
        this.distanceTraveled += stepDist;
        this.splineProgress = Math.min(0.999, this.distanceTraveled / this.totalDistance);

        // Sample current 3D position
        const currentPos = this.pathSpline.getPoint(this.splineProgress);

        // Previous position for velocity and climb calculations
        const prevPos = this.drone.group.position.clone();
        this.drone.group.position.copy(currentPos);

        const climbRate = (currentPos.y - prevPos.y) / simDelta;
        const currentSpeedKmh = (effectiveSpeed * 3.6).toFixed(1);

        // Dynamic banking kinematics + counter-wind crab tilt
        const lateralCurvature = tangent.x * 2.0;
        this.drone.setFlightKinematics(tangent, effectiveSpeed, lateralCurvature, climbRate);
        this.drone.bankAngle += crossWind * 0.012;

        // Update live altitude chart indicator
        this.drawElevationProfile(this.splineProgress);

        // Audio modulation
        window.soundEngine.updateMotorThrottle(0.65, climbRate);

        // Battery energy consumption calculation
        const climbPower = Math.max(0, climbRate) * 0.08;
        this.batteryCurrentWh -= (0.015 + climbPower) * simDelta;
        this.batteryPercentage = Math.max(0, (this.batteryCurrentWh / this.batteryMaxWh) * 100);

        // Live telemetry dispatch
        if (this.onTelemetryUpdate) {
          this.onTelemetryUpdate({
            speed: currentSpeedKmh,
            speedMs: this.flightSpeed.toFixed(1),
            altitude: currentPos.y.toFixed(1),
            remainingDist: Math.max(0, this.totalDistance - this.distanceTraveled).toFixed(1),
            battery: this.batteryPercentage.toFixed(0),
            elapsedTime: this.formatTime(this.elapsedFlightTime)
          });
        }

        // Check if approaching destination
        if (this.splineProgress >= 0.98) {
          this.setState('DESCENT');
          this.stateTimer = 0;
          this.logMission("Target destination reached. Initializing precision delivery descent...");
          window.soundEngine.playWinch();
        }
        break;
      }

      case 'DESCENT': {
        // Hover and precision lower package onto landing pad
        this.drone.group.position.x = THREE.MathUtils.lerp(this.drone.group.position.x, targetPos.x, simDelta * 4.0);
        this.drone.group.position.z = THREE.MathUtils.lerp(this.drone.group.position.z, targetPos.z, simDelta * 4.0);
        this.drone.pitchAngle = THREE.MathUtils.lerp(this.drone.pitchAngle, 0, 0.15);
        this.drone.bankAngle = THREE.MathUtils.lerp(this.drone.bankAngle, 0, 0.15);

        const hoverY = this.drone.group.position.y;
        const dropDist = hoverY - 0.4;
        const progress = Math.min(1.0, this.stateTimer / this.dropDuration);

        this.drone.setWinchExtension(progress * dropDist);
        window.soundEngine.updateMotorThrottle(0.35, -0.4);

        if (this.stateTimer >= this.dropDuration) {
          // Release package on landing pad!
          this.drone.setWinchExtension(0);
          this.drone.releasePackage(new THREE.Vector3(targetPos.x, 0.4, targetPos.z));
          this.targetObj.celebrateSuccess();
          window.soundEngine.playLatch();
          window.soundEngine.playDeliverySuccess();

          this.setState('DELIVERED');
          this.logMission("PACKAGE SAFELY DELIVERED! Mission accomplished with 100% precision.");

          if (this.onMissionComplete) {
            this.onMissionComplete({
              flightTime: this.formatTime(this.elapsedFlightTime),
              totalDistance: this.totalDistance.toFixed(1),
              avgSpeedKmh: (this.flightSpeed * 3.6).toFixed(1),
              energyUsedWh: (this.batteryMaxWh - this.batteryCurrentWh).toFixed(1),
              batteryRemaining: this.batteryPercentage.toFixed(0)
            });
          }
        }
        break;
      }

      case 'DELIVERED': {
        // Drone enters smooth victory hover slightly above target
        this.drone.group.position.y = THREE.MathUtils.lerp(this.drone.group.position.y, 14, simDelta * 1.5);
        this.drone.pitchAngle = 0;
        this.drone.bankAngle = 0;
        window.soundEngine.updateMotorThrottle(0.2, 0);
        break;
      }
    }
  }
}

window.SimulationController = SimulationController;
