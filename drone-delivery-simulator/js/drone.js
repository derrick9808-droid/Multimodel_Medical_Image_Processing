/**
 * Drone Entity & Delivery Target / Package System
 * Handles 3D Quadcopter model, spinning rotors, banking physics, winch latching, package pickup & delivery.
 */

class DroneEntity {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.scene.add(this.group);

    // Propellers for rotation animation
    this.rotors = [];
    this.rotorDiscs = [];

    // Winch & Cargo mechanism
    this.winchCable = null;
    this.winchLatch = null;
    this.winchLength = 0; // Length extended
    this.maxWinchLength = 8.0;

    // Package reference
    this.packageMesh = null;
    this.isCarryingPackage = false;
    this.packageOffset = new THREE.Vector3(0, -1.2, 0);

    // Kinematics & Banking
    this.velocity = new THREE.Vector3();
    this.targetRotation = new THREE.Euler();
    this.bankAngle = 0;
    this.pitchAngle = 0;

    // Spotlight beam
    this.spotLight = null;

    // Navigation LEDs
    this.strobeLight = null;
    this.strobeClock = 0;

    // Build 3D quadcopter model
    this.buildDroneModel();

    // Start hidden or at standby depot
    this.group.visible = false;
  }

  buildDroneModel() {
    // 1. Central Aerodynamic Carbon Fuselage
    const bodyGeo = new THREE.CylinderGeometry(0.9, 1.2, 0.45, 8);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.3,
      metalness: 0.8
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.castShadow = true;
    this.group.add(body);

    // Top Dome Cover (Cyan Tech Accent)
    const domeGeo = new THREE.SphereGeometry(0.75, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const domeMat = new THREE.MeshStandardMaterial({
      color: 0x06b6d4,
      roughness: 0.2,
      metalness: 0.5,
      emissive: 0x0891b2,
      emissiveIntensity: 0.2
    });
    const dome = new THREE.Mesh(domeGeo, domeMat);
    dome.position.y = 0.22;
    this.group.add(dome);

    // Forward Sensor / Dual Eye Camera
    const camGeo = new THREE.BoxGeometry(0.4, 0.2, 0.3);
    const camMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7 });
    const cam = new THREE.Mesh(camGeo, camMat);
    cam.position.set(0, 0, 0.95);
    this.group.add(cam);

    // 2. Four Radial Motor Arms (X-Configuration)
    const armMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9, roughness: 0.2 });
    const motorMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7 });

    const armAngleOffsets = [Math.PI / 4, 3 * Math.PI / 4, 5 * Math.PI / 4, 7 * Math.PI / 4];
    const armLength = 2.2;

    armAngleOffsets.forEach((angle, idx) => {
      // Carbon arm cylinder
      const armGeo = new THREE.CylinderGeometry(0.08, 0.08, armLength, 8);
      const arm = new THREE.Mesh(armGeo, armMat);
      arm.rotation.z = Math.PI / 2;
      arm.rotation.y = angle;
      arm.position.set((Math.cos(angle) * armLength) / 2, 0, (Math.sin(angle) * armLength) / 2);
      this.group.add(arm);

      // Brushless motor nacelle at end of arm
      const motorX = Math.cos(angle) * armLength;
      const motorZ = Math.sin(angle) * armLength;

      const motorGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.35, 12);
      const motor = new THREE.Mesh(motorGeo, motorMat);
      motor.position.set(motorX, 0.1, motorZ);
      this.group.add(motor);

      // 2-Blade Propeller Mesh
      const rotorGroup = new THREE.Group();
      rotorGroup.position.set(motorX, 0.3, motorZ);

      const bladeGeo = new THREE.BoxGeometry(1.6, 0.02, 0.14);
      const bladeMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.5 });
      const blade = new THREE.Mesh(bladeGeo, bladeMat);
      rotorGroup.add(blade);

      // High-speed semi-transparent rotor blur disc
      const discGeo = new THREE.CircleGeometry(0.85, 24);
      const discMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.25,
        side: THREE.DoubleSide
      });
      const disc = new THREE.Mesh(discGeo, discMat);
      disc.rotation.x = Math.PI / 2;
      disc.position.y = 0.02;
      rotorGroup.add(disc);

      this.rotors.push({
        group: rotorGroup,
        direction: idx % 2 === 0 ? 1 : -1 // Counter-rotating pairs
      });
      this.rotorDiscs.push(disc);
      this.group.add(rotorGroup);

      // Nav LED on motor nacelle
      const ledGeo = new THREE.SphereGeometry(0.08, 8, 8);
      let ledColor = 0xffffff;
      if (idx === 0) ledColor = 0x10b981; // Starboard Green (front right)
      else if (idx === 1) ledColor = 0xf43f5e; // Port Red (front left)
      else if (idx === 2) ledColor = 0xf59e0b; // Amber rear left
      else ledColor = 0x38bdf8; // Cyan rear right

      const ledMat = new THREE.MeshBasicMaterial({ color: ledColor });
      const led = new THREE.Mesh(ledGeo, ledMat);
      led.position.set(motorX, -0.1, motorZ);
      this.group.add(led);
    });

    // 3. Landing Skids / Gear
    const skidMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.8 });
    const createSkid = (xOffset) => {
      const legGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.7, 6);
      const leg1 = new THREE.Mesh(legGeo, skidMat);
      leg1.position.set(xOffset, -0.35, 0.6);
      leg1.rotation.x = 0.2;
      this.group.add(leg1);

      const leg2 = new THREE.Mesh(legGeo, skidMat);
      leg2.position.set(xOffset, -0.35, -0.6);
      leg2.rotation.x = -0.2;
      this.group.add(leg2);

      const runnerGeo = new THREE.CylinderGeometry(0.06, 0.06, 1.8, 8);
      const runner = new THREE.Mesh(runnerGeo, skidMat);
      runner.rotation.x = Math.PI / 2;
      runner.position.set(xOffset, -0.65, 0);
      this.group.add(runner);
    };
    createSkid(0.8);
    createSkid(-0.8);

    // 4. Downward Searchlight / Spotlight
    this.spotLight = new THREE.SpotLight(0xa5f3fc, 3.5, 45, Math.PI / 5, 0.3, 1.2);
    this.spotLight.position.set(0, -0.2, 0.5);
    this.spotLight.target.position.set(0, -20, 5);
    this.group.add(this.spotLight);
    this.group.add(this.spotLight.target);

    // 5. Motorized Winch Cable & Magnetic Latch
    const cableGeo = new THREE.CylinderGeometry(0.02, 0.02, 1, 6);
    const cableMat = new THREE.MeshBasicMaterial({ color: 0x94a3b8 });
    this.winchCable = new THREE.Mesh(cableGeo, cableMat);
    this.winchCable.position.set(0, -0.5, 0);
    this.winchCable.visible = false;
    this.group.add(this.winchCable);

    const latchGeo = new THREE.CylinderGeometry(0.3, 0.35, 0.15, 12);
    const latchMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      metalness: 0.9,
      roughness: 0.2,
      emissive: 0x0369a1,
      emissiveIntensity: 0.5
    });
    this.winchLatch = new THREE.Mesh(latchGeo, latchMat);
    this.winchLatch.position.set(0, -0.6, 0);
    this.winchLatch.visible = false;
    this.group.add(this.winchLatch);
  }

  // Set winch cable extension length
  setWinchExtension(length) {
    this.winchLength = length;
    if (length <= 0.05) {
      this.winchCable.visible = false;
      this.winchLatch.visible = false;
    } else {
      this.winchCable.visible = true;
      this.winchLatch.visible = true;
      this.winchCable.scale.set(1, length, 1);
      this.winchCable.position.set(0, -length / 2, 0);
      this.winchLatch.position.set(0, -length, 0);
    }
  }

  // Update rotor spin and banking
  update(delta, speedRatio = 0, climbRate = 0) {
    // 1. Rotor spinning animation
    const spinSpeed = 24 + speedRatio * 35 + Math.max(0, climbRate * 15);
    for (let i = 0; i < this.rotors.length; i++) {
      const r = this.rotors[i];
      r.group.rotation.y += spinSpeed * delta * r.direction;
      this.rotorDiscs[i].material.opacity = 0.2 + speedRatio * 0.3;
    }

    // 2. Navigation strobe light flashing
    this.strobeClock += delta * 4;
    if (this.spotLight) {
      this.spotLight.intensity = 2.8 + Math.sin(this.strobeClock * 3) * 0.4;
    }

    // 3. Smooth banking and pitch orientation
    this.group.rotation.x = THREE.MathUtils.lerp(this.group.rotation.x, this.pitchAngle, 0.1);
    this.group.rotation.z = THREE.MathUtils.lerp(this.group.rotation.z, this.bankAngle, 0.1);
  }

  setFlightKinematics(tangent, speed, lateralAccel, climbRate) {
    // Pitch forward when moving
    this.pitchAngle = Math.min(0.45, Math.max(-0.25, speed * 0.025));
    // Roll bank into turns
    this.bankAngle = Math.min(0.55, Math.max(-0.55, -lateralAccel * 0.08));

    // Align yaw towards tangent vector
    if (tangent && tangent.lengthSq() > 0.001) {
      const targetYaw = Math.atan2(tangent.x, tangent.z);
      // Smooth yaw interpolation
      const currentYaw = this.group.rotation.y;
      let diff = targetYaw - currentYaw;
      while (diff < -Math.PI) diff += Math.PI * 2;
      while (diff > Math.PI) diff -= Math.PI * 2;
      this.group.rotation.y += diff * 0.15;
    }
  }

  attachPackage(packageMesh) {
    this.packageMesh = packageMesh;
    this.isCarryingPackage = true;
    this.group.add(packageMesh);
    packageMesh.position.copy(this.packageOffset);
    packageMesh.rotation.set(0, 0, 0);
  }

  releasePackage(targetWorldPos) {
    if (!this.packageMesh) return;
    this.group.remove(this.packageMesh);
    this.scene.add(this.packageMesh);
    this.packageMesh.position.copy(targetWorldPos);
    this.packageMesh.position.y = 0.4; // Ground height
    this.isCarryingPackage = false;
    this.packageMesh = null;
  }
}

/**
 * Package System - Priority Parcel Box with Delivery Graphics
 */
class DeliveryPackage {
  constructor(scene, initialPos) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.savedPosition = new THREE.Vector3(initialPos.x, initialPos.y, initialPos.z);
    this.scene.add(this.group);

    this.buildPackage();
    this.setPosition(initialPos.x, initialPos.y, initialPos.z);
  }

  buildPackage() {
    // Cardboard delivery box
    const boxGeo = new THREE.BoxGeometry(1.2, 0.8, 1.0);
    const boxMat = new THREE.MeshStandardMaterial({
      color: 0xd97706, // Cardboard brown
      roughness: 0.8,
      metalness: 0.1
    });
    const boxMesh = new THREE.Mesh(boxGeo, boxMat);
    boxMesh.castShadow = true;
    boxMesh.receiveShadow = true;
    this.group.add(boxMesh);

    // Hazard / Courier tape stripe
    const tapeGeo = new THREE.BoxGeometry(1.22, 0.15, 1.02);
    const tapeMat = new THREE.MeshBasicMaterial({ color: 0x0284c7 });
    const tapeMesh = new THREE.Mesh(tapeGeo, tapeMat);
    this.group.add(tapeMesh);

    // Top Magnetic Latch Plate
    const plateGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.06, 12);
    const plateMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.9, roughness: 0.1 });
    const plateMesh = new THREE.Mesh(plateGeo, plateMat);
    plateMesh.position.y = 0.43;
    this.group.add(plateMesh);

    // Blinking status beacon
    const beaconGeo = new THREE.SphereGeometry(0.08, 8, 8);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    this.beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
    this.beaconMesh.position.set(0.4, 0.44, 0.3);
    this.group.add(this.beaconMesh);

    // Ground Pickup Marker Ring
    const ringGeo = new THREE.RingGeometry(1.4, 1.7, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7
    });
    this.groundRing = new THREE.Mesh(ringGeo, ringMat);
    this.groundRing.rotation.x = -Math.PI / 2;
    this.groundRing.position.y = 0.05;
    this.group.add(this.groundRing);
  }

  setPosition(x, y, z) {
    this.savedPosition.set(x, y, z);
    this.group.position.set(x, y, z);
  }

  getPosition() {
    return this.savedPosition.clone();
  }

  update(delta) {
    if (this.groundRing) {
      this.groundRing.rotation.z += delta * 0.8;
    }
  }
}

/**
 * Delivery Target System - Glowing Landing Pad & Holographic Beacon
 */
class DeliveryTarget {
  constructor(scene, initialPos) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.savedPosition = new THREE.Vector3(initialPos.x, initialPos.y, initialPos.z);
    this.scene.add(this.group);

    this.pulseRings = [];
    this.buildTargetPad();
    this.setPosition(initialPos.x, initialPos.y, initialPos.z);
  }

  buildTargetPad() {
    // 1. Dark base platform
    const baseGeo = new THREE.CylinderGeometry(3.2, 3.4, 0.2, 32);
    const baseMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.4,
      metalness: 0.8
    });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = 0.1;
    baseMesh.receiveShadow = true;
    this.group.add(baseMesh);

    // 2. Concentric Neon Target Rings
    const ringColors = [0x06b6d4, 0x3b82f6, 0x10b981];
    [2.8, 2.0, 1.2].forEach((radius, i) => {
      const ringGeo = new THREE.RingGeometry(radius - 0.1, radius, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: ringColors[i % ringColors.length],
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.y = 0.22 + i * 0.01;
      this.group.add(ringMesh);
      this.pulseRings.push(ringMesh);
    });

    // 3. Central Landing Bullseye "H"
    const centerGeo = new THREE.CircleGeometry(0.6, 24);
    const centerMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const centerMesh = new THREE.Mesh(centerGeo, centerMat);
    centerMesh.rotation.x = -Math.PI / 2;
    centerMesh.position.y = 0.24;
    this.group.add(centerMesh);

    // 4. Holographic Sky Beacon Cylinder
    const beaconGeo = new THREE.CylinderGeometry(0.4, 0.8, 60, 16, 1, true);
    const beaconMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.2,
      side: THREE.DoubleSide
    });
    this.skyBeacon = new THREE.Mesh(beaconGeo, beaconMat);
    this.skyBeacon.position.y = 30;
    this.group.add(this.skyBeacon);
  }

  setPosition(x, y, z) {
    this.savedPosition.set(x, y, z);
    this.group.position.set(x, y, z);
  }

  getPosition() {
    return this.savedPosition.clone();
  }

  update(delta) {
    // Pulse concentric rings
    for (let i = 0; i < this.pulseRings.length; i++) {
      this.pulseRings[i].rotation.z += delta * (i % 2 === 0 ? 0.6 : -0.6);
    }
  }

  celebrateSuccess() {
    // Visual pulse explosion effect when package is delivered
    const origScale = this.skyBeacon.scale.x;
    let t = 0;
    const interval = setInterval(() => {
      t += 0.05;
      const s = origScale * (1 + Math.sin(t * 10) * 0.4);
      this.skyBeacon.scale.set(s, 1, s);
      this.skyBeacon.material.opacity = 0.2 + Math.abs(Math.sin(t * 8)) * 0.5;
      if (t >= 3.0) {
        clearInterval(interval);
        this.skyBeacon.scale.set(1, 1, 1);
        this.skyBeacon.material.opacity = 0.2;
      }
    }, 30);
  }
}

window.DroneEntity = DroneEntity;
window.DeliveryPackage = DeliveryPackage;
window.DeliveryTarget = DeliveryTarget;
