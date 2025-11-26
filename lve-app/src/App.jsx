import { useState, useEffect, useMemo } from 'react';
import Scene from './components/Scene';
import UIOverlay from './components/UIOverlay';
import { loadData } from './utils/dataUtils';
// Since we don't have python's astropy in browser, we'll use a simple utility function for RA/Dec -> Cartesian.

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // --- State ---
  // Filters
  const [showLocalGroup, setShowLocalGroup] = useState(false);
  const [showMajorGroups, setShowMajorGroups] = useState(false);
  const [minMass, setMinMass] = useState(6.0); // Log Solar Mass
  const [maxDist, setMaxDist] = useState(11.0);
  
  // Classification
  const [massThreshold, setMassThreshold] = useState(9.0);
  
  // Search & Locate
  const [searchQuery, setSearchQuery] = useState("");
  const [userMarker, setUserMarker] = useState(null);
  const [hoveredGalaxy, setHoveredGalaxy] = useState(null);

  useEffect(() => {
    loadData('/data/LVDB_comb_all.csv')
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
          console.error("Data Load Error:", err);
          setError(err.message || "Failed to load data");
          setLoading(false);
      });
  }, []);

  // Filter Data
  const processedData = useMemo(() => {
    const lowerQuery = searchQuery.toLowerCase();
    return data.filter(d => {
        // Distance Filter
        if (d.dist_mpc > maxDist) return false;
        
        // Mass Filter (Show only galaxies above minMass)
        if (d.mass_log < minMass) return false;

        // Local Group Filter
        if (showLocalGroup && d.dist_mpc > 3.0) return false;

        return true;
    }).map(d => ({
        ...d,
        // If search is active, check match. If empty, all match.
        isMatch: searchQuery ? d.name.toLowerCase().includes(lowerQuery) : true
    }));
  }, [data, maxDist, minMass, showLocalGroup, searchQuery]);

  if (loading) return <div className="flex items-center justify-center h-screen bg-black text-white">Loading Universe...</div>;
  if (error) return <div className="flex items-center justify-center h-screen bg-black text-red-500">Error: {error}</div>;

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <Scene 
        data={processedData} 
        massThreshold={massThreshold}
        onHover={setHoveredGalaxy}
        userMarker={userMarker}
        searchActive={!!searchQuery}
      />
      <UIOverlay 
        // Filters
        showLocalGroup={showLocalGroup} setShowLocalGroup={setShowLocalGroup}
        minMass={minMass} setMinMass={setMinMass}
        maxDist={maxDist} setMaxDist={setMaxDist}
        
        // Classification
        massThreshold={massThreshold} setMassThreshold={setMassThreshold}
        
        // Search & Locate
        searchQuery={searchQuery} setSearchQuery={setSearchQuery}
        setUserMarker={setUserMarker}
        
        // Info
        hoveredGalaxy={hoveredGalaxy}
      />
    </div>
  );
}

export default App;
