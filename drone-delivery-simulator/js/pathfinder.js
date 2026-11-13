/**
 * 3D A* Pathfinding Engine with Line-of-Sight String-Pulling & Spline Smoothing
 * Handles obstacle clearance buffers, dynamic climb vs detour energy trade-offs, and flight profiles.
 */

class PriorityQueue {
  constructor() {
    this.heap = [];
  }
  push(item, priority) {
    this.heap.push({ item, priority });
    this._bubbleUp(this.heap.length - 1);
  }
  pop() {
    if (this.heap.length === 0) return null;
    const top = this.heap[0];
    const bottom = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = bottom;
      this._sinkDown(0);
    }
    return top.item;
  }
  isEmpty() {
    return this.heap.length === 0;
  }
  _bubbleUp(idx) {
    while (idx > 0) {
      const parentIdx = (idx - 1) >> 1;
      if (this.heap[idx].priority < this.heap[parentIdx].priority) {
        const tmp = this.heap[idx];
        this.heap[idx] = this.heap[parentIdx];
        this.heap[parentIdx] = tmp;
        idx = parentIdx;
      } else break;
    }
  }
  _sinkDown(idx) {
    const len = this.heap.length;
    while (true) {
      let left = (idx << 1) + 1;
      let right = left + 1;
      let smallest = idx;
      if (left < len && this.heap[left].priority < this.heap[smallest].priority) {
        smallest = left;
      }
      if (right < len && this.heap[right].priority < this.heap[smallest].priority) {
        smallest = right;
      }
      if (smallest !== idx) {
        const tmp = this.heap[idx];
        this.heap[idx] = this.heap[smallest];
        this.heap[smallest] = tmp;
        idx = smallest;
      } else break;
    }
  }
}

class DronePathfinder {
  constructor() {
    // Spatial grid parameters
    this.worldSize = 160; // -80 to +80
    this.cellSize = 3.0;  // 3m resolution
    this.gridDim = Math.round(this.worldSize / this.cellSize); // ~54 cells
    this.minCoord = -this.worldSize / 2;
    
    // Altitude discretization
    this.baseCruiseAltitude = 16;
    this.minAltitude = 4;
    this.maxAltitude = 110;
    this.altStep = 6;
    this.numAltSteps = Math.ceil((this.maxAltitude - this.minAltitude) / this.altStep) + 1;
    
    // Safety buffer around obstacles
    this.horizontalBuffer = 2.8;
    this.verticalBuffer = 3.2;

    // Path modes: 'balanced' (default), 'direct', 'canyon', 'flyover'
    this.mode = 'balanced';
  }

  setMode(newMode) {
    this.mode = newMode;
  }

  // Convert world (x, z) to grid cell index (gx, gz)
  worldToGrid(x, z) {
    const gx = Math.floor((x - this.minCoord) / this.cellSize);
    const gz = Math.floor((z - this.minCoord) / this.cellSize);
    return {
      gx: Math.max(0, Math.min(this.gridDim - 1, gx)),
      gz: Math.max(0, Math.min(this.gridDim - 1, gz))
    };
  }

  gridToWorld(gx, gz) {
    return {
      x: this.minCoord + (gx + 0.5) * this.cellSize,
      z: this.minCoord + (gz + 0.5) * this.cellSize
    };
  }

  // Altitude to index and back
  altToStep(y) {
    const step = Math.round((y - this.minAltitude) / this.altStep);
    return Math.max(0, Math.min(this.numAltSteps - 1, step));
  }

  stepToAlt(step) {
    return this.minAltitude + step * this.altStep;
  }

  nodeKey(gx, gz, ay) {
    return `${gx},${gz},${ay}`;
  }

  // Build a 2D heightmap of obstacle elevations across the city
  buildObstacleHeightmap(buildings) {
    const heightmap = new Float32Array(this.gridDim * this.gridDim);
    
    // For each cell, record the maximum building height + buffer
    for (const b of buildings) {
      const minX = b.x - b.width / 2 - this.horizontalBuffer;
      const maxX = b.x + b.width / 2 + this.horizontalBuffer;
      const minZ = b.z - b.depth / 2 - this.horizontalBuffer;
      const maxZ = b.z + b.depth / 2 + this.horizontalBuffer;
      const maxH = b.height + this.verticalBuffer;

      const gStart = this.worldToGrid(minX, minZ);
      const gEnd = this.worldToGrid(maxX, maxZ);

      for (let gz = gStart.gz; gz <= gEnd.gz; gz++) {
        for (let gx = gStart.gx; gx <= gEnd.gx; gx++) {
          const idx = gz * this.gridDim + gx;
          if (maxH > heightmap[idx]) {
            heightmap[idx] = maxH;
          }
        }
      }
    }
    return heightmap;
  }

  // 3D Ray-Box intersection to check if a straight line segment collides with any building
  isSegmentClear(p1, p2, buildings) {
    const dir = { x: p2.x - p1.x, y: p2.y - p1.y, z: p2.z - p1.z };
    const dist = Math.sqrt(dir.x * dir.x + dir.y * dir.y + dir.z * dir.z);
    if (dist < 0.001) return true;

    const invDir = {
      x: dir.x !== 0 ? 1.0 / dir.x : 1e12,
      y: dir.y !== 0 ? 1.0 / dir.y : 1e12,
      z: dir.z !== 0 ? 1.0 / dir.z : 1e12
    };

    for (let i = 0; i < buildings.length; i++) {
      const b = buildings[i];
      const boxMinX = b.x - b.width / 2 - this.horizontalBuffer;
      const boxMaxX = b.x + b.width / 2 + this.horizontalBuffer;
      const boxMinY = 0;
      const boxMaxY = b.height + this.verticalBuffer;
      const boxMinZ = b.z - b.depth / 2 - this.horizontalBuffer;
      const boxMaxZ = b.z + b.depth / 2 + this.horizontalBuffer;

      // Check slab intersections
      const t1 = (boxMinX - p1.x) * invDir.x;
      const t2 = (boxMaxX - p1.x) * invDir.x;
      const t3 = (boxMinY - p1.y) * invDir.y;
      const t4 = (boxMaxY - p1.y) * invDir.y;
      const t5 = (boxMinZ - p1.z) * invDir.z;
      const t6 = (boxMaxZ - p1.z) * invDir.z;

      const tmin = Math.max(Math.max(Math.min(t1, t2), Math.min(t3, t4)), Math.min(t5, t6));
      const tmax = Math.min(Math.min(Math.max(t1, t2), Math.max(t3, t4)), Math.max(t5, t6));

      // If tmax < 0, ray is intersecting AABB, but whole AABB is behind us
      // If tmin > tmax, ray doesn't intersect AABB
      if (tmax >= 0 && tmin <= tmax && tmin <= 1.0 && tmax >= 0.0) {
        return false; // Collision detected!
      }
    }
    return true; // No collision along segment
  }

  // Solve for the optimal 3D path using 3D A*
  findPath(startPos, targetPos, buildings) {
    const t0 = performance.now();
    const heightmap = this.buildObstacleHeightmap(buildings);

    // Initial takeoff waypoint above start package
    const startTakeoffY = Math.max(this.baseCruiseAltitude, this.getHeightAt(startPos.x, startPos.z, heightmap) + 2);
    // Final descent waypoint above target dropzone
    const targetDescentY = Math.max(this.baseCruiseAltitude, this.getHeightAt(targetPos.x, targetPos.z, heightmap) + 2);

    const startGrid = this.worldToGrid(startPos.x, startPos.z);
    const targetGrid = this.worldToGrid(targetPos.x, targetPos.z);

    const startAltStep = this.altToStep(startTakeoffY);
    const targetAltStep = this.altToStep(targetDescentY);

    // Cost multipliers based on flight mode
    let climbWeight = 2.0;
    let descentWeight = 1.0;
    if (this.mode === 'canyon') {
      climbWeight = 8.0; // High penalty for climbing; prefers weaving through streets
    } else if (this.mode === 'flyover') {
      climbWeight = 0.5; // Encourages immediate climb to skyway altitude
    } else if (this.mode === 'direct') {
      climbWeight = 1.0;
    }

    const pq = new PriorityQueue();
    const gScore = new Map();
    const cameFrom = new Map();

    const startKey = this.nodeKey(startGrid.gx, startGrid.gz, startAltStep);
    gScore.set(startKey, 0);

    const startH = this.heuristic3D(startGrid.gx, startGrid.gz, startAltStep, targetGrid.gx, targetGrid.gz, targetAltStep, climbWeight);
    pq.push({ gx: startGrid.gx, gz: startGrid.gz, ay: startAltStep }, startH);

    let goalNode = null;
    let iterations = 0;
    const maxIterations = 14000;

    // 10 neighbor directions: 8 horizontal, plus climb/descend transitions
    const neighborDeltas = [
      { dx: 1, dz: 0, dy: 0 },
      { dx: -1, dz: 0, dy: 0 },
      { dx: 0, dz: 1, dy: 0 },
      { dx: 0, dz: -1, dy: 0 },
      { dx: 1, dz: 1, dy: 0 },
      { dx: -1, dz: 1, dy: 0 },
      { dx: 1, dz: -1, dy: 0 },
      { dx: -1, dz: -1, dy: 0 },
      // Climb & descend actions
      { dx: 0, dz: 0, dy: 1 },
      { dx: 0, dz: 0, dy: -1 },
      { dx: 1, dz: 0, dy: 1 },
      { dx: -1, dz: 0, dy: 1 },
      { dx: 0, dz: 1, dy: 1 },
      { dx: 0, dz: -1, dy: 1 },
      { dx: 1, dz: 0, dy: -1 },
      { dx: -1, dz: 0, dy: -1 },
      { dx: 0, dz: 1, dy: -1 },
      { dx: 0, dz: -1, dy: -1 }
    ];

    while (!pq.isEmpty() && iterations++ < maxIterations) {
      const current = pq.pop();
      const currKey = this.nodeKey(current.gx, current.gz, current.ay);
      const currentG = gScore.get(currKey);

      // Check if reached destination
      if (current.gx === targetGrid.gx && current.gz === targetGrid.gz && Math.abs(current.ay - targetAltStep) <= 1) {
        goalNode = current;
        break;
      }

      const currWorld = this.gridToWorld(current.gx, current.gz);
      const currY = this.stepToAlt(current.ay);

      for (const d of neighborDeltas) {
        const ngx = current.gx + d.dx;
        const ngz = current.gz + d.dz;
        const nay = current.ay + d.dy;

        if (ngx < 0 || ngx >= this.gridDim || ngz < 0 || ngz >= this.gridDim || nay < 0 || nay >= this.numAltSteps) {
          continue;
        }

        const nextY = this.stepToAlt(nay);
        const obstacleH = heightmap[ngz * this.gridDim + ngx];

        // Collision check: Drone altitude must clear the obstacle height at the new cell
        if (nextY < obstacleH) {
          continue;
        }

        // Distance & climb cost computation
        const distXZ = Math.sqrt(d.dx * d.dx + d.dz * d.dz) * this.cellSize;
        const distY = (nextY - currY);
        let moveCost = Math.sqrt(distXZ * distXZ + distY * distY);

        if (distY > 0) {
          moveCost += distY * climbWeight;
        } else if (distY < 0) {
          moveCost += Math.abs(distY) * descentWeight;
        }

        // Proximity penalty to encourage open airspace rather than brushing walls
        const clearance = nextY - obstacleH;
        if (clearance < 4.0 && obstacleH > 0) {
          moveCost += (4.0 - clearance) * 2.5;
        }

        const tentativeG = currentG + moveCost;
        const nextKey = this.nodeKey(ngx, ngz, nay);

        if (!gScore.has(nextKey) || tentativeG < gScore.get(nextKey)) {
          gScore.set(nextKey, tentativeG);
          cameFrom.set(nextKey, current);
          const h = this.heuristic3D(ngx, ngz, nay, targetGrid.gx, targetGrid.gz, targetAltStep, climbWeight);
          pq.push({ gx: ngx, gz: ngz, ay: nay }, tentativeG + h);
        }
      }
    }

    // Reconstruct raw waypoints from A*
    let rawPath = [];
    if (goalNode) {
      let curr = goalNode;
      while (curr) {
        const w = this.gridToWorld(curr.gx, curr.gz);
        const y = this.stepToAlt(curr.ay);
        rawPath.unshift(new THREE.Vector3(w.x, y, w.z));
        const key = this.nodeKey(curr.gx, curr.gz, curr.ay);
        curr = cameFrom.get(key);
      }
    } else {
      // Fallback: safe overhead flyover if labyrinth or path blocked
      console.warn("A* found no path, generating overhead flyover fallback");
      const highestBuilding = buildings.reduce((max, b) => Math.max(max, b.height), 20);
      const safeCeiling = highestBuilding + 15;
      rawPath = [
        new THREE.Vector3(startPos.x, startTakeoffY, startPos.z),
        new THREE.Vector3(startPos.x, safeCeiling, startPos.z),
        new THREE.Vector3(targetPos.x, safeCeiling, targetPos.z),
        new THREE.Vector3(targetPos.x, targetDescentY, targetPos.z)
      ];
    }

    // Ensure start takeoff and final target descent are explicitly pinned
    if (rawPath.length > 0) {
      rawPath[0].set(startPos.x, startTakeoffY, startPos.z);
      rawPath[rawPath.length - 1].set(targetPos.x, targetDescentY, targetPos.z);
    }

    // Line-of-sight shortcutting / string-pulling
    const cruiseWaypoints = this.prunePath(rawPath, buildings);

    // If cruiseWaypoints has only 2 points (straight line), add a midpoint to ensure smooth curve handling
    let splinePoints = [...cruiseWaypoints];
    if (splinePoints.length === 2) {
      const mid = new THREE.Vector3().addVectors(splinePoints[0], splinePoints[1]).multiplyScalar(0.5);
      splinePoints = [splinePoints[0], mid, splinePoints[1]];
    }

    // Build smooth Catmull-Rom spline for cruise flight
    const spline = new THREE.CatmullRomCurve3(splinePoints, false, 'centripetal', 0.4);

    // Compute metrics
    const totalDistance = this.calculateSplineLength(spline) + startTakeoffY + targetDescentY;
    const avgSpeed = 15; // m/s (~54 km/h)
    const estimatedTime = (totalDistance / avgSpeed).toFixed(1);
    const estimatedEnergy = (totalDistance * 0.45 + (startTakeoffY * 1.8)).toFixed(1);

    const calcTime = (performance.now() - t0).toFixed(1);

    return {
      waypoints: cruiseWaypoints,
      cruiseWaypoints: cruiseWaypoints,
      startTakeoffY: startTakeoffY,
      targetDescentY: targetDescentY,
      spline: spline,
      metrics: {
        distance: totalDistance.toFixed(1),
        etaSeconds: estimatedTime,
        energyWh: estimatedEnergy,
        calculationMs: calcTime,
        waypointCount: cruiseWaypoints.length
      }
    };
  }

  // Line-of-sight raycast shortcutting (String Pulling)
  prunePath(path, buildings) {
    if (path.length <= 2) return path;

    const pruned = [path[0]];
    let currentIdx = 0;

    while (currentIdx < path.length - 1) {
      let furthestClear = currentIdx + 1;
      // Look ahead as far as possible
      for (let next = path.length - 1; next > currentIdx; next--) {
        if (this.isSegmentClear(path[currentIdx], path[next], buildings)) {
          furthestClear = next;
          break;
        }
      }
      pruned.push(path[furthestClear]);
      currentIdx = furthestClear;
    }

    return pruned;
  }

  calculateSplineLength(spline, samples = 100) {
    let length = 0;
    let prev = spline.getPoint(0);
    for (let i = 1; i <= samples; i++) {
      const curr = spline.getPoint(i / samples);
      length += prev.distanceTo(curr);
      prev = curr;
    }
    return length;
  }

  heuristic3D(gx, gz, ay, tx, tz, tay, climbWeight) {
    const dx = (tx - gx) * this.cellSize;
    const dz = (tz - gz) * this.cellSize;
    const dy = (tay - ay) * this.altStep;
    const baseDist = Math.sqrt(dx * dx + dz * dz + dy * dy);
    return dy > 0 ? baseDist + dy * (climbWeight - 1.0) : baseDist;
  }

  getHeightAt(x, z, heightmap) {
    const g = this.worldToGrid(x, z);
    return heightmap[g.gz * this.gridDim + g.gx] || 0;
  }
}

window.DronePathfinder = DronePathfinder;
