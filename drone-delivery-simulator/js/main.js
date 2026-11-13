/**
 * Main Application Entry Point - Three.js Scene, Camera Director, Raycasting & Render Loop
 */

class CameraDirector {
  constructor(camera, controls) {
    this.camera = camera;
    this.controls = controls;
    this.mode = 'orbit'; // 'orbit', 'chase', 'drone_pov', 'topdown', 'isometric'
    this.droneRef = null;
  }

  setCameraMode(mode) {
    this.mode = mode;
    if (mode === 'orbit') {
      this.controls.enabled = true;
      this.controls.autoRotate = false;
    } else if (mode === 'topdown') {
      this.controls.enabled = true;
      this.camera.position.set(0, 160, 0.01);
      this.controls.target.set(0, 0, 0);
      this.controls.update();
    } else if (mode === 'isometric') {
      this.controls.enabled = true;
      this.camera.position.set(90, 85, 90);
      this.controls.target.set(0, 0, 0);
      this.controls.update();
    } else {
      this.controls.enabled = false;
    }
  }

  update(delta) {
    if (!this.droneRef || !this.droneRef.group.visible) {
      if (this.mode === 'chase' || this.mode === 'drone_pov') {
        this.controls.enabled = true;
      }
      this.controls.update();
      return;
    }

    const dronePos = this.droneRef.group.position;
    const droneRotY = this.droneRef.group.rotation.y;

    if (this.mode === 'chase') {
      // Third-person smooth follow camera
      const dist = 14;
      const height = 6.5;
      const targetCamPos = new THREE.Vector3(
        dronePos.x - Math.sin(droneRotY) * dist,
        dronePos.y + height,
        dronePos.z - Math.cos(droneRotY) * dist
      );
      this.camera.position.lerp(targetCamPos, 0.1);
      this.camera.lookAt(dronePos.x, dronePos.y + 1.2, dronePos.z);
    } else if (this.mode === 'drone_pov') {
      // First-person nose camera
      const headPos = new THREE.Vector3(
        dronePos.x + Math.sin(droneRotY) * 0.8,
        dronePos.y + 0.2,
        dronePos.z + Math.cos(droneRotY) * 0.8
      );
      this.camera.position.copy(headPos);
      const lookTarget = new THREE.Vector3(
        dronePos.x + Math.sin(droneRotY) * 20,
        dronePos.y,
        dronePos.z + Math.cos(droneRotY) * 20
      );
      this.camera.lookAt(lookTarget);
    } else {
      this.controls.update();
    }
  }
}

// Application Orchestrator
class App {
  constructor() {
    this.container = document.getElementById('canvas-container');
    this.clock = new THREE.Clock();

    this.initThree();
    this.initEnvironment();
    this.initEntities();
    this.initRaycasting();
    this.initDefaultCity();

    // Start render loop
    this.animate();
  }

  initThree() {
    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0b0f19);
    this.scene.fog = new THREE.FogExp2(0x0b0f19, 0.0035);

    // 2. Camera
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.5, 600);
    this.camera.position.set(-65, 55, 75);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // 4. Controls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.05; // Don't flip below ground
    this.controls.minDistance = 8;
    this.controls.maxDistance = 250;
    this.controls.target.set(0, 0, 0);

    // 5. Camera Director
    this.camDirector = new CameraDirector(this.camera, this.controls);

    window.addEventListener('resize', () => this.onResize());
  }

  initEnvironment() {
    // Ambient light
    this.ambientLight = new THREE.AmbientLight(0x64748b, 0.65);
    this.scene.add(this.ambientLight);

    // Directional Sun Light
    this.sunLight = new THREE.DirectionalLight(0xffffff, 1.2);
    this.sunLight.position.set(70, 110, 60);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 10;
    this.sunLight.shadow.camera.far = 300;
    const shadowD = 90;
    this.sunLight.shadow.camera.left = -shadowD;
    this.sunLight.shadow.camera.right = shadowD;
    this.sunLight.shadow.camera.top = shadowD;
    this.sunLight.shadow.camera.bottom = -shadowD;
    this.sunLight.shadow.bias = -0.0004;
    this.scene.add(this.sunLight);

    // Cyan City Horizon Accent Light
    this.rimLight = new THREE.DirectionalLight(0x06b6d4, 0.5);
    this.rimLight.position.set(-60, 40, -60);
    this.scene.add(this.rimLight);

    // Ground Tactical Grid
    const groundGeo = new THREE.PlaneGeometry(200, 200);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.85,
      metalness: 0.15
    });
    this.groundMesh = new THREE.Mesh(groundGeo, groundMat);
    this.groundMesh.rotation.x = -Math.PI / 2;
    this.groundMesh.receiveShadow = true;
    this.scene.add(this.groundMesh);

    // Tactical Coordinate Grid Lines
    const gridHelper = new THREE.GridHelper(180, 60, 0x0284c7, 0x1e293b);
    gridHelper.position.y = 0.02;
    this.scene.add(gridHelper);
  }

  initEntities() {
    // 1. Package Starting Point (Origin)
    const initialStart = new THREE.Vector3(-45, 0.4, -35);
    this.packageObj = new DeliveryPackage(this.scene, initialStart);

    // 2. Delivery Target (Destination)
    const initialTarget = new THREE.Vector3(45, 0, 35);
    this.targetObj = new DeliveryTarget(this.scene, initialTarget);

    // 3. Drone Entity
    this.drone = new DroneEntity(this.scene);
    this.camDirector.droneRef = this.drone;

    // 4. City Manager
    this.city = new CityManager(this.scene);

    // 5. 3D Pathfinder
    this.pathfinder = new DronePathfinder();

    // 6. Simulation State Controller
    this.sim = new SimulationController(
      this.scene,
      this.drone,
      this.packageObj,
      this.targetObj,
      this.city,
      this.pathfinder
    );

    // 7. UI Controller
    this.ui = new UIController(this.sim, this.city, this.camDirector);
  }

  initDefaultCity() {
    // Build initial buildings in between the drone start and destination
    // Demonstrating obstacle avoidance right out of the box!
    const start = this.packageObj.getPosition();
    const target = this.targetObj.getPosition();

    // Center skyscraper block directly obstructing straight line
    this.city.addBuilding(0, 0, 20, 20, 75, 'skyscraper');
    this.city.addBuilding(-18, 12, 16, 16, 42, 'office');
    this.city.addBuilding(18, -12, 16, 16, 45, 'office');
    this.city.addBuilding(-25, -15, 14, 14, 25, 'house');
    this.city.addBuilding(25, 15, 14, 14, 28, 'house');
    this.city.addBuilding(5, 25, 16, 16, 50, 'office');
    this.city.addBuilding(-5, -25, 16, 16, 48, 'office');

    // Recalculate initial optimal flight corridor
    this.sim.recalculateFlightPath();
    this.sim.logMission("SkyRoute system initialized. 7 urban obstacles detected in sector.");
  }

  setTimeOfDay(mode) {
    if (mode === 'day') {
      this.scene.background.setHex(0x0b0f19);
      this.scene.fog.color.setHex(0x0b0f19);
      this.sunLight.color.setHex(0xffffff);
      this.sunLight.intensity = 1.2;
      this.ambientLight.color.setHex(0x64748b);
      this.ambientLight.intensity = 0.65;
      this.rimLight.color.setHex(0x06b6d4);
      this.rimLight.intensity = 0.5;
    } else if (mode === 'sunset') {
      this.scene.background.setHex(0x1a0b1e);
      this.scene.fog.color.setHex(0x1a0b1e);
      this.sunLight.color.setHex(0xf97316);
      this.sunLight.intensity = 1.4;
      this.ambientLight.color.setHex(0xc084fc);
      this.ambientLight.intensity = 0.5;
      this.rimLight.color.setHex(0xf43f5e);
      this.rimLight.intensity = 0.8;
    } else if (mode === 'night') {
      this.scene.background.setHex(0x020617);
      this.scene.fog.color.setHex(0x020617);
      this.sunLight.color.setHex(0x1e293b);
      this.sunLight.intensity = 0.3;
      this.ambientLight.color.setHex(0x0f172a);
      this.ambientLight.intensity = 0.3;
      this.rimLight.color.setHex(0x38bdf8);
      this.rimLight.intensity = 1.2;
    }
  }

  initRaycasting() {
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();
    this.draggedEntity = null;

    const canvas = this.renderer.domElement;

    // Mouse Down for Interactive Dragging
    canvas.addEventListener('mousedown', (e) => {
      if (e.target.closest('#ui-overlay') && !e.target.classList.contains('interactive')) return;
      if (e.button !== 0) return; // Only left-click drags

      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);

      // Check package drag
      const hitPkg = this.raycaster.intersectObjects(this.packageObj.group.children, true);
      if (hitPkg.length > 0 && this.sim.state === 'IDLE') {
        this.draggedEntity = { type: 'package' };
        this.controls.enabled = false;
        canvas.classList.add('cursor-grabbing');
        return;
      }

      // Check target pad drag
      const hitTarget = this.raycaster.intersectObjects(this.targetObj.group.children, true);
      if (hitTarget.length > 0 && this.sim.state === 'IDLE') {
        this.draggedEntity = { type: 'target' };
        this.controls.enabled = false;
        canvas.classList.add('cursor-grabbing');
        return;
      }

      // Check building drag in select mode
      if (this.ui.activeTool === 'select') {
        const hitBld = this.raycaster.intersectObjects(this.city.buildingGroup.children, true);
        if (hitBld.length > 0) {
          let bData = null;
          let curr = hitBld[0].object;
          while (curr) {
            if (curr.userData && curr.userData.buildingData) {
              bData = curr.userData.buildingData;
              break;
            }
            curr = curr.parent;
          }
          if (bData) {
            this.draggedEntity = { type: 'building', data: bData };
            this.city.selectBuilding(bData);
            this.controls.enabled = false;
            canvas.classList.add('cursor-grabbing');
          }
        }
      }
    });

    // Mouse Move for Dragging & Ghost Preview
    canvas.addEventListener('mousemove', (e) => {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

      // Handle active drag
      if (this.draggedEntity) {
        this.wasDragging = true;
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObject(this.groundMesh);
        if (intersects.length > 0) {
          const pt = intersects[0].point;
          const snapX = Math.max(-75, Math.min(75, Math.round(pt.x / 2) * 2));
          const snapZ = Math.max(-75, Math.min(75, Math.round(pt.z / 2) * 2));

          if (this.draggedEntity.type === 'package') {
            this.packageObj.setPosition(snapX, 0.4, snapZ);
            this.sim.recalculateFlightPath();
          } else if (this.draggedEntity.type === 'target') {
            this.targetObj.setPosition(snapX, 0, snapZ);
            this.sim.recalculateFlightPath();
          } else if (this.draggedEntity.type === 'building') {
            this.city.moveBuilding(this.draggedEntity.data, snapX, snapZ);
            this.sim.recalculateFlightPath();
          }
        }
        return;
      }

      // Ghost preview for Add Building tool
      if (this.ui.activeTool === 'add-building') {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObject(this.groundMesh);
        if (intersects.length > 0) {
          const pt = intersects[0].point;
          const snapX = Math.round(pt.x / 2) * 2;
          const snapZ = Math.round(pt.z / 2) * 2;

          const dStart = Math.hypot(snapX - this.packageObj.getPosition().x, snapZ - this.packageObj.getPosition().z);
          const dTarget = Math.hypot(snapX - this.targetObj.getPosition().x, snapZ - this.targetObj.getPosition().z);
          const isValid = dStart > 8 && dTarget > 8 && Math.abs(snapX) < 75 && Math.abs(snapZ) < 75;

          this.city.updateGhostPlacement(snapX, snapZ, isValid);
        }
      }
    });

    // Mouse Up: End Dragging
    window.addEventListener('mouseup', () => {
      if (this.draggedEntity) {
        this.draggedEntity = null;
        if (this.camDirector.mode === 'orbit' || this.camDirector.mode === 'topdown' || this.camDirector.mode === 'isometric') {
          this.controls.enabled = true;
        }
        canvas.classList.remove('cursor-grabbing');
      }
    });

    canvas.addEventListener('mouseleave', () => {
      this.city.hideGhost();
    });

    // Mouse Click for Placement / Selection
    canvas.addEventListener('click', (e) => {
      // Ignore clicks if clicking UI overlay or if just finished dragging
      if (e.target.closest('#ui-overlay') && !e.target.classList.contains('interactive')) return;
      if (this.wasDragging) {
        this.wasDragging = false;
        return;
      }

      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      this.raycaster.setFromCamera(this.mouse, this.camera);

      // Tool: Place Package (Start)
      if (this.ui.activeTool === 'place-package') {
        const intersects = this.raycaster.intersectObject(this.groundMesh);
        if (intersects.length > 0) {
          const pt = intersects[0].point;
          this.packageObj.setPosition(pt.x, 0.4, pt.z);
          this.sim.recalculateFlightPath();
          this.sim.logMission(`Package starting point set to (${pt.x.toFixed(1)}, ${pt.z.toFixed(1)})`);
          window.soundEngine.init();
          window.soundEngine.playWaypoint();
        }
      }
      // Tool: Place Target (Drop-off)
      else if (this.ui.activeTool === 'place-target') {
        const intersects = this.raycaster.intersectObject(this.groundMesh);
        if (intersects.length > 0) {
          const pt = intersects[0].point;
          this.targetObj.setPosition(pt.x, 0, pt.z);
          this.sim.recalculateFlightPath();
          this.sim.logMission(`Delivery destination set to (${pt.x.toFixed(1)}, ${pt.z.toFixed(1)})`);
          window.soundEngine.init();
          window.soundEngine.playWaypoint();
        }
      }
      // Tool: Add Building
      else if (this.ui.activeTool === 'add-building') {
        const intersects = this.raycaster.intersectObject(this.groundMesh);
        if (intersects.length > 0) {
          const pt = intersects[0].point;
          const snapX = Math.round(pt.x / 2) * 2;
          const snapZ = Math.round(pt.z / 2) * 2;

          const dStart = Math.hypot(snapX - this.packageObj.getPosition().x, snapZ - this.packageObj.getPosition().z);
          const dTarget = Math.hypot(snapX - this.targetObj.getPosition().x, snapZ - this.targetObj.getPosition().z);

          if (dStart > 8 && dTarget > 8) {
            const dims = this.city.getDimensionsForType(this.city.currentBuildingType, this.city.currentBuildingHeight);
            this.city.addBuilding(snapX, snapZ, dims.width, dims.depth, dims.height, this.city.currentBuildingType);
            this.sim.recalculateFlightPath();
            this.sim.logMission(`Constructed ${this.city.currentBuildingType.toUpperCase()} (H: ${dims.height}m) at (${snapX}, ${snapZ}). Route re-optimized.`);
            window.soundEngine.init();
            window.soundEngine.playWaypoint();
          }
        }
      }
      // Tool: Select Building
      else if (this.ui.activeTool === 'select') {
        const intersects = this.raycaster.intersectObjects(this.city.buildingGroup.children, true);
        if (intersects.length > 0) {
          let bData = null;
          let curr = intersects[0].object;
          while (curr) {
            if (curr.userData && curr.userData.buildingData) {
              bData = curr.userData.buildingData;
              break;
            }
            curr = curr.parent;
          }
          if (bData) {
            this.city.selectBuilding(bData);
            this.ui.buildingHeightInput.value = bData.height;
            this.ui.buildingHeightVal.textContent = bData.height + 'm';
            this.sim.logMission(`Selected structure ${bData.type.toUpperCase()} [ID: ${bData.id}]. Adjust height or press Delete.`);
          }
        } else {
          this.city.selectBuilding(null);
        }
      }
    });
  }

  onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const delta = Math.min(0.1, this.clock.getDelta());

    // Update animations
    this.city.update(delta);
    this.packageObj.update(delta);
    this.targetObj.update(delta);
    this.drone.update(delta);
    this.sim.update(delta);
    this.camDirector.update(delta);

    this.renderer.render(this.scene, this.camera);
  }
}

// Bootstrap once window loads
window.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
