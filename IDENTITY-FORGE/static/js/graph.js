document.addEventListener("DOMContentLoaded", function () {
  const host = document.getElementById("identity-network");
  const source = document.getElementById("graph-data");
  if (!host || !source || typeof THREE === "undefined") {
    return;
  }

  let payload;
  try {
    payload = JSON.parse(source.textContent);
  } catch (error) {
    return;
  }

  const width = host.clientWidth || 800;
  const height = host.clientHeight || 420;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(58, width / height, 0.1, 1000);
  camera.position.z = 6.2;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height);
  renderer.domElement.className = "graph-canvas";
  host.appendChild(renderer.domElement);

  const group = new THREE.Group();
  scene.add(group);

  const colors = {
    user: 0xd4af37,
    role: 0x6ea8fe,
    team: 0xcbd5e1,
    resource: 0xff6b6b,
    permission: 0x4fd1a5
  };

  const nodePositions = {};
  payload.nodes.forEach(function (node) {
    nodePositions[node.id] = [node.x, node.y, node.z];
    const geometry = new THREE.SphereGeometry(node.risk_score >= 8 ? 0.1 : 0.065, 18, 18);
    const material = new THREE.MeshStandardMaterial({
      color: colors[node.kind] || 0xffffff,
      emissive: colors[node.kind] || 0xffffff,
      emissiveIntensity: node.risk_score >= 8 ? 0.65 : 0.2,
      roughness: 0.25,
      metalness: 0.7
    });
    const sphere = new THREE.Mesh(geometry, material);
    sphere.position.set(node.x, node.y, node.z);
    sphere.userData = node;
    group.add(sphere);
  });

  const linePositions = [];
  const lineColors = [];
  payload.links.forEach(function (link) {
    const from = nodePositions[link.source];
    const to = nodePositions[link.target];
    if (!from || !to) {
      return;
    }
    linePositions.push(from[0], from[1], from[2], to[0], to[1], to[2]);
    const color = new THREE.Color(link.risky ? 0xff6b6b : 0x52627c);
    lineColors.push(color.r, color.g, color.b, color.r, color.g, color.b);
  });

  if (linePositions.length) {
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    lineGeometry.setAttribute("color", new THREE.Float32BufferAttribute(lineColors, 3));
    const lineMaterial = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.55 });
    group.add(new THREE.LineSegments(lineGeometry, lineMaterial));
  }

  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const light = new THREE.PointLight(0xd4af37, 1.8, 30);
  light.position.set(3, 4, 6);
  scene.add(light);

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const tooltip = document.getElementById("graph-tooltip");

  host.addEventListener("pointermove", function (event) {
    const bounds = host.getBoundingClientRect();
    pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(group.children.filter(function (child) {
      return child.userData && child.userData.id;
    }));
    if (!tooltip) {
      return;
    }
    if (hits.length) {
      const data = hits[0].object.userData;
      tooltip.textContent = data.label + " · " + data.kind + " · risk " + data.risk_score;
      tooltip.style.opacity = "1";
    } else {
      tooltip.style.opacity = "0";
    }
  });

  let autoRotate = true;
  host.addEventListener("pointerdown", function () {
    autoRotate = false;
  });

  if (typeof gsap !== "undefined" && payload.nodes.length) {
    gsap.to(group.rotation, { y: Math.PI * 2, duration: 90, repeat: -1, ease: "none" });
  }

  function animate() {
    requestAnimationFrame(animate);
    if (autoRotate) {
      group.rotation.x += 0.0006;
    }
    renderer.render(scene, camera);
  }

  animate();

  window.addEventListener("resize", function () {
    const nextWidth = host.clientWidth || 800;
    const nextHeight = host.clientHeight || 420;
    camera.aspect = nextWidth / nextHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(nextWidth, nextHeight);
  });
});
