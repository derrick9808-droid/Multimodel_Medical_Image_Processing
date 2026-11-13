/**
 * UI Controller - Manages Toolbars, Mode Selection, Telemetry Gauges, Modals & User Interaction
 */

class UIController {
  constructor(simController, cityManager, cameraManager) {
    this.sim = simController;
    this.city = cityManager;
    this.cam = cameraManager;

    // Current active tool: 'none', 'place-package', 'place-target', 'add-building', 'select'
    this.activeTool = 'add-building';

    this.cacheElements();
    this.bindEvents();
    this.updateToolUI();
  }

  cacheElements() {
    // Tool buttons
    this.toolBtns = document.querySelectorAll('.tool-btn');
    this.buildingPalette = document.getElementById('building-palette');
    this.buildingTypePills = document.querySelectorAll('.building-type-pill');
    this.buildingHeightInput = document.getElementById('building-height-input');
    this.buildingHeightVal = document.getElementById('building-height-val');

    // Action buttons
    this.randomCityBtn = document.getElementById('btn-random-city');
    this.clearBuildingsBtn = document.getElementById('btn-clear-buildings');
    this.scenarioSelect = document.getElementById('scenario-select');
    this.pathModeSelect = document.getElementById('path-mode-select');

    // Environment & Wind controls
    this.timeOfDaySelect = document.getElementById('time-of-day-select');
    this.windSpeedSlider = document.getElementById('wind-speed-slider');
    this.windSpeedVal = document.getElementById('wind-speed-val');
    this.toggleSafetyBuffers = document.getElementById('toggle-safety-buffers');
    this.toggleFlightTunnel = document.getElementById('toggle-flight-tunnel');

    // Launch & Dock controls
    this.launchBtn = document.getElementById('btn-launch');
    this.resetBtn = document.getElementById('btn-reset');
    this.speedBtns = document.querySelectorAll('.speed-btn');
    this.muteBtn = document.getElementById('btn-mute');

    // Camera buttons
    this.camBtns = document.querySelectorAll('.cam-btn');

    // Telemetry displays
    this.statusBadge = document.getElementById('sim-status-badge');
    this.telemetrySpeed = document.getElementById('telemetry-speed');
    this.telemetryAltitude = document.getElementById('telemetry-altitude');
    this.telemetryDistance = document.getElementById('telemetry-distance');
    this.telemetryEta = document.getElementById('telemetry-eta');
    this.telemetryBatteryVal = document.getElementById('telemetry-battery-val');
    this.telemetryBatteryBar = document.getElementById('telemetry-battery-bar');
    this.missionLogContainer = document.getElementById('mission-log');

    // Modals & Tooltips
    this.helperTooltip = document.getElementById('helper-tooltip');
    this.tooltipText = document.getElementById('tooltip-text');
    this.completionModal = document.getElementById('completion-modal');
    this.modalCloseBtn = document.getElementById('modal-close-btn');

    // Mission summary elements in modal
    this.summaryTime = document.getElementById('summary-time');
    this.summaryDist = document.getElementById('summary-dist');
    this.summarySpeed = document.getElementById('summary-speed');
    this.summaryEnergy = document.getElementById('summary-energy');
  }

  bindEvents() {
    // 1. Tool switching
    this.toolBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        this.setActiveTool(tool);
      });
    });

    // 2. Building Type Selection
    this.buildingTypePills.forEach(pill => {
      pill.addEventListener('click', () => {
        this.buildingTypePills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        const type = pill.dataset.type;
        const height = parseInt(this.buildingHeightInput.value, 10);
        this.city.setPlacementType(type, height);
      });
    });

    // 3. Building Height Slider
    this.buildingHeightInput.addEventListener('input', (e) => {
      const h = parseInt(e.target.value, 10);
      this.buildingHeightVal.textContent = h + 'm';
      this.city.currentBuildingHeight = h;
      if (this.city.ghostMesh) {
        this.city.setPlacementType(this.city.currentBuildingType, h);
      }
      if (this.city.selectedBuilding) {
        // Dynamically adjust selected building height!
        this.city.selectedBuilding.height = h;
        this.city.selectedBuilding.group.scale.y = h / (this.city.selectedBuilding.group.scale.y || 1);
        this.city.selectBuilding(this.city.selectedBuilding);
        this.sim.recalculateFlightPath();
      }
    });

    // 4. Random City & Clear
    this.randomCityBtn.addEventListener('click', () => {
      const startPos = this.sim.packageObj.getPosition();
      const targetPos = this.sim.targetObj.getPosition();
      this.city.generateRandomCity(startPos, targetPos, 22);
      this.sim.recalculateFlightPath();
      this.sim.logMission("Generated randomized urban layout.");
    });

    this.clearBuildingsBtn.addEventListener('click', () => {
      this.city.clearAllBuildings();
      this.sim.recalculateFlightPath();
      this.sim.logMission("Cleared all structures from map.");
    });

    // 5. Preset Scenarios
    this.scenarioSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      const startPos = this.sim.packageObj.getPosition();
      const targetPos = this.sim.targetObj.getPosition();
      this.city.loadScenario(val, startPos, targetPos);
      this.sim.recalculateFlightPath();
      this.sim.logMission(`Loaded scenario: "${e.target.options[e.target.selectedIndex].text}".`);
    });

    // 6. Path Mode Switch
    this.pathModeSelect.addEventListener('change', (e) => {
      const mode = e.target.value;
      this.sim.pathfinder.setMode(mode);
      this.sim.recalculateFlightPath();
      this.sim.logMission(`Flight corridor mode switched to: ${mode.toUpperCase()}.`);
    });

    // 6b. Environment & Wind Controls
    if (this.timeOfDaySelect) {
      this.timeOfDaySelect.addEventListener('change', (e) => {
        if (window.app && window.app.setTimeOfDay) {
          window.app.setTimeOfDay(e.target.value);
          this.sim.logMission(`Atmospheric lighting changed to: ${e.target.value.toUpperCase()}`);
        }
      });
    }

    if (this.windSpeedSlider) {
      this.windSpeedSlider.addEventListener('input', (e) => {
        const spd = parseInt(e.target.value, 10);
        this.windSpeedVal.textContent = spd + ' km/h';
        this.sim.setWind(spd);
      });
    }

    if (this.toggleSafetyBuffers) {
      this.toggleSafetyBuffers.addEventListener('change', (e) => {
        this.city.toggleSafetyBuffers(e.target.checked);
      });
    }

    if (this.toggleFlightTunnel) {
      this.toggleFlightTunnel.addEventListener('change', (e) => {
        this.sim.toggleFlightTunnel(e.target.checked);
      });
    }

    // 7. Launch / Pause / Resume
    this.launchBtn.addEventListener('click', () => {
      if (this.sim.state === 'IDLE' || this.sim.state === 'DELIVERED') {
        this.sim.startMission();
      } else if (this.sim.state === 'PAUSED') {
        this.sim.startMission();
      } else {
        this.sim.pauseMission();
      }
    });

    // 8. Reset
    this.resetBtn.addEventListener('click', () => {
      this.sim.resetMission();
    });

    // 9. Sim Speed
    this.speedBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        this.speedBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mult = parseFloat(btn.dataset.speed);
        this.sim.setSpeedMultiplier(mult);
      });
    });

    // 10. Mute Audio
    this.muteBtn.addEventListener('click', () => {
      window.soundEngine.init();
      const isMuted = window.soundEngine.toggleMute();
      this.muteBtn.textContent = isMuted ? '🔇 Audio Off' : '🔊 Audio On';
    });

    // 11. Camera Views
    this.camBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        this.camBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const view = btn.dataset.view;
        this.cam.setCameraMode(view);
      });
    });

    // 12. Modal Close
    this.modalCloseBtn.addEventListener('click', () => {
      this.completionModal.classList.add('hidden');
    });

    // 13. Sim Callbacks
    this.sim.onTelemetryUpdate = (data) => this.updateTelemetryUI(data);
    this.sim.onMissionLog = (time, text) => this.appendLogEntry(time, text);
    this.sim.onStateChange = (state) => this.onSimStateChange(state);
    this.sim.onMissionComplete = (stats) => this.showMissionCompleteModal(stats);

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        this.launchBtn.click();
      } else if (e.code === 'KeyR') {
        this.resetBtn.click();
      } else if (e.code === 'KeyDelete' || e.code === 'Backspace') {
        if (this.city.selectedBuilding) {
          this.city.removeBuilding(this.city.selectedBuilding);
          this.sim.recalculateFlightPath();
        }
      }
    });
  }

  setActiveTool(tool) {
    this.activeTool = tool;
    this.toolBtns.forEach(b => {
      b.classList.toggle('active', b.dataset.tool === tool);
    });

    // Show/hide sub-palette
    if (tool === 'add-building') {
      this.buildingPalette.classList.remove('hidden');
    } else {
      this.buildingPalette.classList.add('hidden');
      this.city.hideGhost();
    }

    if (tool !== 'select') {
      this.city.selectBuilding(null);
    }

    this.updateHelperTooltip();
  }

  updateHelperTooltip() {
    let msg = "";
    switch (this.activeTool) {
      case 'place-package':
        msg = "📦 Click anywhere on the ground to set the Package Starting Point";
        break;
      case 'place-target':
        msg = "🎯 Click anywhere on the ground to set the Delivery Destination Pad";
        break;
      case 'add-building':
        msg = "🏢 Click on the map to construct a building between start and target";
        break;
      case 'select':
        msg = "✋ Click a building to inspect, resize, or press Delete to remove";
        break;
      default:
        msg = "Ready. Configure obstacles or click Launch Delivery!";
    }
    this.tooltipText.textContent = msg;
  }

  updateToolUI() {
    this.setActiveTool(this.activeTool);
  }

  onSimStateChange(state) {
    this.statusBadge.textContent = state.replace('_', ' ');
    this.statusBadge.className = 'status-badge';

    if (state === 'EN_ROUTE' || state === 'ASCENT') {
      this.statusBadge.classList.add('in-flight');
      this.launchBtn.innerHTML = '⏸ Pause';
      this.launchBtn.classList.add('running');
    } else if (state === 'PAUSED') {
      this.statusBadge.classList.add('warning');
      this.launchBtn.innerHTML = '▶ Resume';
      this.launchBtn.classList.remove('running');
    } else if (state === 'DELIVERED') {
      this.statusBadge.classList.add('delivered');
      this.launchBtn.innerHTML = '▶ Launch';
      this.launchBtn.classList.remove('running');
    } else {
      this.launchBtn.innerHTML = '▶ Launch Delivery';
      this.launchBtn.classList.remove('running');
    }
  }

  updateTelemetryUI(data) {
    if (data.speed !== undefined) this.telemetrySpeed.textContent = data.speed;
    if (data.altitude !== undefined) this.telemetryAltitude.textContent = data.altitude;
    if (data.remainingDist !== undefined) this.telemetryDistance.textContent = data.remainingDist;
    if (data.eta !== undefined) this.telemetryEta.textContent = data.eta + 's';
    if (data.battery !== undefined) {
      this.telemetryBatteryVal.textContent = data.battery + '%';
      this.telemetryBatteryBar.style.width = data.battery + '%';
      if (parseFloat(data.battery) < 25) {
        this.telemetryBatteryBar.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
      } else {
        this.telemetryBatteryBar.style.background = 'linear-gradient(90deg, var(--accent-emerald), #34d399)';
      }
    }
  }

  appendLogEntry(time, text) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">[${time}]</span><span class="log-text">${text}</span>`;
    this.missionLogContainer.appendChild(entry);
    this.missionLogContainer.scrollTop = this.missionLogContainer.scrollHeight;
  }

  showMissionCompleteModal(stats) {
    this.summaryTime.textContent = stats.flightTime;
    this.summaryDist.textContent = stats.totalDistance + 'm';
    this.summarySpeed.textContent = stats.avgSpeedKmh + ' km/h';
    this.summaryEnergy.textContent = stats.energyUsedWh + ' Wh';
    this.completionModal.classList.remove('hidden');
  }
}

window.UIController = UIController;

