import json

def get_threejs_html(data_json, user_marker_json, width=800, height=800):
    """
    Generates the HTML string for the Three.js visualization.
    
    Args:
        data_json (str): JSON string of the galaxy data (list of dicts).
        user_marker_json (str): JSON string for the user marker (dict or null).
        width (int): Width of the container.
        height (int): Height of the container.
    """
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #000; }}
            #info {{
                position: absolute;
                top: 10px;
                left: 10px;
                color: white;
                font-family: 'Helvetica Neue', sans-serif;
                pointer-events: none;
                font-size: 14px;
                background: rgba(0,0,0,0.5);
                padding: 5px;
                border-radius: 4px;
                display: none;
            }}
        </style>
        <!-- Import Three.js and OrbitControls from CDN -->
        <script type="importmap">
          {{
            "imports": {{
              "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
              "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
            }}
          }}
        </script>
    </head>
    <body>
        <div id="container"></div>
        <div id="info"></div>

        <script type="module">
            import * as THREE from 'three';
            import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

            // --- Data ---
            const galaxies = {data_json};
            const userMarker = {user_marker_json};

            // --- Scene Setup ---
            const scene = new THREE.Scene();
            scene.fog = new THREE.FogExp2(0x000000, 0.002); // Distance fog

            const camera = new THREE.PerspectiveCamera(60, {width} / {height}, 0.1, 2000);
            camera.position.set(10, 10, 20);

            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize({width}, {height});
            renderer.setPixelRatio(window.devicePixelRatio);
            document.getElementById('container').appendChild(renderer.domElement);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // --- Textures ---
            // Create a simple glow texture programmatically
            function createGlowTexture() {{
                const canvas = document.createElement('canvas');
                canvas.width = 32;
                canvas.height = 32;
                const context = canvas.getContext('2d');
                const gradient = context.createRadialGradient(16, 16, 0, 16, 16, 16);
                gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
                gradient.addColorStop(0.2, 'rgba(255, 255, 255, 0.8)');
                gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.2)');
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                context.fillStyle = gradient;
                context.fillRect(0, 0, 32, 32);
                const texture = new THREE.CanvasTexture(canvas);
                return texture;
            }}
            const glowTexture = createGlowTexture();

            // --- Starfield Background ---
            const starGeometry = new THREE.BufferGeometry();
            const starCount = 5000;
            const starPos = new Float32Array(starCount * 3);
            for(let i=0; i<starCount*3; i++) {{
                starPos[i] = (Math.random() - 0.5) * 1000;
            }}
            starGeometry.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
            const starMaterial = new THREE.PointsMaterial({{
                color: 0x888888,
                size: 0.5,
                sizeAttenuation: true,
                transparent: true,
                opacity: 0.8
            }});
            const stars = new THREE.Points(starGeometry, starMaterial);
            scene.add(stars);

            // --- Galaxies ---
            // We will separate Massive and Dwarf for different styling
            const massivePositions = [];
            const massiveColors = [];
            const massiveSizes = [];
            
            const dwarfPositions = [];
            const dwarfColors = [];
            
            const colorMassive = new THREE.Color(0xff4444); // Red
            const colorDwarf = new THREE.Color(0x00ffff);   // Cyan

            galaxies.forEach(g => {{
                if (g.is_massive) {{
                    massivePositions.push(g.x, g.y, g.z);
                    // Slight color variation
                    massiveColors.push(colorMassive.r, colorMassive.g + Math.random()*0.2, colorMassive.b);
                    massiveSizes.push(g.size);
                }} else {{
                    dwarfPositions.push(g.x, g.y, g.z);
                    dwarfColors.push(colorDwarf.r, colorDwarf.g, colorDwarf.b + Math.random()*0.2);
                }}
            }});

            // Massive Galaxies (Glowing Sprites)
            if (massivePositions.length > 0) {{
                const massiveGeo = new THREE.BufferGeometry();
                massiveGeo.setAttribute('position', new THREE.Float32BufferAttribute(massivePositions, 3));
                massiveGeo.setAttribute('color', new THREE.Float32BufferAttribute(massiveColors, 3));
                // We can't easily pass per-particle size to standard PointsMaterial without shader.
                // But let's use a uniform size for now, or use a custom shader if we really want variable size.
                // For simplicity/robustness in this snippet, let's use a nice PointsMaterial.
                
                const massiveMat = new THREE.PointsMaterial({{
                    size: 1.5,
                    map: glowTexture,
                    vertexColors: true,
                    transparent: true,
                    opacity: 0.9,
                    depthWrite: false,
                    blending: THREE.AdditiveBlending
                }});
                const massivePoints = new THREE.Points(massiveGeo, massiveMat);
                scene.add(massivePoints);
            }}

            // Dwarf Galaxies (Smaller, Fainter)
            if (dwarfPositions.length > 0) {{
                const dwarfGeo = new THREE.BufferGeometry();
                dwarfGeo.setAttribute('position', new THREE.Float32BufferAttribute(dwarfPositions, 3));
                dwarfGeo.setAttribute('color', new THREE.Float32BufferAttribute(dwarfColors, 3));
                
                const dwarfMat = new THREE.PointsMaterial({{
                    size: 0.5,
                    map: glowTexture,
                    vertexColors: true,
                    transparent: true,
                    opacity: 0.5,
                    depthWrite: false,
                    blending: THREE.AdditiveBlending
                }});
                const dwarfPoints = new THREE.Points(dwarfGeo, dwarfMat);
                scene.add(dwarfPoints);
            }}

            // --- User Marker ---
            if (userMarker) {{
                const markerGeo = new THREE.OctahedronGeometry(0.5, 0);
                const markerMat = new THREE.MeshBasicMaterial({{ color: 0x00ff00, wireframe: true }});
                const markerMesh = new THREE.Mesh(markerGeo, markerMat);
                markerMesh.position.set(userMarker.x, userMarker.y, userMarker.z);
                scene.add(markerMesh);
                
                // Add a line to origin
                const points = [];
                points.push(new THREE.Vector3(0, 0, 0));
                points.push(new THREE.Vector3(userMarker.x, userMarker.y, userMarker.z));
                const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
                const lineMat = new THREE.LineBasicMaterial({{ color: 0x00ff00, transparent: true, opacity: 0.3 }});
                const line = new THREE.Line(lineGeo, lineMat);
                scene.add(line);
            }}

            // --- Raycaster for Interaction ---
            const raycaster = new THREE.Raycaster();
            raycaster.params.Points.threshold = 0.5;
            const mouse = new THREE.Vector2();
            const infoDiv = document.getElementById('info');

            window.addEventListener('mousemove', (event) => {{
                // Calculate mouse position in normalized device coordinates
                // The container might not be full screen, so we need bounding rect
                const rect = renderer.domElement.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                
                // Update info div position
                infoDiv.style.left = (event.clientX - rect.left + 15) + 'px';
                infoDiv.style.top = (event.clientY - rect.top + 15) + 'px';
            }});

            // --- Animation Loop ---
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();

                // Raycasting
                raycaster.setFromCamera(mouse, camera);
                // We need to raycast against both point clouds if they exist
                const targets = [];
                scene.children.forEach(child => {{
                    if (child.isPoints && child !== stars) {{
                        targets.push(child);
                    }}
                }});
                
                const intersects = raycaster.intersectObjects(targets);

                if (intersects.length > 0) {{
                    const index = intersects[0].index;
                    const object = intersects[0].object;
                    
                    // Find the galaxy data corresponding to this point
                    // This is tricky because we split the data into two arrays.
                    // A simpler way is to just find the closest galaxy in the original list to the intersection point.
                    const point = intersects[0].point;
                    
                    // Simple linear search for closest galaxy (fast enough for <1000 items)
                    let closestDist = Infinity;
                    let closestGalaxy = null;
                    
                    for (let g of galaxies) {{
                        const d = (g.x - point.x)**2 + (g.y - point.y)**2 + (g.z - point.z)**2;
                        if (d < closestDist) {{
                            closestDist = d;
                            closestGalaxy = g;
                        }}
                    }}

                    if (closestGalaxy && closestDist < 1.0) {{
                        infoDiv.style.display = 'block';
                        infoDiv.innerHTML = `<strong>${{closestGalaxy.name}}</strong><br>Dist: ${{closestGalaxy.dist.toFixed(2)}} Mpc<br>M_V: ${{closestGalaxy.lum.toFixed(2)}}`;
                        document.body.style.cursor = 'pointer';
                    }} else {{
                        infoDiv.style.display = 'none';
                        document.body.style.cursor = 'default';
                    }}
                }} else {{
                    infoDiv.style.display = 'none';
                    document.body.style.cursor = 'default';
                }}

                renderer.render(scene, camera);
            }}
            animate();

            // Handle resize
            window.addEventListener('resize', () => {{
                // For Streamlit component, window resize might not trigger correctly for the iframe
                // But we can try
                // camera.aspect = window.innerWidth / window.innerHeight;
                // camera.updateProjectionMatrix();
                // renderer.setSize(window.innerWidth, window.innerHeight);
            }});
        </script>
    </body>
    </html>
    """
    return html_template
