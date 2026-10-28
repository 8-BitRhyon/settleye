// Settleye third eye: a lazy Three.js brand mark beside the final CTA.
// The module does no work until the CTA card nears the viewport. The CSS
// eye already in the markup stays as the fallback for reduced motion,
// missing WebGL, and any load failure. The canvas is decorative only:
// the adjacent heading and link carry all meaning.

type ThreeModule = typeof import("three");

type EyeHandle = {
  dispose: () => void;
};

const PINE = "047857";

// Iris texture in sphere-cap UV space: u wraps around the pole, v runs
// from the pupil (top of the canvas) to the limbal edge (bottom). Radial
// striations on a real iris are vertical lines in this space. Marbling
// stays inside the brand palette: deep pine and slate with thin mint
// cracks, with no off-palette hues anywhere in the texture.
function makeIrisTexture(THREE: ThreeModule): InstanceType<ThreeModule["CanvasTexture"]> {
  const width = 512;
  const height = 256;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return new THREE.CanvasTexture(canvas);
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#5eead4");
  gradient.addColorStop(0.22, "#10b981");
  gradient.addColorStop(0.48, `#${PINE}`);
  gradient.addColorStop(0.7, "#3d5a50");
  gradient.addColorStop(0.86, "#64748b");
  gradient.addColorStop(1, "#022c22");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);
  // Marbled pine and slate clouds.
  const marble = ["#0f172a", "#1e293b", "#334155", "#64748b", "#94a3b8", "#065f46", "#022c22", "#134e4a"];
  for (let i = 0; i < 130; i += 1) {
    const x = Math.random() * width;
    const y = height * 0.15 + Math.random() * height * 0.85;
    const rx = 18 + Math.random() * 80;
    const ry = 6 + Math.random() * 26;
    ctx.save();
    ctx.globalAlpha = 0.14 + Math.random() * 0.26;
    ctx.fillStyle = marble[Math.floor(Math.random() * marble.length)];
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, Math.random() * Math.PI, 0, Math.PI * 2);
    ctx.fill();
    // Wrap the seam so the cap has no visible join.
    ctx.beginPath();
    ctx.ellipse(x - width, y, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(x + width, y, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  // Fine radial striations.
  ctx.globalAlpha = 0.14;
  for (let i = 0; i < 260; i += 1) {
    const x = Math.random() * width;
    ctx.strokeStyle = Math.random() > 0.5 ? "#ccfbf1" : "#0f172a";
    ctx.lineWidth = 1 + Math.random() * 1.6;
    ctx.beginPath();
    ctx.moveTo(x, 6);
    ctx.lineTo(x + (Math.random() - 0.5) * 8, height - 4);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  // Thin glowing mint cracks: jagged radial walks with short branches.
  ctx.save();
  ctx.strokeStyle = "rgba(110, 231, 183, 0.85)";
  ctx.shadowColor = "rgba(52, 211, 153, 0.9)";
  ctx.shadowBlur = 5;
  ctx.lineCap = "round";
  for (let i = 0; i < 60; i += 1) {
    let x = Math.random() * width;
    let y = Math.random() * height * 0.35;
    ctx.lineWidth = 1.1 + Math.random() * 1.5;
    ctx.globalAlpha = 0.55 + Math.random() * 0.45;
    ctx.beginPath();
    ctx.moveTo(x, y);
    const steps = 4 + Math.floor(Math.random() * 5);
    for (let s = 0; s < steps; s += 1) {
      x += (Math.random() - 0.5) * 22;
      y += 14 + Math.random() * 26;
      ctx.lineTo(x, y);
      if (Math.random() > 0.62) {
        ctx.moveTo(x, y);
        ctx.lineTo(x + (Math.random() - 0.5) * 30, y + 8 + Math.random() * 14);
        ctx.moveTo(x, y);
      }
    }
    ctx.stroke();
  }
  ctx.restore();
  ctx.globalAlpha = 1;
  // Pale collarette band near the pupil, dark limbal band at the rim.
  ctx.fillStyle = "rgba(190, 242, 220, 0.28)";
  ctx.fillRect(0, height * 0.4, width, 5);
  const limbal = ctx.createLinearGradient(0, height * 0.88, 0, height);
  limbal.addColorStop(0, "rgba(2, 44, 34, 0)");
  limbal.addColorStop(1, "rgba(2, 44, 34, 0.92)");
  ctx.fillStyle = limbal;
  ctx.fillRect(0, height * 0.88, width, height * 0.12);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  return texture;
}

function makeGlowTexture(THREE: ThreeModule): InstanceType<ThreeModule["CanvasTexture"]> {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return new THREE.CanvasTexture(canvas);
  const center = size / 2;
  const gradient = ctx.createRadialGradient(center, center, 4, center, center, center);
  gradient.addColorStop(0, "rgba(167, 243, 208, 0.8)");
  gradient.addColorStop(0.35, "rgba(52, 211, 153, 0.3)");
  gradient.addColorStop(0.65, "rgba(4, 120, 87, 0.12)");
  gradient.addColorStop(1, "rgba(4, 120, 87, 0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// Small 4-point star glint for the pupil centre: long vertical points,
// shorter horizontal points, white-mint core over a soft mint halo.
function makeStarTexture(THREE: ThreeModule): InstanceType<ThreeModule["CanvasTexture"]> {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return new THREE.CanvasTexture(canvas);
  const c = size / 2;
  const halo = ctx.createRadialGradient(c, c, 2, c, c, c * 0.55);
  halo.addColorStop(0, "rgba(236, 253, 245, 0.95)");
  halo.addColorStop(0.35, "rgba(110, 231, 183, 0.45)");
  halo.addColorStop(1, "rgba(4, 120, 87, 0)");
  ctx.fillStyle = halo;
  ctx.fillRect(0, 0, size, size);
  const star = (long: number, short: number, waist: number) => {
    ctx.beginPath();
    ctx.moveTo(c, c - long);
    ctx.quadraticCurveTo(c + waist, c - waist, c + short, c);
    ctx.quadraticCurveTo(c + waist, c + waist, c, c + long);
    ctx.quadraticCurveTo(c - waist, c + waist, c - short, c);
    ctx.quadraticCurveTo(c - waist, c - waist, c, c - long);
    ctx.closePath();
  };
  ctx.save();
  ctx.shadowColor = "rgba(167, 243, 208, 0.95)";
  ctx.shadowBlur = 18;
  ctx.fillStyle = "rgba(255, 255, 255, 0.98)";
  star(size * 0.47, size * 0.2, size * 0.028);
  ctx.fill();
  ctx.restore();
  ctx.fillStyle = "rgba(236, 253, 245, 1)";
  star(size * 0.35, size * 0.14, size * 0.02);
  ctx.fill();
  const core = ctx.createRadialGradient(c, c, 0, c, c, size * 0.09);
  core.addColorStop(0, "rgba(255, 255, 255, 1)");
  core.addColorStop(1, "rgba(167, 243, 208, 0)");
  ctx.fillStyle = core;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createEye(THREE: ThreeModule, host: HTMLElement): EyeHandle | null {
  const canvas = document.createElement("canvas");
  canvas.className = "third-eye__canvas";
  canvas.setAttribute("aria-hidden", "true");
  host.appendChild(canvas);

  let renderer: InstanceType<ThreeModule["WebGLRenderer"]>;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "low-power",
    });
    if (!renderer.getContext()) throw new Error("WebGL context unavailable");
  } catch {
    canvas.remove();
    return null;
  }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100);
  camera.position.set(0, 0, 4.35);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x131316, 0.95));
  const key = new THREE.DirectionalLight(0xffffff, 2.1);
  key.position.set(2.5, 3, 4);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x6ee7b7, 0.85);
  rim.position.set(-3, -0.5, 2.5);
  scene.add(rim);

  // Faint mint halo behind the eye.
  const glowMaterial = new THREE.SpriteMaterial({
    map: makeGlowTexture(THREE),
    transparent: true,
    opacity: 0.45,
    depthWrite: false,
  });
  const glow = new THREE.Sprite(glowMaterial);
  glow.scale.set(2.8, 2.8, 1);
  glow.position.z = -0.7;
  scene.add(glow);

  const eyeGroup = new THREE.Group();
  scene.add(eyeGroup);
  const blinkGroup = new THREE.Group();
  eyeGroup.add(blinkGroup);

  const eyeball = new THREE.Mesh(
    new THREE.SphereGeometry(1, 48, 32),
    new THREE.MeshPhysicalMaterial({
      color: 0xf8f4e8,
      roughness: 0.22,
      metalness: 0,
      clearcoat: 1,
      clearcoatRoughness: 0.28,
    }),
  );
  blinkGroup.add(eyeball);

  // Iris, pupil, and highlights ride in a look group so the gaze can
  // drift a few millimetres ahead of the eyeball rotation.
  const lookGroup = new THREE.Group();
  blinkGroup.add(lookGroup);

  // Iris and pupil are spherical caps hugging the eyeball, so the gaze
  // stays printed on the ball at every parallax angle.
  const irisGeometry = new THREE.SphereGeometry(1.015, 64, 32, 0, Math.PI * 2, 0, 0.6);
  irisGeometry.rotateX(Math.PI / 2);
  const iris = new THREE.Mesh(
    irisGeometry,
    new THREE.MeshStandardMaterial({
      map: makeIrisTexture(THREE),
      roughness: 0.32,
      metalness: 0,
    }),
  );
  lookGroup.add(iris);

  // Luminous mint core in place of a black pupil: pine emissive keeps
  // the glow in the #047857 family at every parallax angle.
  const pupilGeometry = new THREE.SphereGeometry(1.019, 48, 16, 0, Math.PI * 2, 0, 0.265);
  pupilGeometry.rotateX(Math.PI / 2);
  const pupil = new THREE.Mesh(
    pupilGeometry,
    new THREE.MeshStandardMaterial({
      color: 0x6ee7b7,
      emissive: 0x047857,
      emissiveIntensity: 1.5,
      roughness: 0.3,
    }),
  );
  lookGroup.add(pupil);

  // 4-point star glint sprite pinned to the core centre.
  const starMaterial = new THREE.SpriteMaterial({
    map: makeStarTexture(THREE),
    transparent: true,
    opacity: 0.95,
    depthWrite: false,
  });
  const star = new THREE.Sprite(starMaterial);
  star.scale.set(0.66, 0.66, 1);
  star.position.set(0, 0, 1.045);
  lookGroup.add(star);

  const placeHighlight = (x: number, y: number, radius: number, opacity: number) => {
    const mesh = new THREE.Mesh(
      new THREE.CircleGeometry(radius, 24),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity }),
    );
    const pos = new THREE.Vector3(x, y, 1).normalize().multiplyScalar(1.026);
    mesh.position.copy(pos);
    mesh.lookAt(pos.clone().multiplyScalar(2));
    lookGroup.add(mesh);
  };
  placeHighlight(-0.16, 0.17, 0.045, 0.75);
  placeHighlight(0.12, -0.12, 0.022, 0.4);

  // Lids: dark spherical caps concentric with the eyeball. Rotating a
  // cap around the eyeball centre slides it over the surface, so a
  // blink never clips through the ball.
  // Bold near-black upper lid: parked a touch lower than a full open
  // lid so its edge reads as a dark lash line across the top.
  const LID_TOP_OPEN = -1.05;
  const lidMaterial = new THREE.MeshStandardMaterial({
    color: 0x08080a,
    roughness: 0.42,
    metalness: 0.05,
    side: THREE.DoubleSide,
  });
  const lidTopPivot = new THREE.Group();
  const lidTop = new THREE.Mesh(
    new THREE.SphereGeometry(1.045, 48, 24, 0, Math.PI * 2, 0, Math.PI * 0.5),
    lidMaterial,
  );
  lidTopPivot.add(lidTop);
  lidTopPivot.rotation.x = LID_TOP_OPEN;
  blinkGroup.add(lidTopPivot);

  const lidBottomPivot = new THREE.Group();
  const lidBottom = new THREE.Mesh(
    new THREE.SphereGeometry(1.045, 48, 24, 0, Math.PI * 2, Math.PI * 0.5, Math.PI * 0.5),
    lidMaterial,
  );
  lidBottomPivot.add(lidBottom);
  lidBottomPivot.rotation.x = 1.25;
  blinkGroup.add(lidBottomPivot);

  // Bold upper lash line: a near-black tube arc sampled on the ball
  // surface across the top of the iris, so it hugs the sphere at every
  // parallax angle instead of sinking into it like a flat torus would.
  // It lives in the blink group (not the look group) so the gaze can
  // drift under a steady lid line, and the blink caps cover it on close.
  const lashPoints: InstanceType<ThreeModule["Vector3"]>[] = [];
  for (let i = 0; i <= 16; i += 1) {
    const t = (i / 16) * 2 - 1;
    const x = 0.78 * t;
    const y = 0.58 - 0.28 * t * t;
    const z = Math.sqrt(Math.max(1.005 * 1.005 - x * x - y * y, 0.01));
    lashPoints.push(new THREE.Vector3(x, y, z));
  }
  const lashCurve = new THREE.CatmullRomCurve3(lashPoints);
  const lash = new THREE.Mesh(
    new THREE.TubeGeometry(lashCurve, 32, 0.055, 10, false),
    new THREE.MeshBasicMaterial({ color: 0x050506 }),
  );
  lash.renderOrder = 3;
  blinkGroup.add(lash);

  const finePointer = window.matchMedia("(pointer: fine)");
  let targetRotX = 0;
  let targetRotY = 0;
  let lookX = 0;
  let lookY = 0;
  let gazeX = 0;
  let gazeY = 0;

  const onPointerMove = (event: PointerEvent) => {
    const nx = (event.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2;
    const ny = (event.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2;
    targetRotY = nx * 0.22;
    targetRotX = ny * 0.13;
    lookX = nx * 0.02;
    lookY = -ny * 0.016;
  };
  if (finePointer.matches) {
    window.addEventListener("pointermove", onPointerMove, { passive: true });
  }

  const resize = () => {
    const width = host.clientWidth || 144;
    const height = host.clientHeight || width;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  resize();
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);

  const clock = new THREE.Clock();
  let raf = 0;
  let nextBlinkAt = 5 + Math.random() * 2;
  let blinkStart = -1;
  const BLINK_SECONDS = 0.3;

  const tick = () => {
    raf = requestAnimationFrame(tick);
    const t = clock.getElapsedTime();

    if (blinkStart < 0 && t >= nextBlinkAt) {
      blinkStart = t;
      nextBlinkAt = t + 5 + Math.random() * 2;
    }
    let blink = 0;
    if (blinkStart >= 0) {
      const progress = (t - blinkStart) / BLINK_SECONDS;
      if (progress >= 1) {
        blinkStart = -1;
      } else {
        blink = Math.sin(progress * Math.PI);
      }
    }
    lidTopPivot.rotation.x = LID_TOP_OPEN + blink * 2.63;
    lidBottomPivot.rotation.x = 1.25 - blink * 2.05;
    blinkGroup.scale.y = 1 - blink * 0.05;

    // Idle float and a slow watchful sway.
    eyeGroup.position.y = Math.sin(t * 0.7) * 0.045;
    eyeGroup.position.x = Math.sin(t * 0.45) * 0.02;
    gazeX += (targetRotX - gazeX) * 0.055;
    gazeY += (targetRotY - gazeY) * 0.055;
    eyeGroup.rotation.x = gazeX;
    eyeGroup.rotation.y = gazeY + Math.sin(t * 0.3) * 0.04;
    eyeGroup.rotation.z = Math.sin(t * 0.4) * 0.018;
    lookGroup.position.x += (lookX - lookGroup.position.x) * 0.08;
    lookGroup.position.y += (lookY - lookGroup.position.y) * 0.08;
    glowMaterial.opacity = 0.4 + Math.sin(t * 0.9) * 0.08;
    const starPulse = 0.66 + Math.sin(t * 1.6) * 0.025;
    star.scale.set(starPulse, starPulse, 1);
    starMaterial.opacity = 0.9 + Math.sin(t * 1.6) * 0.08;

    renderer.render(scene, camera);
  };
  tick();

  return {
    dispose: () => {
      cancelAnimationFrame(raf);
      resizeObserver.disconnect();
      window.removeEventListener("pointermove", onPointerMove);
      scene.traverse((obj) => {
        const node = obj as {
          geometry?: { dispose: () => void };
          material?: { map?: { dispose: () => void }; dispose: () => void } | Array<{ map?: { dispose: () => void }; dispose: () => void }>;
        };
        node.geometry?.dispose();
        const materials = Array.isArray(node.material) ? node.material : node.material ? [node.material] : [];
        for (const material of materials) {
          material.map?.dispose();
          material.dispose();
        }
      });
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}

const host = document.querySelector<HTMLElement>(".cta-card .third-eye");
const card = document.querySelector<HTMLElement>(".cta-card");

if (host && card) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let active: EyeHandle | null = null;
  let starting = false;
  let generation = 0;

  const stopEye = () => {
    generation += 1;
    active?.dispose();
    active = null;
    delete host.dataset.eye;
  };

  const startEye = async () => {
    if (active || starting || reducedMotion.matches) return;
    starting = true;
    const gen = generation;
    try {
      const THREE = await import("three");
      if (gen !== generation || reducedMotion.matches || active) return;
      active = createEye(THREE, host);
      if (active) {
        host.dataset.eye = "webgl";
      } else {
        host.dataset.eye = "fallback";
      }
    } catch {
      if (gen === generation) host.dataset.eye = "fallback";
    } finally {
      starting = false;
    }
  };

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          void startEye();
        } else {
          stopEye();
        }
      }
    },
    { threshold: 0.2 },
  );
  observer.observe(card);

  reducedMotion.addEventListener("change", (event) => {
    if (event.matches) stopEye();
  });
  window.addEventListener("pagehide", () => {
    observer.disconnect();
    stopEye();
  });
}
