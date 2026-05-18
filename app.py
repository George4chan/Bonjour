import streamlit as st
import requests
import pandas as pd
import numpy as np
import math
from datetime import datetime
import time
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="Real Flight Radar",
    page_icon="🛸",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: #0a0f0a;
    }
    .radar-title {
        text-align: center;
        margin-bottom: 20px;
    }
    .radar-title h1 {
        color: #00ff00;
        text-shadow: 0 0 10px #00ff00;
        font-family: monospace;
    }
    .info-box {
        background: #0a1a0a;
        border: 1px solid #00ff00;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

class RealFlightRadar:
    def __init__(self):
        self.flights = []
        self.center_lat = 40.7128  # Default: New York
        self.center_lon = -74.0060
        self.range_km = 200
        
    def get_live_flights(self):
        """Get real flight data from OpenSky Network API (free, no API key)"""
        try:
            # OpenSky API - Returns live flight data
            url = "https://opensky-network.org/api/states/all"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                states = data.get('states', [])
                
                flights = []
                for state in states:
                    if state[5] is not None and state[6] is not None:  # Has position
                        lat = state[6]  # Latitude
                        lon = state[5]  # Longitude
                        altitude = state[7]  # Altitude in meters
                        velocity = state[9]  # Speed in m/s
                        callsign = state[1]  # Flight number
                        
                        # Convert to km/h
                        if velocity:
                            speed_kmh = velocity * 3.6
                        else:
                            speed_kmh = 0
                        
                        # Calculate distance from radar center
                        distance = self.calculate_distance(
                            self.center_lat, self.center_lon, lat, lon
                        )
                        
                        # Calculate bearing
                        bearing = self.calculate_bearing(
                            self.center_lat, self.center_lon, lat, lon
                        )
                        
                        # Only include flights within range
                        if distance <= self.range_km:
                            flights.append({
                                'callsign': callsign.strip() if callsign else 'UNKNOWN',
                                'latitude': lat,
                                'longitude': lon,
                                'altitude': altitude if altitude else 0,
                                'speed': speed_kmh,
                                'distance': round(distance, 1),
                                'bearing': bearing,
                                'angle': self.bearing_to_angle(bearing)
                            })
                
                return flights
            else:
                st.warning(f"API returned status {response.status_code}")
                return []
                
        except Exception as e:
            st.error(f"Error fetching flight data: {str(e)}")
            return []
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km (Haversine formula)"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing from point1 to point2"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def bearing_to_angle(self, bearing):
        """Convert bearing (0-360) to radar angle"""
        return bearing

def draw_real_radar(flights, center_lat, center_lon, range_km, scan_angle, width=800, height=800):
    """Draw radar with real flight positions"""
    
    img = Image.new('RGB', (width, height), color=(0, 10, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width // 2, height // 2)
    max_radius = min(width, height) // 2 - 60
    
    # Draw outer circle
    draw.ellipse([center[0] - max_radius, center[1] - max_radius,
                  center[0] + max_radius, center[1] + max_radius],
                 outline=(0, 200, 0), width=3)
    
    # Draw range rings
    for i in range(1, 6):
        radius = int(max_radius * (i / 5))
        draw.ellipse([center[0] - radius, center[1] - radius,
                      center[0] + radius, center[1] + radius],
                     outline=(0, 80, 0), width=1)
        
        range_label = int((i / 5) * range_km)
        draw.text((center[0] + radius - 30, center[1] + 5), f"{range_label}km", fill=(0, 150, 0))
    
    # Draw crosshairs
    draw.line([(center[0], center[1] - max_radius), (center[0], center[1] + max_radius)],
              fill=(0, 60, 0), width=1)
    draw.line([(center[0] - max_radius, center[1]), (center[0] + max_radius, center[1])],
              fill=(0, 60, 0), width=1)
    
    # Draw cardinal directions
    directions = [
        (0, "N", 0), (45, "NE", 45), (90, "E", 90),
        (135, "SE", 135), (180, "S", 180), (225, "SW", 225),
        (270, "W", 270), (315, "NW", 315)
    ]
    
    for angle, label, deg in directions:
        rad = math.radians(angle)
        label_radius = max_radius + 20
        x = center[0] + int(label_radius * math.cos(rad))
        y = center[1] + int(label_radius * math.sin(rad))
        
        if angle == 0:
            x, y = center[0] - 15, center[1] - max_radius - 15
        elif angle == 90:
            x, y = center[0] + max_radius + 10, center[1] - 8
        elif angle == 180:
            x, y = center[0] - 15, center[1] + max_radius + 10
        elif angle == 270:
            x, y = center[0] - max_radius - 40, center[1] - 8
        
        draw.text((x, y), f"{label}", fill=(0, 200, 0))
    
    # Draw real flights
    for flight in flights:
        # Convert distance to pixels
        distance_ratio = flight['distance'] / range_km
        if distance_ratio > 1:
            continue
            
        angle_rad = math.radians(flight['angle'])
        x = center[0] + int(distance_ratio * max_radius * math.cos(angle_rad))
        y = center[1] + int(distance_ratio * max_radius * math.sin(angle_rad))
        
        # Color based on altitude
        if flight['altitude'] < 1000:
            color = (255, 0, 0)  # Red - Low altitude
        elif flight['altitude'] < 3000:
            color = (255, 100, 0)  # Orange - Medium altitude
        else:
            color = (0, 255, 0)  # Green - High altitude
        
        # Draw target
        draw.ellipse([x-6, y-6, x+6, y+6], fill=color, outline=(0, 255, 0))
        draw.text((x+8, y-8), flight['callsign'][:6], fill=(0, 255, 0))
    
    # Draw scanning line
    rad = math.radians(scan_angle)
    scan_x = center[0] + int(max_radius * math.cos(rad))
    scan_y = center[1] + int(max_radius * math.sin(rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Draw center point
    draw.ellipse([center[0]-5, center[1]-5, center[0]+5, center[1]+5], fill=(0, 255, 0))
    draw.text((center[0]-25, center[1]-15), "RADAR", fill=(0, 255, 0))
    
    return img

def main():
    st.markdown("""
    <div class="radar-title">
        <h1>🛸 REAL FLIGHT RADAR SYSTEM</h1>
        <p>Live Air Traffic | Real Data from OpenSky Network | 200km Range</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for location settings
    with st.sidebar:
        st.markdown("## 📍 RADAR LOCATION")
        
        location_option = st.radio(
            "Set Radar Center",
            ["Use My Location", "Select City", "Manual Coordinates"]
        )
        
        if location_option == "Select City":
            city = st.selectbox(
                "City",
                ["New York", "London", "Tokyo", "Dubai", "Singapore", "Los Angeles", "Chicago", "Paris"]
            )
            cities = {
                "New York": (40.7128, -74.0060),
                "London": (51.5074, -0.1278),
                "Tokyo": (35.6762, 139.6503),
                "Dubai": (25.2048, 55.2708),
                "Singapore": (1.3521, 103.8198),
                "Los Angeles": (34.0522, -118.2437),
                "Chicago": (41.8781, -87.6298),
                "Paris": (48.8566, 2.3522)
            }
            lat, lon = cities[city]
            
        elif location_option == "Manual Coordinates":
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitude", value=40.7128, format="%.4f")
            with col2:
                lon = st.number_input("Longitude", value=-74.0060, format="%.4f")
        else:
            # Use my location (default)
            lat = 40.7128
            lon = -74.0060
            st.info("Default: New York City")
        
        st.markdown("---")
        st.markdown("## ⚙️ RADAR SETTINGS")
        
        radar_range = st.slider("Range (km)", 50, 300, 200, 25)
        refresh_rate = st.slider("Refresh Rate (seconds)", 2, 15, 5, 1)
        
        st.markdown("---")
        st.markdown("## ℹ️ DATA SOURCE")
        st.info("""
        **Real Flight Data from OpenSky Network**
        - Live ADS-B data
        - 5000+ aircraft tracked
        - Updates every 5-10 seconds
        - Free & open API
        
        **Shows real aircraft:**
        - Commercial flights
        - Private jets
        - Cargo aircraft
        - Some military (limited)
        """)
        
        if st.button("🔄 FORCE REFRESH", use_container_width=True):
            st.session_state.last_refresh = 0
    
    # Initialize radar
    if 'radar' not in st.session_state:
        st.session_state.radar = RealFlightRadar()
        st.session_state.scan_angle = 0
        st.session_state.last_refresh = 0
        st.session_state.flights = []
    
    # Update radar position
    st.session_state.radar.center_lat = lat
    st.session_state.radar.center_lon = lon
    st.session_state.radar.range_km = radar_range
    
    # Refresh flight data
    current_time = time.time()
    if current_time - st.session_state.last_refresh >= refresh_rate:
        with st.spinner("Fetching live flight data..."):
            st.session_state.flights = st.session_state.radar.get_live_flights()
            st.session_state.last_refresh = current_time
    
    # Update scan angle
    st.session_state.scan_angle += 4
    if st.session_state.scan_angle >= 360:
        st.session_state.scan_angle = 0
    
    # Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Draw radar
        radar_img = draw_real_radar(
            st.session_state.flights,
            lat, lon, radar_range,
            st.session_state.scan_angle
        )
        st.image(radar_img, use_container_width=True)
        
        # Status metrics
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("RADAR STATUS", "🟢 ACTIVE")
        mcol2.metric("REAL AIRCRAFT", len(st.session_state.flights))
        mcol3.metric("RANGE", f"{radar_range} km")
        mcol4.metric("LAST UPDATE", f"{refresh_rate}s")
    
    with col2:
        st.markdown("## ✈️ REAL AIRCRAFT DETECTED")
        
        if st.session_state.flights:
            # Sort by distance
            sorted_flights = sorted(st.session_state.flights, key=lambda x: x['distance'])
            
            for flight in sorted_flights[:10]:
                # Format bearing
                bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                           'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                bearing_idx = int((flight['bearing'] + 11.25) / 22.5) % 16
                bearing_str = bearings[bearing_idx]
                
                # Color based on distance
                if flight['distance'] < 30:
                    color = "#ff0000"
                    threat = "🔴"
                elif flight['distance'] < 80:
                    color = "#ffaa00"
                    threat = "🟠"
                else:
                    color = "#00ff00"
                    threat = "🟢"
                
                st.markdown(f"""
                <div style="background: #0a0a0a; border-left: 4px solid {color}; 
                            border-radius: 5px; padding: 8px; margin: 5px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{threat} {flight['callsign']}</b>
                        <span style="color: #00ff00;">{flight['distance']} km</span>
                    </div>
                    <div style="font-size: 11px; color: #00aa00;">
                        Bearing: {bearing_str} ({flight['bearing']:.0f}°) | Alt: {flight['altitude']:.0f} m<br>
                        Speed: {flight['speed']:.0f} km/h
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(sorted_flights) > 10:
                st.caption(f"+ {len(sorted_flights) - 10} more aircraft")
        else:
            st.warning("No aircraft detected within radar range")
            st.caption("Try increasing range or changing location")
        
        # Stats
        if st.session_state.flights:
            st.markdown("## 📊 AIR TRAFFIC STATS")
            
            avg_alt = sum(f['altitude'] for f in st.session_state.flights) / len(st.session_state.flights)
            avg_dist = sum(f['distance'] for f in st.session_state.flights) / len(st.session_state.flights)
            
            col1, col2 = st.columns(2)
            col1.metric("Avg Altitude", f"{avg_alt:.0f} m")
            col2.metric("Avg Distance", f"{avg_dist:.0f} km")
            
            # Closest aircraft
            closest = min(st.session_state.flights, key=lambda x: x['distance'])
            st.info(f"**Closest Aircraft:** {closest['callsign']}\n{closest['distance']} km at {closest['bearing']:.0f}°")
    
    # Auto-refresh
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()
