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
    .flight-card {
        background: #0a0a0a;
        border-left: 4px solid #00ff00;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

class RealFlightRadar:
    def __init__(self):
        self.flights = []
        self.center_lat = 40.7128
        self.center_lon = -74.0060
        self.range_km = 200
        self.last_error = None
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km"""
        R = 6371
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
    
    def get_live_flights(self):
        """Get real flight data from OpenSky Network API"""
        try:
            # Use a timeout to prevent hanging
            url = "https://opensky-network.org/api/states/all"
            response = requests.get(url, timeout=15, headers={'User-Agent': 'Streamlit Radar App'})
            
            if response.status_code == 200:
                data = response.json()
                states = data.get('states', [])
                
                flights = []
                for state in states:
                    try:
                        # Extract flight data
                        callsign = state[1] if state[1] else None
                        lon = state[5]  # Longitude
                        lat = state[6]  # Latitude
                        altitude = state[7]  # Altitude in meters
                        velocity = state[9]  # Speed in m/s
                        
                        # Skip if no position
                        if lat is None or lon is None:
                            continue
                        
                        # Convert speed to km/h
                        if velocity:
                            speed_kmh = velocity * 3.6
                        else:
                            speed_kmh = 0
                        
                        # Calculate distance from radar center
                        distance = self.calculate_distance(
                            self.center_lat, self.center_lon, lat, lon
                        )
                        
                        # Only include flights within range
                        if distance <= self.range_km:
                            # Calculate bearing
                            bearing = self.calculate_bearing(
                                self.center_lat, self.center_lon, lat, lon
                            )
                            
                            # Clean up callsign
                            if callsign:
                                callsign = callsign.strip()
                            else:
                                callsign = f"FL{len(flights)+1}"
                            
                            flights.append({
                                'callsign': callsign,
                                'latitude': lat,
                                'longitude': lon,
                                'altitude': altitude if altitude else 0,
                                'speed': round(speed_kmh, 1),
                                'distance': round(distance, 1),
                                'bearing': round(bearing, 1),
                                'angle': bearing
                            })
                    except Exception as e:
                        continue
                
                self.last_error = None
                return flights
            else:
                self.last_error = f"API returned {response.status_code}"
                return []
                
        except requests.exceptions.Timeout:
            self.last_error = "Request timeout - API may be slow"
            return []
        except requests.exceptions.ConnectionError:
            self.last_error = "Connection error - Check internet"
            return []
        except Exception as e:
            self.last_error = str(e)
            return []
    
    def get_sample_flights(self):
        """Return sample flight data for demonstration"""
        return [
            {'callsign': 'UAL123', 'distance': 25.3, 'bearing': 45.0, 'angle': 45.0, 'altitude': 3500, 'speed': 850},
            {'callsign': 'DAL456', 'distance': 52.1, 'bearing': 120.0, 'angle': 120.0, 'altitude': 5200, 'speed': 780},
            {'callsign': 'AAL789', 'distance': 87.4, 'bearing': 210.0, 'angle': 210.0, 'altitude': 2800, 'speed': 650},
            {'callsign': 'SWA234', 'distance': 142.6, 'bearing': 310.0, 'angle': 310.0, 'altitude': 4100, 'speed': 720},
            {'callsign': 'JBU567', 'distance': 175.2, 'bearing': 15.0, 'angle': 15.0, 'altitude': 3800, 'speed': 800},
        ]

def draw_radar(flights, center_lat, center_lon, range_km, scan_angle, width=800, height=800):
    """Draw radar display"""
    
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
    directions = [(0, "N"), (45, "NE"), (90, "E"), (135, "SE"), 
                  (180, "S"), (225, "SW"), (270, "W"), (315, "NW")]
    
    for angle, label in directions:
        rad = math.radians(angle)
        x = center[0] + int((max_radius + 25) * math.cos(rad))
        y = center[1] + int((max_radius + 25) * math.sin(rad))
        
        if angle == 0:
            x, y = center[0] - 10, center[1] - max_radius - 15
        elif angle == 90:
            x, y = center[0] + max_radius + 15, center[1] - 8
        elif angle == 180:
            x, y = center[0] - 10, center[1] + max_radius + 10
        elif angle == 270:
            x, y = center[0] - max_radius - 35, center[1] - 8
        
        draw.text((x, y), label, fill=(0, 200, 0))
    
    # Draw flights
    for flight in flights:
        distance_ratio = flight['distance'] / range_km
        if distance_ratio > 1:
            continue
            
        angle_rad = math.radians(flight['angle'])
        x = center[0] + int(distance_ratio * max_radius * math.cos(angle_rad))
        y = center[1] + int(distance_ratio * max_radius * math.sin(angle_rad))
        
        # Color based on distance
        if flight['distance'] < 50:
            color = (255, 0, 0)
            size = 8
        elif flight['distance'] < 100:
            color = (255, 100, 0)
            size = 7
        else:
            color = (0, 255, 0)
            size = 6
        
        # Draw target
        draw.ellipse([x-size, y-size, x+size, y+size], fill=color, outline=(0, 255, 0))
        draw.text((x+8, y-8), flight['callsign'][:6], fill=(0, 255, 0))
    
    # Draw scanning line
    rad = math.radians(scan_angle)
    scan_x = center[0] + int(max_radius * math.cos(rad))
    scan_y = center[1] + int(max_radius * math.sin(rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Draw center
    draw.ellipse([center[0]-5, center[1]-5, center[0]+5, center[1]+5], fill=(0, 255, 0))
    draw.text((center[0]-20, center[1]-15), "RADAR", fill=(0, 255, 0))
    
    return img

def main():
    st.markdown("""
    <div class="radar-title">
        <h1>🛸 REAL FLIGHT RADAR SYSTEM</h1>
        <p>Live Air Traffic | Real ADS-B Data | 200km Range</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📍 RADAR LOCATION")
        
        location_option = st.radio(
            "Select Location",
            ["New York (JFK)", "London (LHR)", "Tokyo (HND)", "Dubai (DXB)", "Los Angeles (LAX)"]
        )
        
        locations = {
            "New York (JFK)": (40.6413, -73.7781),
            "London (LHR)": (51.4700, -0.4543),
            "Tokyo (HND)": (35.5494, 139.7798),
            "Dubai (DXB)": (25.2528, 55.3644),
            "Los Angeles (LAX)": (33.9416, -118.4085)
        }
        
        lat, lon = locations[location_option]
        
        st.markdown("---")
        st.markdown("## ⚙️ RADAR SETTINGS")
        
        radar_range = st.slider("Detection Range (km)", 50, 300, 200, 25)
        use_real_data = st.checkbox("Use Real Flight Data", value=True, help="Toggle between real data and demo")
        
        st.markdown("---")
        st.markdown("## ℹ️ DATA SOURCE")
        st.info("""
        **Real Data from OpenSky Network**
        - Live ADS-B aircraft transponder data
        - Updates every 10 seconds
        - Shows real commercial & private flights
        - Free public API
        
        **Toggle off for demo mode** if API is unavailable
        """)
    
    # Initialize session state
    if 'radar' not in st.session_state:
        st.session_state.radar = RealFlightRadar()
        st.session_state.scan_angle = 0
        st.session_state.last_refresh = 0
        st.session_state.flights = []
        st.session_state.api_error = False
    
    # Update radar settings
    st.session_state.radar.center_lat = lat
    st.session_state.radar.center_lon = lon
    st.session_state.radar.range_km = radar_range
    
    # Get flight data
    current_time = time.time()
    if current_time - st.session_state.last_refresh >= 10:  # Refresh every 10 seconds
        if use_real_data:
            with st.spinner("Fetching live flight data from OpenSky Network..."):
                flights = st.session_state.radar.get_live_flights()
                if flights:
                    st.session_state.flights = flights
                    st.session_state.api_error = False
                else:
                    # Use sample data if real data fails
                    st.session_state.flights = st.session_state.radar.get_sample_flights()
                    if st.session_state.radar.last_error:
                        st.session_state.api_error = st.session_state.radar.last_error
        else:
            # Demo mode - use sample data
            st.session_state.flights = st.session_state.radar.get_sample_flights()
        
        st.session_state.last_refresh = current_time
    
    # Update scan angle
    st.session_state.scan_angle += 4
    if st.session_state.scan_angle >= 360:
        st.session_state.scan_angle = 0
    
    # Show API error if any
    if st.session_state.api_error and use_real_data:
        st.warning(f"⚠️ Using demo data: {st.session_state.api_error}")
    
    # Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Draw radar
        radar_img = draw_radar(
            st.session_state.flights,
            lat, lon, radar_range,
            st.session_state.scan_angle
        )
        st.image(radar_img, use_container_width=True)
        
        # Status metrics
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("RADAR STATUS", "🟢 ACTIVE")
        mcol2.metric("AIRCRAFT", len(st.session_state.flights))
        mcol3.metric("RANGE", f"{radar_range} km")
        mcol4.metric("DATA SOURCE", "LIVE" if use_real_data and not st.session_state.api_error else "DEMO")
    
    with col2:
        st.markdown("## ✈️ AIRCRAFT DETECTED")
        
        if st.session_state.flights:
            # Sort by distance
            sorted_flights = sorted(st.session_state.flights, key=lambda x: x['distance'])
            
            for flight in sorted_flights[:12]:
                # Get bearing text
                bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                           'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                bearing_idx = int((flight['bearing'] + 11.25) / 22.5) % 16
                bearing_str = bearings[bearing_idx]
                
                # Color coding
                if flight['distance'] < 50:
                    color = "#ff0000"
                    threat = "🔴"
                elif flight['distance'] < 100:
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
                        Bearing: {bearing_str} ({flight['bearing']:.0f}°)<br>
                        Alt: {flight['altitude']:.0f} m | Speed: {flight['speed']:.0f} km/h
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(sorted_flights) > 12:
                st.caption(f"+ {len(sorted_flights) - 12} more aircraft")
        else:
            st.info("No aircraft detected in range")
            st.caption("Try increasing range or changing location")
        
        # Statistics
        if st.session_state.flights:
            st.markdown("## 📊 AIR TRAFFIC STATS")
            
            distances = [f['distance'] for f in st.session_state.flights]
            altitudes = [f['altitude'] for f in st.session_state.flights]
            
            col1, col2 = st.columns(2)
            col1.metric("Avg Distance", f"{sum(distances)/len(distances):.0f} km")
            col2.metric("Avg Altitude", f"{sum(altitudes)/len(altitudes):.0f} m")
            
            # Closest aircraft
            closest = min(st.session_state.flights, key=lambda x: x['distance'])
            st.info(f"**✈️ Closest:** {closest['callsign']}\n{closest['distance']} km at {closest['bearing']:.0f}°")
            
            # Update time
            st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    # Auto-refresh
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()
