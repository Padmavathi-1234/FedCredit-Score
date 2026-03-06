/**
 * Three.js — Animated Particle Network Background
 * Subtle, performant particle system with connection lines.
 */

(function () {
  'use strict';

  const PARTICLE_COUNT = 120;
  const CONNECTION_DISTANCE = 150;
  const PARTICLE_SIZE = 2;

  let scene, camera, renderer;
  let particles, positions, velocities;
  let lines, linePositions;
  let animationId;
  let mouseX = 0, mouseY = 0;

  function init() {
    const canvas = document.getElementById('three-canvas');
    if (!canvas) return;

    // Scene
    scene = new THREE.Scene();

    // Camera
    camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      1,
      1000
    );
    camera.position.z = 400;

    // Renderer
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // Create particles
    const geometry = new THREE.BufferGeometry();
    positions = new Float32Array(PARTICLE_COUNT * 3);
    velocities = new Float32Array(PARTICLE_COUNT * 3);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 600;
      positions[i3 + 1] = (Math.random() - 0.5) * 600;
      positions[i3 + 2] = (Math.random() - 0.5) * 300;

      velocities[i3] = (Math.random() - 0.5) * 0.3;
      velocities[i3 + 1] = (Math.random() - 0.5) * 0.3;
      velocities[i3 + 2] = (Math.random() - 0.5) * 0.1;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: PARTICLE_SIZE,
      color: 0x6366f1,
      transparent: true,
      opacity: 0.6,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
    });

    particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Connection lines
    const lineGeom = new THREE.BufferGeometry();
    const maxLines = PARTICLE_COUNT * PARTICLE_COUNT;
    linePositions = new Float32Array(maxLines * 6);
    lineGeom.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    lineGeom.setDrawRange(0, 0);

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.08,
      blending: THREE.AdditiveBlending,
    });

    lines = new THREE.LineSegments(lineGeom, lineMat);
    scene.add(lines);

    // Events
    window.addEventListener('resize', onResize);
    document.addEventListener('mousemove', onMouseMove);

    animate();
  }

  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function onMouseMove(e) {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 40;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 40;
  }

  function animate() {
    animationId = requestAnimationFrame(animate);

    // Update particle positions
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const i3 = i * 3;
      positions[i3] += velocities[i3];
      positions[i3 + 1] += velocities[i3 + 1];
      positions[i3 + 2] += velocities[i3 + 2];

      // Boundary wrap
      if (positions[i3] > 300) positions[i3] = -300;
      if (positions[i3] < -300) positions[i3] = 300;
      if (positions[i3 + 1] > 300) positions[i3 + 1] = -300;
      if (positions[i3 + 1] < -300) positions[i3 + 1] = 300;
      if (positions[i3 + 2] > 150) positions[i3 + 2] = -150;
      if (positions[i3 + 2] < -150) positions[i3 + 2] = 150;
    }

    particles.geometry.attributes.position.needsUpdate = true;

    // Update connection lines
    let lineIdx = 0;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      for (let j = i + 1; j < PARTICLE_COUNT; j++) {
        const i3 = i * 3, j3 = j * 3;
        const dx = positions[i3] - positions[j3];
        const dy = positions[i3 + 1] - positions[j3 + 1];
        const dz = positions[i3 + 2] - positions[j3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist < CONNECTION_DISTANCE) {
          linePositions[lineIdx++] = positions[i3];
          linePositions[lineIdx++] = positions[i3 + 1];
          linePositions[lineIdx++] = positions[i3 + 2];
          linePositions[lineIdx++] = positions[j3];
          linePositions[lineIdx++] = positions[j3 + 1];
          linePositions[lineIdx++] = positions[j3 + 2];
        }
      }
    }

    lines.geometry.setDrawRange(0, lineIdx / 3);
    lines.geometry.attributes.position.needsUpdate = true;

    // Subtle camera follow mouse
    camera.position.x += (mouseX - camera.position.x) * 0.02;
    camera.position.y += (-mouseY - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
