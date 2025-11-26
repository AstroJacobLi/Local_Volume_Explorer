import { useMemo, useRef, useLayoutEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text } from '@react-three/drei';
import * as THREE from 'three';

const BlinkingMarker = ({ position }) => {
    const materialRef = useRef();
    
    useFrame(({ clock }) => {
        if (materialRef.current) {
            // Blink logic: 0.3 to 1.0 opacity
            const t = clock.getElapsedTime();
            const opacity = 0.65 + 0.35 * Math.sin(t * 8.0);
            materialRef.current.opacity = opacity;
        }
    });

    // Create a texture for the marker (same soft circle)
    const texture = useMemo(() => {
        const canvas = document.createElement('canvas');
        canvas.width = 32; canvas.height = 32;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createRadialGradient(16,16,0,16,16,16);
        grad.addColorStop(0, 'rgba(255,255,255,1)');
        grad.addColorStop(0.2, 'rgba(255,255,255,0.8)');
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0,0,32,32);
        return new THREE.CanvasTexture(canvas);
    }, []);

    return (
        <points position={position}>
            <bufferGeometry>
                <bufferAttribute 
                    attach="attributes-position" 
                    count={1} 
                    array={new Float32Array([0, 0, 0])} 
                    itemSize={3} 
                />
            </bufferGeometry>
            <pointsMaterial
                ref={materialRef}
                color="#FF0000"
                size={2.0} // Small but visible size
                map={texture}
                transparent
                depthWrite={false}
                blending={THREE.AdditiveBlending}
                sizeAttenuation={true}
            />
        </points>
    );
};

const GalaxyParticles = ({ data, massThreshold, onHover, searchActive }) => {
    const pointsRef = useRef();

    // Shader definitions
    const vertexShader = `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        void main() {
            vColor = color;
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            // Scale size by distance, but keep a minimum visual size
            gl_PointSize = size * (300.0 / -mvPosition.z);
            gl_Position = projectionMatrix * mvPosition;
        }
    `;

    const fragmentShader = `
        varying vec3 vColor;
        void main() {
            // Soft glow particle
            vec2 coord = gl_PointCoord - vec2(0.5);
            float r = length(coord);
            if (r > 0.5) discard;
            
            // Gaussian-like falloff for glow
            float glow = exp(-r * r * 8.0);
            
            // Core intensity
            float core = 1.0 - smoothstep(0.0, 0.2, r);
            
            // Mix core and glow
            float alpha = glow * 0.8 + core * 0.4;
            
            gl_FragColor = vec4(vColor, alpha);
        }
    `;

    const { positions, colors, sizes, particles, matchedGalaxy, labeledGalaxies } = useMemo(() => {
        const pos = [];
        const cols = [];
        const s = [];
        const particlesList = [];
        const labeled = [];
        let match = null;

        // Magma Colormap Approximation
        // 0.0 -> Black/Purple
        // 0.25 -> Purple/Red
        // 0.5 -> Red/Orange
        // 0.75 -> Orange/Yellow
        // 1.0 -> White
        const colorStops = [
            { t: 0.0, c: new THREE.Color('#000004') }, // Black
            { t: 0.2, c: new THREE.Color('#3B0F70') }, // Dark Purple
            { t: 0.4, c: new THREE.Color('#8C2981') }, // Purple
            { t: 0.6, c: new THREE.Color('#DE4968') }, // Red/Pink
            { t: 0.8, c: new THREE.Color('#FE9F6D') }, // Orange
            { t: 1.0, c: new THREE.Color('#FCFDBF') }  // Yellow/White
        ];

        const getMagmaColor = (t) => {
            // Clamp t
            t = Math.max(0, Math.min(1, t));
            
            // Find segment
            for (let i = 0; i < colorStops.length - 1; i++) {
                if (t >= colorStops[i].t && t <= colorStops[i+1].t) {
                    const tSeg = (t - colorStops[i].t) / (colorStops[i+1].t - colorStops[i].t);
                    return new THREE.Color().lerpColors(colorStops[i].c, colorStops[i+1].c, tSeg);
                }
            }
            return colorStops[colorStops.length-1].c;
        };

        data.forEach((d, i) => {
            // Position
            pos.push(d.x, d.y, d.z);
            
            // Store ref for raycasting/hover
            particlesList.push({ ...d, originalIndex: i });

            // Find match
            if (searchActive && d.isMatch) {
                match = d;
            }

            // Labels for massive galaxies
            if (d.mass_log > massThreshold) {
                labeled.push(d);
            }

            // Color Logic: Magma based on Mass
            // Map mass 6.0 -> 11.5 to 0.0 -> 1.0
            // We want dwarfs to be dark purple, massive to be bright yellow/white
            const t = (d.mass_log - 6.0) / 5.5;
            const c = getMagmaColor(t);
            
            cols.push(c.r, c.g, c.b);

            // Size Logic
            // Make them slightly larger generally to show off the glow
            let baseSize = 1.0;
            if (d.mass_log < 8.0) {
                baseSize = 1.5; // Small dwarfs
            } else if (d.mass_log < 10.0) {
                baseSize = 2.5; // Mid-size
            } else {
                baseSize = 4.0; // Massive
            }
            
            s.push(baseSize);
        });

        return {
            positions: new Float32Array(pos),
            colors: new Float32Array(cols),
            sizes: new Float32Array(s),
            particles: particlesList,
            matchedGalaxy: match,
            labeledGalaxies: labeled
        };
    }, [data, massThreshold, searchActive]);

    // Ensure bounding sphere is computed for raycasting
    useLayoutEffect(() => {
        if (pointsRef.current) {
            pointsRef.current.geometry.computeBoundingSphere();
        }
    }, [positions]);

    return (
        <group>
            <points 
                ref={pointsRef}
                key={massThreshold} 
                onPointerMove={(e) => {
                    e.stopPropagation();
                    if (e.index !== undefined) {
                        onHover(particles[e.index]);
                    }
                }}
                onPointerOut={(e) => {
                    e.stopPropagation();
                    onHover(null);
                }}
            >
                <bufferGeometry>
                    <bufferAttribute 
                        attach="attributes-position" 
                        count={positions.length / 3} 
                        array={positions} 
                        itemSize={3} 
                    />
                    <bufferAttribute 
                        attach="attributes-color" 
                        count={colors.length / 3} 
                        array={colors} 
                        itemSize={3} 
                    />
                    <bufferAttribute 
                        attach="attributes-size" 
                        count={sizes.length} 
                        array={sizes} 
                        itemSize={1} 
                    />
                </bufferGeometry>
                <shaderMaterial
                    vertexShader={vertexShader}
                    fragmentShader={fragmentShader}
                    transparent
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </points>

            {/* Labels for Massive Galaxies */}
            {labeledGalaxies.map((g, i) => (
                <Text
                    key={`label-${i}`}
                    position={[g.x + 0.5, g.y + 0.5, g.z]} // Offset slightly
                    fontSize={0.5}
                    color="white"
                    anchorX="left"
                    anchorY="middle"
                    outlineWidth={0.05}
                    outlineColor="black"
                >
                    {g.name}
                </Text>
            ))}

            {/* Blinking Marker for Matched Galaxy */}
            {matchedGalaxy && (
                <BlinkingMarker position={[matchedGalaxy.x, matchedGalaxy.y, matchedGalaxy.z]} />
            )}
        </group>
    );
};

export default GalaxyParticles;
