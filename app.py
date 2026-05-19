import streamlit as st
import requests
import math
from datetime import datetime
import time
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

st.set_page_config(
    page_title="Haiti 360° Radar System",
    page_icon="🇭🇹",
    layout="wide"
)

# Military Green Theme
st.markdown("""
<style>
    .stApp { background: #050805; }
    .main-title { text-align: center; margin-bottom: 20px; }
    .main-title h1 { color: #00ff00; font-family: 'Courier New', monospace; text-shadow: 0 0 10px #00ff00; }
    .target-card {
        background: #0a150a;
        border-left: 3px solid #00ff00;
        padding: 8px;
        margin: 5px 0;
        border-radius: 3px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HAITI COORDINATES - REAL AIRSPACE
# ============================================================
RADAR_CENTER = {"lat": 18.5754, "lon": -72.2947}  # PAP Airport, Haiti
RANGE_KM = 200

class HaitiRealRadar:
    def __init__(self):
        self.center_lat = RADAR_CENTER["lat"]
        self.center_lon = RADAR_CENTER["lon"]
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in km - REAL MATH"""
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
    
    def fetch_real_flights(self):
        """Get REAL aircraft from OpenSky Network API"""
        try:
            # Bounding box for Haiti region (17N-20N, 75W-71W)
            url = "https://opensky-network.org/api/states/all"
            response = requests.get(url, timeout=12, headers={'User-Agent': 'HaitiRadar/1.0'})
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            states = data.get('states', [])
            
            flights = []
            for state in states:
                try:
                    callsign = state[1].strip() if state[1] else None
                    lon = state[5]
                    lat = state[6]
                    altitude = state[7]
                    velocity = state[9]
                    
                    if lat is None or lon is None:
                        continue
                    
                    # Check if within Haiti region
                    if 17.5 <= lat <= 20.0 and -75.0 <= lon <= -71.0:
                        distance = self.haversine_distance(self.center_lat, self.center_lon, lat, lon)
                        
                        if distance <= RANGE_KM:
                            speed_kmh = (velocity * 3.6) if velocity else 0
                            bearing = self.calculate_bearing(self.center_lat, self.center_lon, lat, lon)
                            
                            # Determine aircraft type (rough estimate)
                            if altitude and altitude < 3000:
                                aircraft_type = "HELICOPTER"
                            elif altitude and altitude < 8000:
                                aircraft_type = "SMALL AIRCRAFT"
                            else:
                                aircraft_type = "COMMERCIAL JET"
                            
                            flights.append({
                                'callsign': callsign if callsign else f"FL{len(flights)+1:03d}",
                                'distance': round(distance, 1),
                                'bearing': round(bearing, 1),
                                'angle': bearing,
                                'altitude': round(altitude) if altitude else 0,
                                'speed': round(speed_kmh, 1),
                                'type': aircraft_type
                            })
                except:
                    continue
            
            return flights
        except Exception as e:
            st.warning(f"API Connection: {str(e)[:50]}")
            return []

# ============================================================
# RADAR DISPLAY - EXACT MATCH TO CHATGPT IMAGE
# ============================================================
def draw_radar_image(flights, scan_angle, width=800, height=800):
    """Draw the 360° radar exactly like the ChatGPT image"""
    
    img = Image.new('RGB', (width, height), color=(0, 8, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width // 2, height // 2)
    max_radius = min(width, height) // 2 - 50
    
    # ===== OUTER CIRCLE (360° BORDER) =====
    draw.ellipse([center[0] - max_radius, center[1] - max_radius,
                  center[0] + max_radius, center[1] + max_radius],
                 outline=(0, 180, 0), width=3)
    
    # ===== RANGE RINGS (50km, 100km, 150km, 200km) =====
    rings = [50, 100, 150, 200]
    for i, ring_km in enumerate(rings):
        radius = int(max_radius * (ring_km / RANGE_KM))
        draw.ellipse([center[0] - radius, center[1] - radius,
                      center[0] + radius, center[1] + radius],
                     outline=(0, 70, 0), width=1)
        # Ring label
        draw.text((center[0] + radius - 25, center[1] + 5), f"{ring_km}KM", fill=(0, 120, 0))
    
    # ===== CROSSHAIRS (Radial lines) =====
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = center[0] + int(max_radius * math.cos(rad))
        y = center[1] + int(max_radius * math.sin(rad))
        draw.line([center, (x, y)], fill=(0, 50, 0), width=1)
    
    # ===== CARDINAL & INTERCARDINAL LABELS (like ChatGPT image) =====
    labels = [
        (0, "0°", "NORTH"), (30, "30°", ""), (60, "60°", ""),
        (90, "90°", "EAST"), (120, "120°", ""), (150, "150°", ""),
        (180, "180°", "SOUTH"), (210, "210°", ""), (240, "240°", ""),
        (270, "270°", "WEST"), (300, "300°", ""), (330, "330°", "")
    ]
    
    for angle, deg_label, cardinal in labels:
        rad = math.radians(angle)
        label_radius = max_radius + 20
        x = center[0] + int(label_radius * math.cos(rad))
        y = center[1] + int(label_radius * math.sin(rad))
        
        # Adjust positions for cardinals
        if angle == 0:
            x, y = center[0] - 25, center[1] - max_radius - 15
        elif angle == 90:
            x, y = center[0] + max_radius + 15, center[1] - 8
        elif angle == 180:
            x, y = center[0] - 30, center[1] + max_radius + 10
        elif angle == 270:
            x, y = center[0] - max_radius - 45, center[1] - 8
        
        draw.text((x, y), deg_label, fill=(0, 180, 0))
        if cardinal:
            draw.text((x, y + 15), cardinal, fill=(0, 200, 0))
    
    # ===== DRAW REAL TARGETS =====
    for i, flight in enumerate(flights):
        dist_ratio = flight['distance'] / RANGE_KM
        if dist_ratio > 1:
            continue
        
        angle_rad = math.radians(flight['angle'])
        x = center[0] + int(dist_ratio * max_radius * math.cos(angle_rad))
        y = center[1] + int(dist_ratio * max_radius * math.sin(angle_rad))
        
        # Color by type
        if flight['type'] == "HELICOPTER":
            color = (255, 100, 0)
        elif flight['type'] == "SMALL AIRCRAFT":
            color = (255, 200, 0)
        else:
            color = (0, 255, 0)
        
        # Draw target blip
        draw.ellipse([x-7, y-7, x+7, y+7], fill=color, outline=(0, 255, 0), width=1)
        
        # Label like "TARGET01" format from ChatGPT image
        target_label = f"TARGET{flight.get('index', i+1):02d}"
        draw.text((x + 10, y - 12), target_label, fill=(0, 255, 0))
        
        # Distance label below
        draw.text((x - 20, y + 10), f"{flight['distance']}KM", fill=(0, 200, 0))
    
    # ===== ROTATING SCAN LINE =====
    scan_rad = math.radians(scan_angle)
    scan_x = center[0] + int(max_radius * math.cos(scan_rad))
    scan_y = center[1] + int(max_radius * math.sin(scan_rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Scan head glow
    for r in range(6, 0, -1):
        draw.ellipse([scan_x - r, scan_y - r, scan_x + r, scan_y + r], 
                     fill=(0, 255, 0), outline=(0, 255, 0))
    
    # Center dot
    draw.ellipse([center[0] - 8, center[1] - 8, center[0] + 8, center[1] + 8], 
                 fill=(0, 50, 0), outline=(0, 150, 0))
    draw.ellipse([center[0] - 3, center[1] - 3, center[0] + 3, center[1] + 3], 
                 fill=(0, 255, 0))
    
    return img

# ============================================================
# MAIN APP
# ============================================================
def main():
    st.markdown("""
    <div class="main-title">
        <h1>🇭🇹 360° REAL HAITI RADAR SYSTEM</h1>
        <p style="color: #00aa00;">REAL ADS-B DATA | PORT-AU-PRINCE (PAP) | 200KM RANGE</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 RADAR STATION")
        st.markdown("**Location:** Port-au-Prince, Haiti")
        st.markdown("**Airport:** Toussaint Louverture (PAP)")
        st.markdown("**Coordinates:** 18.5754°N, 72.2947°W")
        st.markdown("**Range:** 200km")
        
        st.markdown("---")
        st.markdown("## ⚠️ CAPABILITIES")
        st.markdown("✅ **REAL AIRPLANES** - Live ADS-B data")
        st.markdown("✅ **REAL HELICOPTERS** - When transponder equipped")
        st.markdown("❌ **CONSUMER DRONES** - Not detectable via radar")
        st.markdown("")
        st.markdown("*Drones require physical RF sensors or military radar*")
        
        st.markdown("---")
        st.markdown(f"**Last Scan:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Initialize
    if 'radar' not in st.session_state:
        st.session_state.radar = HaitiRealRadar()
        st.session_state.scan_angle = 0
        st.session_state.last_fetch = 0
        st.session_state.flights = []
    
    # Fetch real data every 15 seconds
    current_time = time.time()
    if current_time - st.session_state.last_fetch >= 15:
        with st.spinner("🛰️ Scanning Haitian airspace for REAL aircraft..."):
            st.session_state.flights = st.session_state.radar.fetch_real_flights()
            # Add index for display
            for idx, f in enumerate(st.session_state.flights):
                f['index'] = idx + 1
            st.session_state.last_fetch = current_time
    
    # Update scan animation
    st.session_state.scan_angle += 3
    if st.session_state.scan_angle >= 360:
        st.session_state.scan_angle = 0
    
    # Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Draw radar
        radar_img = draw_radar_image(st.session_state.flights, st.session_state.scan_angle)
        st.image(radar_img, use_container_width=True)
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🟢 RADAR", "ACTIVE")
        m2.metric("✈️ AIRCRAFT", len(st.session_state.flights))
        m3.metric("📡 RANGE", "200 KM")
        m4.metric("🔄 UPDATE", "15 SEC")
    
    with col2:
        st.markdown("## 🎯 REAL TARGETS")
        
        if st.session_state.flights:
            for flight in st.session_state.flights[:10]:
                # Determine threat icon
                if flight['type'] == "HELICOPTER":
                    icon = "🚁"
                elif flight['type'] == "SMALL AIRCRAFT":
                    icon = "🛩️"
                else:
                    icon = "✈️"
                
                # Bearing to direction
                bearings = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
                idx = int((flight['bearing'] + 22.5) / 45) % 8
                direction = bearings[idx]
                
                st.markdown(f"""
                <div class="target-card">
                    <b>{icon} {flight['callsign']}</b><br>
                    📍 <b>{flight['distance']} KM</b> | {direction} ({flight['bearing']:.0f}°)<br>
                    📈 {flight['altitude']:,} M | ⚡ {flight['speed']} KM/H<br>
                    🏷️ {flight['type']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🚫 NO AIRCRAFT DETECTED IN HAITIAN AIRSPACE")
            st.caption("The sky may be quiet or aircraft without transponders")
        
        # Stats
        if st.session_state.flights:
            st.markdown("## 📊 AIRSPACE SUMMARY")
            helicopters = [f for f in st.session_state.flights if f['type'] == "HELICOPTER"]
            jets = [f for f in st.session_state.flights if f['type'] == "COMMERCIAL JET"]
            
            st.metric("🚁 Helicopters", len(helicopters))
            st.metric("✈️ Commercial Jets", len(jets))
            
            if st.session_state.flights:
                closest = min(st.session_state.flights, key=lambda x: x['distance'])
                st.warning(f"⚠️ CLOSEST: {closest['callsign']} at {closest['distance']} KM")
    
    # Auto-refresh for animation
    time.sleep(0.08)
    st.rerun()

if __name__ == "__main__":
    main()
