import streamlit as st
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import streamlit.components.v1 as components
import json
from viz_utils import get_threejs_html

# Set page config
st.set_page_config(layout="wide", page_title="Local Volume Explorer", initial_sidebar_state="expanded")

# Custom CSS for Dark Universe Theme
st.markdown("""
<style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #111111;
    }
    div[data-testid="stSidebarUserContent"] {
        background-color: #111111;
    }
    h1, h2, h3 {
        color: #e0e0e0 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stCheckbox label {
        color: #cccccc !important;
    }
    .stSlider label {
        color: #cccccc !important;
    }
    .stTextInput label {
        color: #cccccc !important;
    }
    .stNumberInput label {
        color: #cccccc !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading & Processing ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/LVDB_comb_all.csv")
        
        # Coordinate Conversion (kpc -> Mpc)
        df['x'] = df['sg_xx'] / 1000.0
        df['y'] = df['sg_yy'] / 1000.0
        df['z'] = df['sg_zz'] / 1000.0
        
        # Ensure mass_stellar is numeric
        df['mass_stellar'] = pd.to_numeric(df['mass_stellar'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

# --- Sidebar Controls ---
st.sidebar.title("🌌 LV Explorer")

# Filters
st.sidebar.subheader("Filters")
show_local_group = st.sidebar.checkbox("Local Group Only", value=False)
show_major_groups = st.sidebar.checkbox("Major Groups Only", value=False)

# Luminosity Filter (M_V)
min_lum, max_lum = st.sidebar.slider("Absolute Magnitude (M_V)", -25.0, 0.0, (-25.0, 0.0))

# Distance Filter (Mpc)
max_dist = st.sidebar.slider("Max Distance (Mpc)", 0.0, 15.0, 11.0)

# Mass Threshold Slider
st.sidebar.subheader("Classification")
mass_threshold = st.sidebar.slider("Massive Galaxy Threshold (log M*)", 6.0, 12.0, 9.0, 0.1, help="Galaxies above this stellar mass (log10) are considered 'Massive'.")

# Search
st.sidebar.subheader("Search")
search_query = st.sidebar.text_input("Find Galaxy", "")

# Coordinate Input
st.sidebar.subheader("Locate Coordinate")
input_ra = st.sidebar.number_input("RA (deg)", value=0.0)
input_dec = st.sidebar.number_input("Dec (deg)", value=0.0)
input_dist = st.sidebar.number_input("Distance (Mpc)", value=1.0)
show_marker = st.sidebar.checkbox("Show Marker", value=False)

# --- Filtering Logic ---
if not df.empty:
    filtered_df = df.copy()
    
    # Distance Filter
    if 'distance' in filtered_df.columns:
         filtered_df = filtered_df[filtered_df['distance'] / 1000.0 <= max_dist]
    
    # Luminosity Filter
    if 'M_V' in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df['M_V'] >= min_lum) & (filtered_df['M_V'] <= max_lum)]

    # Search
    if search_query:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]

    # --- Prepare Data for Three.js ---
    
    # Classification
    if 'mass_stellar' in filtered_df.columns:
        is_linear = filtered_df['mass_stellar'].max() > 20
        if is_linear:
             mass_col = np.log10(filtered_df['mass_stellar'].replace(0, np.nan))
        else:
             mass_col = filtered_df['mass_stellar']
        
        # Add is_massive column
        filtered_df['is_massive'] = mass_col > mass_threshold
    else:
        filtered_df['is_massive'] = False

    # Prepare JSON list
    galaxy_data = []
    for _, row in filtered_df.iterrows():
        galaxy_data.append({
            "name": str(row['name']),
            "x": float(row['x']),
            "y": float(row['y']),
            "z": float(row['z']),
            "is_massive": bool(row['is_massive']),
            "dist": float(row['distance'] / 1000.0) if 'distance' in row else 0,
            "lum": float(row['M_V']) if 'M_V' in row else 0,
            "size": 1.5 if row['is_massive'] else 0.5 # Base size, can be tweaked
        })
    
    # User Marker
    user_marker_data = None
    if show_marker:
        c = SkyCoord(ra=input_ra*u.degree, dec=input_dec*u.degree, distance=input_dist*u.Mpc)
        c_sg = c.supergalactic.cartesian
        user_marker_data = {
            "x": float(c_sg.x.value),
            "y": float(c_sg.y.value),
            "z": float(c_sg.z.value)
        }

    # Generate HTML
    html_code = get_threejs_html(
        json.dumps(galaxy_data), 
        json.dumps(user_marker_data),
        width=1000,
        height=800
    )

    # Render Three.js Component
    components.html(html_code, height=800, width=1000)
    
    # Info Panel (below viz)
    if not filtered_df.empty:
        st.markdown("### 🔭 Galaxy Details")
        st.dataframe(filtered_df[['name', 'distance', 'M_V', 'mass_stellar']].head(20), use_container_width=True)

else:
    st.warning("No data available.")
