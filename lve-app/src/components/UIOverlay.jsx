import { useState } from 'react';
import { Search, MapPin, Sliders, Info, Crosshair } from 'lucide-react';

const UIOverlay = ({ 
    showLocalGroup, setShowLocalGroup,
    minMass, setMinMass,
    maxDist, setMaxDist,
    massThreshold, setMassThreshold,
    searchQuery, setSearchQuery,
    setUserMarker,
    hoveredGalaxy
}) => {
    // Local state for Locate inputs
    const [ra, setRa] = useState(0);
    const [dec, setDec] = useState(0);
    const [dist, setDist] = useState(1);

    console.log("Rendering UIOverlay...");

    const handleLocate = () => {
        // Convert RA/Dec/Dist to Cartesian (Supergalactic approximation or simple spherical)
        // Note: Real conversion requires complex math. 
        // For now, we'll use a simple spherical conversion assuming input is Supergalactic for simplicity,
        // OR we implement a rough RA/Dec -> SG conversion here.
        // Let's assume the user inputs Supergalactic coordinates for now to match the view, 
        // or we just map them directly to x/y/z if they want to probe a point.
        // Actually, let's just do simple spherical to Cartesian:
        // x = d * cos(dec) * cos(ra)
        // y = d * cos(dec) * sin(ra)
        // z = d * sin(dec)
        // (Converting degrees to radians)
        
        const d2r = Math.PI / 180;
        const x = dist * Math.cos(dec * d2r) * Math.cos(ra * d2r);
        const y = dist * Math.cos(dec * d2r) * Math.sin(ra * d2r);
        const z = dist * Math.sin(dec * d2r);
        
        setUserMarker({ x, y, z });
    };

  return (
    <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-50">
        {/* Sidebar */}
        <div className="absolute top-0 left-0 h-full w-80 bg-black/90 backdrop-blur-xl border-r border-white/10 p-6 pointer-events-auto overflow-y-auto custom-scrollbar">
            {/* Header / Logo */}
            <div className="mb-8">
                <h1 className="text-4xl font-black tracking-tighter text-white drop-shadow-[0_0_15px_rgba(0,243,255,0.8)]">
                    LVE
                </h1>
                <p className="text-xs text-gray-300 tracking-widest uppercase mt-1 font-semibold">Local Volume Explorer</p>
            </div>

            {/* Controls Container */}
            <div className="space-y-8">
                
                {/* Section: Visibility Filters */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-neon-blue mb-2">
                        <Sliders size={16} />
                        <h2 className="text-sm font-bold uppercase tracking-wider">Filters</h2>
                    </div>

                    {/* Checkboxes */}
                    <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer group">
                            <input 
                                type="checkbox" 
                                checked={showLocalGroup}
                                onChange={(e) => setShowLocalGroup(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-neon-blue focus:ring-neon-blue/50"
                            />
                            <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Local Group</span>
                        </label>
                    </div>

                    {/* Min Mass Slider */}
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">Min Mass (log M*)</span>
                            <span className="text-white font-mono">{minMass}</span>
                        </div>
                        <input 
                            type="range" min="4" max="10" step="0.5" 
                            value={minMass}
                            onChange={(e) => setMinMass(parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-white hover:accent-neon-blue transition-colors"
                        />
                    </div>

                    {/* Max Distance Slider */}
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">Max Distance</span>
                            <span className="text-white font-mono">{maxDist} Mpc</span>
                        </div>
                        <input 
                            type="range" min="0" max="15" step="0.5" 
                            value={maxDist}
                            onChange={(e) => setMaxDist(parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-white hover:accent-neon-blue transition-colors"
                        />
                    </div>
                </div>

                {/* Section: Classification */}
                <div className="space-y-4 pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2 text-neon-red mb-2">
                        <Info size={16} />
                        <h2 className="text-sm font-bold uppercase tracking-wider">Classification</h2>
                    </div>
                    
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">Massive Threshold</span>
                            <span className="text-neon-red font-mono">{massThreshold}</span>
                        </div>
                        <input 
                            type="range" min="6" max="11" step="0.1" 
                            value={massThreshold}
                            onChange={(e) => setMassThreshold(parseFloat(e.target.value))}
                            className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-neon-red"
                        />
                        <p className="text-[10px] text-gray-500 mt-1">
                            Galaxies above 10^{massThreshold} M* are highlighted as massive.
                        </p>
                    </div>
                </div>

                {/* Section: Search */}
                <div className="space-y-4 pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2 text-white mb-2">
                        <Search size={16} />
                        <h2 className="text-sm font-bold uppercase tracking-wider">Search</h2>
                    </div>
                    <input 
                        type="text" 
                        placeholder="Find galaxy (e.g. Andromeda)..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-black/50 border border-gray-700 rounded-lg py-2 px-3 text-sm text-white focus:outline-none focus:border-neon-blue transition-colors placeholder-gray-600"
                    />
                </div>

                {/* Section: Locate */}
                <div className="space-y-4 pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                        <Crosshair size={16} />
                        <h2 className="text-sm font-bold uppercase tracking-wider">Locate</h2>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">RA (°)</label>
                            <input type="number" value={ra} onChange={e => setRa(parseFloat(e.target.value))} className="w-full bg-black/50 border border-gray-700 rounded px-2 py-1 text-xs text-white" />
                        </div>
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">Dec (°)</label>
                            <input type="number" value={dec} onChange={e => setDec(parseFloat(e.target.value))} className="w-full bg-black/50 border border-gray-700 rounded px-2 py-1 text-xs text-white" />
                        </div>
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">Dist (Mpc)</label>
                            <input type="number" value={dist} onChange={e => setDist(parseFloat(e.target.value))} className="w-full bg-black/50 border border-gray-700 rounded px-2 py-1 text-xs text-white" />
                        </div>
                    </div>
                    <button 
                        onClick={handleLocate}
                        className="w-full bg-gray-800 hover:bg-green-500/20 hover:text-green-400 border border-gray-700 hover:border-green-500/50 text-gray-300 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                    >
                        Go to Coordinates
                    </button>
                </div>

            </div>

            {/* Galaxy Info Panel (Floating) */}
            {hoveredGalaxy && (
                <div className="fixed bottom-6 left-80 ml-6 p-4 bg-black/80 backdrop-blur-xl rounded-xl border border-white/20 shadow-[0_0_30px_rgba(0,0,0,0.5)] w-64 animate-in fade-in slide-in-from-bottom-4 pointer-events-none">
                    <h3 className="text-xl font-bold text-white mb-1">{hoveredGalaxy.name}</h3>
                    <div className="h-0.5 w-10 bg-neon-blue mb-3"></div>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Distance</span>
                            <span className="text-white font-mono">{hoveredGalaxy.dist_mpc.toFixed(2)} <span className="text-xs text-gray-500">Mpc</span></span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Stellar Mass</span>
                            <span className="text-white font-mono">10^{hoveredGalaxy.mass_log.toFixed(1)} <span className="text-xs text-gray-500">M*</span></span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Abs Mag (V)</span>
                            <span className="text-white font-mono">{hoveredGalaxy.M_V}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Type</span>
                            <span className={hoveredGalaxy.mass_log > massThreshold ? "text-neon-red font-bold" : "text-neon-blue"}>
                                {hoveredGalaxy.mass_log > massThreshold ? "MASSIVE" : "DWARF"}
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    </div>
  );
};

export default UIOverlay;
