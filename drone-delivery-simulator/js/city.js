/**
 * City Manager - Handles 3D Building Creation, Textures, Scenarios, Selection & Obstacle Data
 */

class CityManager {
  constructor(scene) {
    this.scene = scene;
    this.buildings = [];
    this.buildingGroup = new THREE.Group();
    this.scene.add(this.buildingGroup);

    // Selected building reference
    this.selectedBuilding = null;
    this.selectionBox = null;

    // Ghost preview mesh for building placement
    this.ghostMesh = null;
    this.currentBuildingType = 'office';
    this.currentBuildingHeight = 35;

    // Procedural canvas textures for building facades
    this.textures = this.generateProceduralTextures();

    // Red aviation beacons array for blinking animation
    this.beacons = [];
    this.beaconClock = 0;

    // Safety buffer visualization group
    this.showSafetyBuffers = false;
    this.bufferGroup = new THREE.Group();
    this.bufferGroup.visible = false;
    this.scene.add(this.bufferGroup);

    // Create selection bounding box helper
    this.initSelectionBox();
  }

  generateProceduralTextures() {
    // 1. Modern Glass Office Facade
    const canvasOffice = document.createElement('canvas');
    canvasOffice.width = 256;
    canvasOffice.height = 256;
    const ctxO = canvasOffice.getContext('2d');
    ctxO.fillStyle = '#1e293b';
    ctxO.fillRect(0, 0, 256, 256);
    
    // Windows grid
    ctxO.fillStyle = '#38bdf8';
    for (let y = 16; y < 256; y += 32) {
      for (let x = 16; x < 256; x += 32) {
        if (Math.random() > 0.15) {
          ctxO.fillStyle = Math.random() > 0.4 ? '#7dd3fc' : '#0284c7';
          ctxO.fillRect(x, y, 20, 22);
        }
      }
    }
    const textureOffice = new THREE.CanvasTexture(canvasOffice);
    textureOffice.wrapS = THREE.RepeatWrapping;
    textureOffice.wrapT = THREE.RepeatWrapping;

    // 2. Concrete / Skyscraper Facade
    const canvasTower = document.createElement('canvas');
    canvasTower.width = 256;
    canvasTower.height = 256;
    const ctxT = canvasTower.getContext('2d');
    ctxT.fillStyle = '#0f172a';
    ctxT.fillRect(0, 0, 256, 256);

    ctxT.fillStyle = '#60a5fa';
    for (let y = 10; y < 256; y += 24) {
      for (let x = 10; x < 256; x += 24) {
        if (Math.random() > 0.2) {
          ctxT.fillStyle = Math.random() > 0.5 ? '#93c5fd' : '#1e3a8a';
          ctxT.fillRect(x, y, 14, 16);
        }
      }
    }
    const textureTower = new THREE.CanvasTexture(canvasTower);
    textureTower.wrapS = THREE.RepeatWrapping;
    textureTower.wrapT = THREE.RepeatWrapping;

    return {
      office: textureOffice,
      tower: textureTower
    };
  }

  initSelectionBox() {
    const boxGeo = new THREE.BoxGeometry(1, 1, 1);
    const boxMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      wireframe: true,
      transparent: true,
      opacity: 0.8
    });
    this.selectionBox = new THREE.Mesh(boxGeo, boxMat);
    this.selectionBox.visible = false;
    this.scene.add(this.selectionBox);
  }

  // Create building definition and 3D mesh
  addBuilding(x, z, width, depth, height, type = 'office') {
    const group = new THREE.Group();
    group.position.set(x, 0, z);

    let mainMesh;
    let material;

    if (type === 'noflyzone') {
      // Cylindrical holographic restricted airspace
      const geo = new THREE.CylinderGeometry(width / 2, width / 2, height, 32);
      material = new THREE.MeshStandardMaterial({
        color: 0xf43f5e,
        transparent: true,
        opacity: 0.35,
        wireframe: false,
        emissive: 0x881337,
        emissiveIntensity: 0.6
      });
      mainMesh = new THREE.Mesh(geo, material);
      mainMesh.position.y = height / 2;
      group.add(mainMesh);

      // Wireframe warning perimeter rings
      const wireGeo = new THREE.CylinderGeometry(width / 2, width / 2, height, 16, 4, true);
      const wireMat = new THREE.MeshBasicMaterial({
        color: 0xf43f5e,
        wireframe: true,
        transparent: true,
        opacity: 0.7
      });
      const wireMesh = new THREE.Mesh(wireGeo, wireMat);
      wireMesh.position.y = height / 2;
      group.add(wireMesh);
    } else {
      // Solid architectural building
      const tex = type === 'skyscraper' || type === 'megatower' ? this.textures.tower.clone() : this.textures.office.clone();
      tex.repeat.set(Math.max(1, Math.round(width / 8)), Math.max(1, Math.round(height / 10)));
      tex.needsUpdate = true;

      const geo = new THREE.BoxGeometry(width, height, depth);
      const wallMat = new THREE.MeshStandardMaterial({
        color: type === 'house' ? 0x94a3b8 : 0xffffff,
        map: tex,
        roughness: 0.3,
        metalness: 0.6
      });
      const roofMat = new THREE.MeshStandardMaterial({
        color: 0x1e293b,
        roughness: 0.8,
        metalness: 0.2
      });

      // Multi-material cube: walls vs roof/floor
      const materials = [wallMat, wallMat, roofMat, roofMat, wallMat, wallMat];
      mainMesh = new THREE.Mesh(geo, materials);
      mainMesh.position.y = height / 2;
      mainMesh.castShadow = true;
      mainMesh.receiveShadow = true;
      group.add(mainMesh);

      // Rooftop details (HVAC units, antenna, aviation warning light)
      if (height > 25) {
        this.addRooftopDetails(group, width, depth, height);
      }
    }

    // Metadata payload attached to mesh for raycasting
    const buildingData = {
      id: 'bld_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
      x: x,
      z: z,
      width: width,
      depth: depth,
      height: height,
      type: type,
      group: group,
      mainMesh: mainMesh
    };

    mainMesh.userData = { buildingData: buildingData };
    group.userData = { buildingData: buildingData };

    this.buildings.push(buildingData);
    this.buildingGroup.add(group);
    this.updateSafetyBuffers();

    return buildingData;
  }

  addRooftopDetails(group, width, depth, height) {
    // 1. Elevator penthouse / HVAC box
    const hvacGeo = new THREE.BoxGeometry(width * 0.4, 3, depth * 0.4);
    const hvacMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });
    const hvac = new THREE.Mesh(hvacGeo, hvacMat);
    hvac.position.set(0, height + 1.5, 0);
    hvac.castShadow = true;
    group.add(hvac);

    // 2. High aviation spire / beacon on tall towers
    if (height >= 40) {
      const spireH = Math.min(14, height * 0.15);
      const spireGeo = new THREE.CylinderGeometry(0.2, 0.4, spireH, 8);
      const spireMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8 });
      const spire = new THREE.Mesh(spireGeo, spireMat);
      spire.position.set(0, height + 3 + spireH / 2, 0);
      group.add(spire);

      // Flashing red obstruction beacon light
      const beaconGeo = new THREE.SphereGeometry(0.5, 12, 12);
      const beaconMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
      const beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
      beaconMesh.position.set(0, height + 3 + spireH + 0.3, 0);
      group.add(beaconMesh);

      this.beacons.push({
        mesh: beaconMesh,
        mat: beaconMat,
        baseY: height + 3 + spireH + 0.3
      });
    }
  }

  // Ghost mesh for interactive placement preview
  updateGhostPlacement(x, z, isValid = true) {
    if (!this.ghostMesh) {
      this.createGhostMesh();
    }
    this.ghostMesh.visible = true;
    this.ghostMesh.position.set(x, this.currentBuildingHeight / 2, z);
    
    const mat = this.ghostMesh.material;
    if (isValid) {
      mat.color.setHex(0x10b981); // Emerald green for valid
      mat.opacity = 0.55;
    } else {
      mat.color.setHex(0xf43f5e); // Rose red for blocked
      mat.opacity = 0.65;
    }
  }

  createGhostMesh() {
    let dims = this.getDimensionsForType(this.currentBuildingType, this.currentBuildingHeight);
    let geo;
    if (this.currentBuildingType === 'noflyzone') {
      geo = new THREE.CylinderGeometry(dims.width / 2, dims.width / 2, dims.height, 24);
    } else {
      geo = new THREE.BoxGeometry(dims.width, dims.height, dims.depth);
    }
    const mat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.5,
      wireframe: true
    });
    this.ghostMesh = new THREE.Mesh(geo, mat);
    this.scene.add(this.ghostMesh);
  }

  hideGhost() {
    if (this.ghostMesh) {
      this.ghostMesh.visible = false;
    }
  }

  setPlacementType(type, height) {
    this.currentBuildingType = type;
    if (height !== undefined) {
      this.currentBuildingHeight = height;
    }
    if (this.ghostMesh) {
      this.scene.remove(this.ghostMesh);
      this.ghostMesh.geometry.dispose();
      this.ghostMesh.material.dispose();
      this.ghostMesh = null;
    }
    this.createGhostMesh();
  }

  getDimensionsForType(type, customHeight = 35) {
    switch (type) {
      case 'house':
        return { width: 10, depth: 10, height: Math.min(customHeight, 18) };
      case 'office':
        return { width: 16, depth: 16, height: customHeight };
      case 'skyscraper':
        return { width: 20, depth: 20, height: Math.max(customHeight, 60) };
      case 'megatower':
        return { width: 24, depth: 24, height: Math.max(customHeight, 95) };
      case 'tower':
        return { width: 5, depth: 5, height: Math.max(customHeight, 80) };
      case 'noflyzone':
        return { width: 28, depth: 28, height: customHeight };
      default:
        return { width: 16, depth: 16, height: customHeight };
    }
  }

  selectBuilding(buildingData) {
    this.selectedBuilding = buildingData;
    if (buildingData) {
      this.selectionBox.visible = true;
      this.selectionBox.position.set(buildingData.x, buildingData.height / 2, buildingData.z);
      this.selectionBox.scale.set(buildingData.width + 1.2, buildingData.height + 1.2, buildingData.depth + 1.2);
    } else {
      this.selectionBox.visible = false;
    }
  }

  removeBuilding(buildingData) {
    if (!buildingData) return;
    const idx = this.buildings.indexOf(buildingData);
    if (idx !== -1) {
      this.buildings.splice(idx, 1);
      this.buildingGroup.remove(buildingData.group);

      // Clean up beacons
      this.beacons = this.beacons.filter(b => !buildingData.group.children.includes(b.mesh));

      // Dispose geometries & materials
      buildingData.group.traverse((child) => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach(m => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });

      if (this.selectedBuilding === buildingData) {
        this.selectBuilding(null);
      }
      this.updateSafetyBuffers();
    }
  }

  moveBuilding(buildingData, newX, newZ) {
    if (!buildingData) return;
    buildingData.x = newX;
    buildingData.z = newZ;
    buildingData.group.position.set(newX, 0, newZ);
    if (this.selectedBuilding === buildingData) {
      this.selectBuilding(buildingData);
    }
    this.updateSafetyBuffers();
  }

  toggleSafetyBuffers(visible) {
    this.showSafetyBuffers = visible;
    this.bufferGroup.visible = visible;
    if (visible) {
      this.updateSafetyBuffers();
    }
  }

  updateSafetyBuffers() {
    if (!this.bufferGroup) return;
    while (this.bufferGroup.children.length > 0) {
      const child = this.bufferGroup.children[0];
      this.bufferGroup.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
    }
    if (!this.showSafetyBuffers) return;

    const bufH = 2.8;
    const bufV = 3.2;
    for (const b of this.buildings) {
      const geo = new THREE.BoxGeometry(b.width + bufH * 2, b.height + bufV, b.depth + bufH * 2);
      const mat = new THREE.MeshBasicMaterial({
        color: 0x06b6d4,
        wireframe: true,
        transparent: true,
        opacity: 0.22
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(b.x, (b.height + bufV) / 2, b.z);
      this.bufferGroup.add(mesh);
    }
  }

  clearAllBuildings() {
    this.selectBuilding(null);
    for (const b of [...this.buildings]) {
      this.removeBuilding(b);
    }
    this.buildings = [];
    this.beacons = [];
    this.updateSafetyBuffers();
  }

  // Animation update for flashing aviation beacons
  update(delta) {
    this.beaconClock += delta * 3.5;
    const flash = Math.sin(this.beaconClock) > 0.4 ? 1.0 : 0.15;
    for (let i = 0; i < this.beacons.length; i++) {
      this.beacons[i].mat.color.setRGB(flash, 0, 0);
    }
  }

  // Preset Scenario Loaders
  loadScenario(scenarioName, startPos, targetPos) {
    this.clearAllBuildings();

    switch (scenarioName) {
      case 'canyons':
        this.buildUrbanCanyonsScenario(startPos, targetPos);
        break;
      case 'wall':
        this.buildSkyscraperWallScenario(startPos, targetPos);
        break;
      case 'maze':
        this.buildMazeChallengeScenario(startPos, targetPos);
        break;
      case 'suburb':
        this.buildSuburbanScenario(startPos, targetPos);
        break;
      case 'nofly':
        this.buildAirspaceRestrictionScenario(startPos, targetPos);
        break;
      case 'clean':
      default:
        // Clean empty map
        break;
    }
  }

  buildUrbanCanyonsScenario(start, target) {
    // Grid of high-rises forming urban avenues and canyons
    for (let x = -60; x <= 60; x += 30) {
      for (let z = -60; z <= 60; z += 30) {
        // Skip spots too close to start and target
        const dStart = Math.hypot(x - start.x, z - start.z);
        const dTarget = Math.hypot(x - target.x, z - target.z);
        if (dStart > 18 && dTarget > 18) {
          const h = 45 + Math.floor(Math.random() * 45);
          const type = h > 70 ? 'skyscraper' : 'office';
          this.addBuilding(x, z, 18, 18, h, type);
        }
      }
    }
  }

  buildSkyscraperWallScenario(start, target) {
    // A contiguous line of towering skyscrapers across the flight path
    // Drone has to either climb high or navigate around edges
    const midX = (start.x + target.x) / 2;
    const midZ = (start.z + target.z) / 2;
    const perpX = -(target.z - start.z);
    const perpZ = (target.x - start.x);
    const len = Math.hypot(perpX, perpZ);
    const uX = perpX / len;
    const uZ = perpZ / len;

    for (let i = -3; i <= 3; i++) {
      const bx = midX + i * 18 * uX;
      const bz = midZ + i * 18 * uZ;
      const h = 75 + Math.abs(i) * 10;
      this.addBuilding(bx, bz, 16, 16, h, 'skyscraper');
    }
  }

  buildMazeChallengeScenario(start, target) {
    // S-bend labyrinth
    const wallHeight = 40;
    // Row 1
    for (let x = -50; x <= 20; x += 16) {
      this.addBuilding(x, -15, 14, 14, wallHeight, 'office');
    }
    // Row 2
    for (let x = -20; x <= 50; x += 16) {
      this.addBuilding(x, 15, 14, 14, wallHeight, 'office');
    }
    // Flanking blocks
    this.addBuilding(-45, 15, 14, 14, wallHeight, 'office');
    this.addBuilding(45, -15, 14, 14, wallHeight, 'office');
  }

  buildSuburbanScenario(start, target) {
    for (let i = 0; i < 22; i++) {
      const x = (Math.random() - 0.5) * 110;
      const z = (Math.random() - 0.5) * 110;
      if (Math.hypot(x - start.x, z - start.z) > 16 && Math.hypot(x - target.x, z - target.z) > 16) {
        this.addBuilding(x, z, 12, 12, 14 + Math.random() * 12, 'house');
      }
    }
  }

  buildAirspaceRestrictionScenario(start, target) {
    const midX = (start.x + target.x) / 2;
    const midZ = (start.z + target.z) / 2;
    // Massive restricted airspace in center + flanking office blocks
    this.addBuilding(midX, midZ, 36, 36, 80, 'noflyzone');
    this.addBuilding(midX - 28, midZ - 20, 16, 16, 50, 'office');
    this.addBuilding(midX + 28, midZ + 20, 16, 16, 50, 'office');
  }

  generateRandomCity(startPos, targetPos, count = 18) {
    this.clearAllBuildings();
    let placed = 0;
    let attempts = 0;

    while (placed < count && attempts++ < 150) {
      const x = Math.round((Math.random() - 0.5) * 120 / 5) * 5;
      const z = Math.round((Math.random() - 0.5) * 120 / 5) * 5;

      const dStart = Math.hypot(x - startPos.x, z - startPos.z);
      const dTarget = Math.hypot(x - targetPos.x, z - targetPos.z);
      if (dStart < 16 || dTarget < 16) continue;

      // Check collision with already placed buildings
      let collides = false;
      for (const b of this.buildings) {
        if (Math.hypot(x - b.x, z - b.z) < 20) {
          collides = true;
          break;
        }
      }
      if (collides) continue;

      const types = ['office', 'office', 'skyscraper', 'house', 'megatower'];
      const type = types[Math.floor(Math.random() * types.length)];
      const h = type === 'house' ? 14 : (type === 'office' ? 35 + Math.random() * 25 : 65 + Math.random() * 45);
      const dims = this.getDimensionsForType(type, h);

      this.addBuilding(x, z, dims.width, dims.depth, dims.height, type);
      placed++;
    }
  }
}

window.CityManager = CityManager;

