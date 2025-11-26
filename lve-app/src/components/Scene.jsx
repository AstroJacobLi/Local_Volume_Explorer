import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import GalaxyParticles from './GalaxyParticles';
import * as THREE from 'three';

// Blinking Marker Component (Red Soft Dot)
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
        <points position={[position.x, position.y, position.z]}>
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

const Scene = ({ data, massThreshold, onHover, userMarker, searchActive }) => {
  return (
    <div className="w-full h-screen bg-black">
      <Canvas 
        camera={{ position: [10, 10, 20], fov: 60 }}
        raycaster={{ params: { Points: { threshold: 1.0 } } }} // Increased threshold for better hover detection
      >
        <color attach="background" args={['#050505']} />
        <fog attach="fog" args={['#050505', 10, 100]} />
        
        <OrbitControls enableDamping dampingFactor={0.05} />
        
        {/* Stars Background */}
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        {/* XYZ Axes */}
        <axesHelper args={[5]} />

        {/* Galaxies */}
        <GalaxyParticles 
            data={data} 
            massThreshold={massThreshold} 
            onHover={onHover} 
            searchActive={searchActive}
        />

        {/* User Marker */}
        {userMarker && <BlinkingMarker position={userMarker} />}
      </Canvas>
    </div>
  );
};

export default Scene;
