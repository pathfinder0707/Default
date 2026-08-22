"use client";

import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { EXCHANGES } from "@/lib/data/exchanges";
import { facingRotation, landPositions, latLngToVector } from "@/lib/geo";

const ACCENT = "#efb640";
const LAND = "#b9c2d0";

/** Pairs of market centres, drawn as great-circle-ish arcs. */
const ROUTES: [string, string][] = [
  ["mumbai", "london"],
  ["london", "new-york"],
  ["tokyo", "shanghai"],
  ["shanghai", "mumbai"],
  ["new-york", "tokyo"],
];

function dotTexture(): THREE.Texture {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.45, "rgba(255,255,255,0.9)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/**
 * Two shaders do all the work.
 *
 * The body is a soft radial fall-off so the sphere reads as a lit object
 * against a near-black page rather than a hole in it; the atmosphere is the
 * classic rim glow, kept faint enough to suggest light rather than announce it.
 */
const bodyShader = {
  vertexShader: /* glsl */ `
    varying vec3 vNormal;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */ `
    uniform vec3 uCore;
    uniform vec3 uEdge;
    varying vec3 vNormal;
    void main() {
      float facing = clamp(dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 0.0, 1.0);
      gl_FragColor = vec4(mix(uEdge, uCore, pow(facing, 1.6)), 1.0);
    }
  `,
};

const atmosphereShader = {
  vertexShader: /* glsl */ `
    varying vec3 vNormal;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: /* glsl */ `
    uniform vec3 uColor;
    varying vec3 vNormal;
    void main() {
      float intensity = pow(0.58 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.6);
      gl_FragColor = vec4(uColor, 1.0) * clamp(intensity, 0.0, 1.0) * 0.5;
    }
  `,
};

function LandPoints() {
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(landPositions(1.005), 3));
    return geo;
  }, []);

  const texture = useMemo(() => dotTexture(), []);

  useEffect(() => {
    return () => {
      geometry.dispose();
      texture.dispose();
    };
  }, [geometry, texture]);

  return (
    <points geometry={geometry}>
      <pointsMaterial
        map={texture}
        color={LAND}
        // Sized for the camera distance below — attenuated points shrink fast.
        size={0.03}
        sizeAttenuation
        transparent
        opacity={0.9}
        depthWrite={false}
      />
    </points>
  );
}

function Marker({
  lat,
  lng,
  active,
  live,
  pulseOffset,
  animate,
  onHover,
}: {
  lat: number;
  lng: number;
  active: boolean;
  /** Trading right now — only open markets pulse, so the globe reads as live. */
  live: boolean;
  pulseOffset: number;
  animate: boolean;
  onHover: (hovering: boolean) => void;
}) {
  const ringRef = useRef<THREE.Mesh>(null);
  const position = useMemo(() => latLngToVector(lat, lng, 1.012), [lat, lng]);

  // Orient the ring so it lies flat against the surface.
  const quaternion = useMemo(() => {
    const dummy = new THREE.Object3D();
    dummy.position.set(...position);
    dummy.lookAt(position[0] * 2, position[1] * 2, position[2] * 2);
    return dummy.quaternion.clone();
  }, [position]);

  useFrame(({ clock }) => {
    const ring = ringRef.current;
    if (!ring) return;
    const material = ring.material as THREE.MeshBasicMaterial;

    if (!animate || !live) {
      ring.scale.setScalar(active ? 1.5 : 1.2);
      material.opacity = active ? 0.55 : 0.22;
      return;
    }

    const t = ((clock.elapsedTime + pulseOffset) % 2.8) / 2.8;
    const eased = 1 - Math.pow(1 - t, 3);
    ring.scale.setScalar(1 + eased * 2.4);
    material.opacity = (1 - t) * (active ? 0.8 : 0.45);
  });

  return (
    <group position={position} quaternion={quaternion}>
      <mesh ref={ringRef}>
        <ringGeometry args={[0.026, 0.034, 32]} />
        <meshBasicMaterial color={ACCENT} transparent side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <mesh scale={active ? 1.5 : 1}>
        <sphereGeometry args={[0.016, 16, 16]} />
        <meshBasicMaterial color={ACCENT} transparent opacity={live || active ? 1 : 0.6} />
      </mesh>
      {/* Generous invisible hit area — a 0.016 sphere is hard to point at. */}
      <mesh
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(true);
        }}
        onPointerOut={() => onHover(false)}
      >
        <sphereGeometry args={[0.05, 12, 12]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
    </group>
  );
}

function Arc({
  from,
  to,
  animate,
  offset,
}: {
  from: string;
  to: string;
  animate: boolean;
  /** Staggers the traveller so the five routes never move in lockstep. */
  offset: number;
}) {
  const travellerRef = useRef<THREE.Mesh>(null);

  const { curve, geometry, line } = useMemo(() => {
    const a = EXCHANGES.find((e) => e.id === from)!;
    const b = EXCHANGES.find((e) => e.id === to)!;
    const start = new THREE.Vector3(...latLngToVector(a.lat, a.lng, 1.01));
    const end = new THREE.Vector3(...latLngToVector(b.lat, b.lng, 1.01));
    // Lift the control point by how far apart the two cities are, so short
    // hops stay low and long hauls bow out.
    const lift = 1 + start.distanceTo(end) * 0.35;
    const mid = start.clone().add(end).multiplyScalar(0.5).normalize().multiplyScalar(lift);
    const c = new THREE.QuadraticBezierCurve3(start, mid, end);
    const geo = new THREE.BufferGeometry().setFromPoints(c.getPoints(48));
    const material = new THREE.LineBasicMaterial({
      color: ACCENT,
      transparent: true,
      opacity: 0.16,
      depthWrite: false,
    });
    return { curve: c, geometry: geo, line: new THREE.Line(geo, material) };
  }, [from, to]);

  useEffect(
    () => () => {
      geometry.dispose();
      (line.material as THREE.Material).dispose();
    },
    [geometry, line],
  );

  useFrame(({ clock }) => {
    const traveller = travellerRef.current;
    if (!traveller) return;
    if (!animate) {
      traveller.visible = false;
      return;
    }
    const t = ((clock.elapsedTime + offset) % 4) / 4;
    traveller.position.copy(curve.getPoint(t));
    const material = traveller.material as THREE.MeshBasicMaterial;
    // Fade in and out at the ends so packets do not pop.
    material.opacity = Math.sin(t * Math.PI) * 0.9;
  });

  return (
    <group>
      <primitive object={line} />
      <mesh ref={travellerRef}>
        <sphereGeometry args={[0.011, 10, 10]} />
        <meshBasicMaterial color={ACCENT} transparent depthWrite={false} />
      </mesh>
    </group>
  );
}

function Scene({
  focusId,
  openIds,
  animate,
  onHoverMarket,
}: {
  focusId: string | null;
  openIds: string[];
  animate: boolean;
  onHoverMarket: (id: string | null) => void;
}) {
  const tiltRef = useRef<THREE.Group>(null);
  const spinRef = useRef<THREE.Group>(null);
  // Start on the land-heavy face (roughly 30°E) rather than mid-Pacific.
  const spin = useRef(-2.1);
  const tilt = useRef(0.18);
  const pointer = useRef({ x: 0, y: 0 });
  const { size } = useThree();

  useEffect(() => {
    if (!animate) return;
    const onMove = (event: PointerEvent) => {
      pointer.current = {
        x: (event.clientX / size.width - 0.5) * 2,
        y: (event.clientY / size.height - 0.5) * 2,
      };
    };
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, [animate, size.width, size.height]);

  useFrame((_, delta) => {
    const step = Math.min(delta, 0.05);
    const focus = focusId ? EXCHANGES.find((e) => e.id === focusId) : null;

    if (focus) {
      const target = facingRotation(focus.lat, focus.lng);
      // Take the short way round rather than unwinding a full turn.
      let diff = (target.y - spin.current) % (Math.PI * 2);
      if (diff > Math.PI) diff -= Math.PI * 2;
      if (diff < -Math.PI) diff += Math.PI * 2;
      spin.current += diff * Math.min(1, step * 3.2);
      tilt.current += (target.x - tilt.current) * Math.min(1, step * 3.2);
    } else {
      if (animate) spin.current += step * 0.075;
      tilt.current += (0.18 - tilt.current) * Math.min(1, step * 2);
    }

    if (spinRef.current) {
      spinRef.current.rotation.y = spin.current + pointer.current.x * 0.16;
    }
    if (tiltRef.current) {
      tiltRef.current.rotation.x = tilt.current + pointer.current.y * 0.1;
    }
  });

  return (
    <group ref={tiltRef}>
      <group ref={spinRef}>
        {/* Opaque body so only the near hemisphere's dots are visible. */}
        <mesh>
          <sphereGeometry args={[1, 64, 64]} />
          <shaderMaterial
            vertexShader={bodyShader.vertexShader}
            fragmentShader={bodyShader.fragmentShader}
            uniforms={{
              uCore: { value: new THREE.Color("#20262f") },
              uEdge: { value: new THREE.Color("#0c0f14") },
            }}
          />
        </mesh>

        <LandPoints />

        {ROUTES.map(([from, to], index) => (
          <Arc
            key={`${from}-${to}`}
            from={from}
            to={to}
            animate={animate}
            offset={index * 0.8}
          />
        ))}

        {EXCHANGES.map((market, index) => (
          <Marker
            key={market.id}
            lat={market.lat}
            lng={market.lng}
            active={focusId === market.id}
            live={openIds.includes(market.id)}
            pulseOffset={index * 0.55}
            animate={animate}
            onHover={(hovering) => onHoverMarket(hovering ? market.id : null)}
          />
        ))}
      </group>

      <mesh scale={1.09}>
        <sphereGeometry args={[1, 48, 48]} />
        <shaderMaterial
          vertexShader={atmosphereShader.vertexShader}
          fragmentShader={atmosphereShader.fragmentShader}
          uniforms={{ uColor: { value: new THREE.Color(ACCENT) } }}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
          transparent
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

export default function Globe({
  focusId,
  openIds,
  animate,
  onHoverMarket,
}: {
  focusId: string | null;
  openIds: string[];
  animate: boolean;
  onHoverMarket: (id: string | null) => void;
}) {
  return (
    <Canvas
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      // Far enough back that the globe and its rim sit inside a square canvas.
      camera={{ position: [0, 0, 5.0], fov: 30 }}
      // The globe is decorative here — the city list beside it carries the
      // same information for assistive tech and keyboards.
      aria-hidden
      style={{ touchAction: "pan-y" }}
    >
      <Scene
        focusId={focusId}
        openIds={openIds}
        animate={animate}
        onHoverMarket={onHoverMarket}
      />
    </Canvas>
  );
}
