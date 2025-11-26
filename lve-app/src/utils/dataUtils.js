import Papa from 'papaparse';

export const loadData = async (url) => {
  console.log(`Attempting to load data from: ${url}`);
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        console.log("CSV Parse Complete. Rows:", results.data.length);
        if (results.data.length === 0) {
            console.warn("CSV is empty!");
            resolve([]);
            return;
        }

        // Pre-scan to detect mass scale
        let maxMass = 0;
        results.data.forEach(row => {
            if (row.mass_stellar > maxMass) maxMass = row.mass_stellar;
        });
        const isLinear = maxMass > 20;
        console.log(`Detected Mass Scale: ${isLinear ? 'Linear' : 'Log'}. Max Mass: ${maxMass}`);

        const data = results.data
          .filter(row => row.sg_xx != null && row.sg_yy != null && row.sg_zz != null)
          .map((row, index) => {
            // Coordinates kpc -> Mpc
            const x = row.sg_xx / 1000;
            const y = row.sg_yy / 1000;
            const z = row.sg_zz / 1000;
            
            // Mass processing
            let mass = row.mass_stellar || 0;
            if (isLinear && mass > 0) {
                mass = Math.log10(mass);
            }
            
            return {
              id: index,
              ...row,
              x, y, z,
              mass_log: mass,
              dist_mpc: (row.distance || 0) / 1000
            };
          });
        
        console.log("Processed Data Length:", data.length);
        resolve(data);
      },
      error: (err) => {
          console.error("PapaParse Error:", err);
          reject(err);
      }
    });
  });
};
