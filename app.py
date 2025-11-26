import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

# --- Color Palette ---
C_MASSIVE = '#ffbf00' # Golden/Amber
C_DWARF = '#a6c8ff'   # Pale Blue
C_VIRIAL = '#808080'  # light gray
C_MW = 'seagreen'
C_M31 = '#FFA500'     # Orange
C_USER = 'purple'
C_HIGHLIGHT = 'crimson'
C_BG = '#111111'      # Dark Gray
C_GRID = '#333333'
C_TEXT = 'white'
C_MARKER_LINE = '#ffffff'

# Set page config
st.set_page_config(layout="wide", page_title="Local Volume Explorer", initial_sidebar_state="expanded")

# --- Session State Initialization ---
if 'ui_revision' not in st.session_state:
    st.session_state.ui_revision = 0

if 'center_target' not in st.session_state:
    st.session_state.center_target = None # dict(x, y, z)

# --- Custom CSS (Dark Theme Only) ---
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
    .stCheckbox label, .stSlider label, .stTextInput label, .stNumberInput label {
        color: #e0e0e0 !important;
    }
    /* Input Box Styling */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        color: #ffffff !important;
        background-color: #222222 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: #ff4444 !important;
    }
    /* Button Styling for Dark Mode */
    .stButton button {
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #555555;
    }
    .stButton button:hover {
        background-color: #444444;
        border-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

plotly_template = 'plotly_dark'
marker_line_color = C_MARKER_LINE
user_marker_color = C_USER

# --- Helper Functions ---

def puebla17_ms_to_mh(logms, mh_1=12.58, ms_0=10.90, beta=0.48, delta=0.29, gamma=1.52,
                      redshift=None):
    """
    Halo mass from stellar mass based on Rodriguez-Puebla et al. 2017 (arxiv:1703.04542).
    """
    if redshift is not None:
        if 0.0 < redshift <= 0.20:
            mh_1, ms_0, beta, delta, gamma = 12.58, 10.90, 0.48, 0.29, 1.52
        elif 0.20 < redshift <= 0.40:
            mh_1, ms_0, beta, delta, gamma = 12.61, 10.93, 0.48, 0.27, 1.46
        elif 0.40 < redshift <= 0.60:
            mh_1, ms_0, beta, delta, gamma = 12.68, 10.99, 0.48, 0.23, 1.39
        elif 0.60 < redshift <= 0.90:
            mh_1, ms_0, beta, delta, gamma = 12.77, 11.08, 0.50, 0.18, 1.33
        elif 0.90 < redshift <= 1.20:
            mh_1, ms_0, beta, delta, gamma = 12.89, 11.19, 0.51, 0.12, 1.27
        elif 1.20 < redshift <= 1.40:
            mh_1, ms_0, beta, delta, gamma = 13.01, 11.31, 0.53, 0.03, 1.22
        elif 1.40 < redshift <= 1.60:
            mh_1, ms_0, beta, delta, gamma = 13.15, 11.47, 0.54, -0.10, 1.17
        elif 1.60 < redshift <= 1.80:
            mh_1, ms_0, beta, delta, gamma = 13.33, 11.73, 0.55, -0.34, 1.16
        else:
            raise Exception("# Wrong redshift range: [0.0, 1.8]")

    mass_ratio  = (10.0 ** logms) / (10.0 ** ms_0)
    
    term_1 = np.log10(mass_ratio) * beta
    term_2 = mass_ratio ** delta
    term_3 = (mass_ratio ** -gamma) + 1.0

    return mh_1 + term_1 + (term_2 / term_3) - 0.50

def create_sphere_mesh(x_center, y_center, z_center, radius, color, name, hover_text, opacity=1.0):
    # Create a sphere
    phi = np.linspace(0, 2*np.pi, 20)
    theta = np.linspace(0, np.pi, 20)
    phi, theta = np.meshgrid(phi, theta)
    
    x_sphere = radius * np.sin(theta) * np.cos(phi) + x_center
    y_sphere = radius * np.sin(theta) * np.sin(phi) + y_center
    z_sphere = radius * np.cos(theta) + z_center
    
    return go.Mesh3d(
        x=x_sphere.flatten(),
        y=y_sphere.flatten(),
        z=z_sphere.flatten(),
        alphahull=0,
        color=color,
        opacity=opacity,
        name=name,
        text=hover_text,
        hoverinfo='text'
    )

# --- Data Loading & Processing ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/LVDB_comb_all.csv")
        
        # Coordinate Conversion (kpc -> Mpc)
        # Using Supergalactic coordinates provided in catalog
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
st.sidebar.title("🌌 Local Volume Explorer")


# Filters
st.sidebar.subheader("Filters")
show_local_group = st.sidebar.checkbox("Local Group Only (< 1 Mpc)", value=False)

# Stellar Mass Filter (log M*) - Replaces Luminosity
min_mass, max_mass = st.sidebar.slider("Stellar Mass (log M*)", 0.0, 12.0, (0.0, 12.0))

# Distance Filter (Mpc)
max_dist = st.sidebar.slider("Max Distance (Mpc)", 0.0, 15.0, 11.0)

# Mass Threshold Slider (for Classification)
st.sidebar.subheader("Classification")
mass_threshold = st.sidebar.slider("Massive Galaxy Threshold (log M*)", 6.0, 12.0, 10.0, 0.1, help="Galaxies above this stellar mass (log10) are considered 'Massive'.")
dwarf_size_scale = st.sidebar.slider("Dwarf Marker Size Scale", 0.1, 10.0, 0.5, 0.1, help="Adjusts the size of dwarf galaxies.")

# Search
st.sidebar.subheader("Search")
search_query = st.sidebar.text_input("Find Galaxy", "")
target_galaxy_name = None

if search_query and not df.empty:
    # Filter for matches
    matches = df[df['name'].str.contains(search_query, case=False, na=False)]
    if not matches.empty:
        target_galaxy_name = st.sidebar.selectbox("Select Galaxy", matches['name'])
    else:
        st.sidebar.warning("No matches found.")
else:
    # Reset center target if search is cleared
    if st.session_state.center_target is not None:
        st.session_state.center_target = None
        st.session_state.ui_revision += 1
        st.rerun()

# Coordinate Input
st.sidebar.subheader("Locate Coordinate")
input_name = st.sidebar.text_input("Name", value="Target")
input_ra = st.sidebar.number_input("RA (deg)", value=0.0)
input_dec = st.sidebar.number_input("Dec (deg)", value=0.0)
input_dist = st.sidebar.number_input("Distance (Mpc)", value=1.0)
show_marker = st.sidebar.checkbox("Show Marker", value=False)

# --- Filtering Logic ---
if not df.empty:
    filtered_df = df.copy()
    
    # Local Group Logic
    if show_local_group:
        filtered_df = filtered_df[filtered_df['distance'] / 1000.0 <= 1.0]
    else:
        # Distance Filter
        if 'distance' in filtered_df.columns:
             filtered_df = filtered_df[filtered_df['distance'] / 1000.0 <= max_dist]
    
    # Stellar Mass Filter
    if 'mass_stellar' in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df['mass_stellar'] >= min_mass) & (filtered_df['mass_stellar'] <= max_mass)]

    # Search Logic (Highlighting & Centering)
    highlight_df = pd.DataFrame()
    if target_galaxy_name:
        highlight_df = df[df['name'] == target_galaxy_name]
        
        if not highlight_df.empty:
            st.sidebar.markdown("---")
            # st.sidebar.write(f"Selected: **{highlight_df.iloc[0]['name']}**") # Redundant with selectbox
            if st.sidebar.button("Center on this galaxy"):
                target = highlight_df.iloc[0]
                st.session_state.center_target = {'x': target['x'], 'y': target['y'], 'z': target['z']}
                st.session_state.ui_revision += 1 # Force view update
                st.rerun()

    # --- Visualization ---
    
    # Classification
    if 'mass_stellar' in filtered_df.columns:
        massive_mask = filtered_df['mass_stellar'] > mass_threshold
        massive_df = filtered_df[massive_mask]
        dwarf_df = filtered_df[~massive_mask]
    else:
        massive_df = filtered_df
        dwarf_df = pd.DataFrame()

    fig = go.Figure()

    # Dwarfs (Blue/Cyan, Small, Transparent)
    if not dwarf_df.empty:
        # Size calculation based on stellar mass
        size = dwarf_size_scale * 10**(0.2 * (dwarf_df['mass_stellar'] - 4))
        
        fig.add_trace(go.Scatter3d(
            x=dwarf_df['x'],
            y=dwarf_df['y'],
            z=dwarf_df['z'],
            mode='markers',
            marker=dict(
                size=size,
                color=C_DWARF,
                opacity=0.6,
                line=dict(width=0) # No border for dwarfs
            ),
            name='Dwarfs',
            text=dwarf_df['name'],
            hovertemplate="<b>%{text}</b><br>Dist: %{customdata[0]:.2f} Mpc<br>logM*: %{customdata[1]:.2f}<extra></extra>",
            customdata=np.stack((dwarf_df['distance'] / 1000.0, dwarf_df['mass_stellar']), axis=-1)
        ))

    # Massive (Red/Orange, Large, Opaque, Halo effect)
    if not massive_df.empty:
        fig.add_trace(go.Scatter3d(
            x=massive_df['x'],
            y=massive_df['y'],
            z=massive_df['z'],
            mode='markers+text',
            marker=dict(
                size=8,
                color=C_MASSIVE,
                opacity=0.9,
                line=dict(color=marker_line_color, width=1)
            ),
            name='Massive',
            text=massive_df['name'],
            textposition="top center",
            textfont=dict(color=marker_line_color, size=10),
            hovertemplate="<b>%{text}</b><br>Dist: %{customdata[0]:.2f} Mpc<br>logM*: %{customdata[1]:.2f}<extra></extra>",
            customdata=np.stack((massive_df['distance'] / 1000.0, massive_df['mass_stellar']), axis=-1)
        ))

    # Virial Spheres
    show_virial = st.sidebar.checkbox("Show Virial Spheres", value=False)
    
    if show_virial:
        # Add dummy trace for legend
        fig.add_trace(go.Mesh3d(x=[None], y=[None], z=[None], color=C_VIRIAL, opacity=0.2, name='Virial Sphere'))
        
        if not massive_df.empty:
            for index, row in massive_df.iterrows():
                # Calculate Halo Mass
                log_mh = puebla17_ms_to_mh(row['mass_stellar'])
                m_halo = 10**log_mh
                
                # Calculate Virial Radius (Mpc)
                # Scaling from MW: Mh = 1e12, Rvir = 0.3 Mpc
                # R ~ M^(1/3)
                r_vir = 0.3 * (m_halo / 1e12)**(1/3)
                
                hover_txt = f"<b>{row['name']}</b><br>log Mh: {log_mh:.2f}<br>Rvir: {r_vir*1000:.0f} kpc"
                
                fig.add_trace(create_sphere_mesh(
                    row['x'], row['y'], row['z'], 
                    r_vir, 
                    C_VIRIAL, 
                    'Virial Sphere', 
                    hover_txt,
                    opacity=0.1
                ))
            
        # Add MW Virial Sphere
        fig.add_trace(create_sphere_mesh(0, 0, 0, 0.3, C_VIRIAL, 'MW Halo', 'MW Halo', opacity=0.1))
        
        # Add M31 Virial Sphere (Approx same mass as MW)
        m31_c = SkyCoord(ra='00 42 44.5', dec='+41 16 09', unit=(u.hourangle, u.deg), distance=0.7*u.Mpc)
        m31_sg = m31_c.supergalactic.cartesian
        fig.add_trace(create_sphere_mesh(m31_sg.x.value, m31_sg.y.value, m31_sg.z.value, 0.3, C_VIRIAL, 'M31 Halo', 'M31 Halo', opacity=0.1))

    # Highlighted Galaxy (Search Result)
    if not highlight_df.empty:
        target = highlight_df.iloc[0]
        # # Glow Effect
        # fig.add_trace(go.Scatter3d(
        #     x=[target['x']],
        #     y=[target['y']],
        #     z=[target['z']],
        #     mode='markers',
        #     marker=dict(
        #         size=30, # Larger size for glow
        #         color=C_HIGHLIGHT, 
        #         line=dict(width=0),
        #         opacity=0.3
        #     ),
        #     hoverinfo='skip',
        #     showlegend=False
        # ))
        # Core Marker
        fig.add_trace(go.Scatter3d(
            x=[target['x']],
            y=[target['y']],
            z=[target['z']],
            mode='markers+text',
            marker=dict(
                size=10, 
                color=C_HIGHLIGHT, 
                line=dict(color=marker_line_color, width=2),
                opacity=1.0
            ),
            name='Search Result: ' + target['name'],
            text=[target['name']],
            textposition="top center",
            textfont=dict(color=C_HIGHLIGHT, size=12, family="Helvetica Neue", weight="bold"),
            hovertemplate="<b>%{text}</b><br>Dist: %{customdata:.2f} Mpc<extra></extra>",
            customdata=[target['distance'] / 1000.0]
        ))

    # Milky Way (Center)
    fig.add_trace(go.Scatter3d(
        x=[0],
        y=[0],
        z=[0],
        mode='markers+text',
        marker=dict(
            size=10,
            color=C_MW,
            line=dict(color=marker_line_color, width=1),
            opacity=0.9
        ),
        name='Milky Way',
        text=["Milky Way"],
        textposition="top center",
        textfont=dict(color=C_MW, size=10, family="Helvetica Neue"),
        hovertemplate="<b>Milky Way</b><br>Home<extra></extra>"
    ))

    # M31 (Andromeda)
    # RA=00 42 44.5, Dec=+41 16 09, distance=0.7 Mpc
    m31_c = SkyCoord(ra='00 42 44.5', dec='+41 16 09', unit=(u.hourangle, u.deg), distance=0.7*u.Mpc)
    m31_sg = m31_c.supergalactic.cartesian
    
    fig.add_trace(go.Scatter3d(
        x=[m31_sg.x.value],
        y=[m31_sg.y.value],
        z=[m31_sg.z.value],
        mode='markers+text',
        marker=dict(
            size=10,
            color=C_M31,
            line=dict(color=marker_line_color, width=1),
            opacity=0.9
        ),
        name='M31',
        text=["M31"],
        textposition="top center",
        textfont=dict(color=C_M31, size=10, family="Helvetica Neue"),
        hovertemplate="<b>M31</b><br>Dist: 0.7 Mpc<extra></extra>"
    ))

    # User Marker
    if show_marker:
        # Convert RA/Dec/Dist to Supergalactic Cartesian using Astropy
        c = SkyCoord(ra=input_ra*u.degree, dec=input_dec*u.degree, distance=input_dist*u.Mpc)
        c_sg = c.supergalactic.cartesian
        
        fig.add_trace(go.Scatter3d(
            x=[c_sg.x.value], 
            y=[c_sg.y.value], 
            z=[c_sg.z.value],
            mode='markers+text',
            marker=dict(
                size=10, 
                color=user_marker_color, # Sphere
                symbol='circle', # Sphere-like
                line=dict(color=marker_line_color, width=2),
                opacity=0.8
            ),
            name='User Location',
            text=[input_name],
            textfont=dict(color=marker_line_color, size=10),
            textposition="top center",
            hovertemplate=f"<b>{input_name}</b><br>Dist: %{{x:.2f}}, %{{y:.2f}}, %{{z:.2f}} Mpc<extra></extra>"
        ))

    # Layout Configuration
    # Background color: #111111 (Dark Gray) instead of pure black
    bg_color = C_BG
    grid_color = C_GRID
    
    scene_config = dict(
        xaxis=dict(title='SGX (Mpc)', backgroundcolor=bg_color, gridcolor=grid_color, zerolinecolor="#666666", showspikes=False),
        yaxis=dict(title='SGY (Mpc)', backgroundcolor=bg_color, gridcolor=grid_color, zerolinecolor="#666666", showspikes=False),
        zaxis=dict(title='SGZ (Mpc)', backgroundcolor=bg_color, gridcolor=grid_color, zerolinecolor="#666666", showspikes=False),
        bgcolor=bg_color,
        aspectmode='data'
    )
    
    paper_bgcolor = bg_color
    font_color = C_TEXT

    # Apply Center Target (if set)
    if st.session_state.center_target:
        t = st.session_state.center_target
        # Define a window size
        # Use max_dist to preserve the global scale (don't zoom in too much)
        window = max(max_dist, 1.0)
        scene_config['xaxis']['range'] = [t['x'] - window, t['x'] + window]
        scene_config['yaxis']['range'] = [t['y'] - window, t['y'] + window]
        scene_config['zaxis']['range'] = [t['z'] - window, t['z'] + window]

    # Define Camera View (Angle)
    # x, y, z are relative coordinates (default is usually around 1.25, 1.25, 1.25)
    # Smaller values = Closer to center (Zoom In)
    # Larger values = Further from center (Zoom Out)
    camera = dict(
        eye=dict(x=0.75, y=0.75, z=0.25) 
    )

    fig.update_layout(
        template=plotly_template,
        scene=scene_config,
        scene_camera=camera, # Apply camera settings
        dragmode='turntable', # Allows for freer rotation and zooming
        margin=dict(l=0, r=0, b=0, t=0),
        height=650,
        paper_bgcolor=paper_bgcolor,
        legend=dict(font=dict(color=font_color)),
        uirevision=st.session_state.ui_revision # Controls persistence of user interaction
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Info Panel
    if not filtered_df.empty:
        st.markdown("### 🔭 Galaxy Details")
        st.dataframe(filtered_df[['name', 'distance', 'M_V', 'mass_stellar']].head(20), use_container_width=True)

else:
    st.warning("No data available.")
