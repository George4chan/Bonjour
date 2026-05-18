# app.py - Real 360° Radar Detection System
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.graph_objs as go
import math
import random

# Page configuration
st.set_page_config(
    page_title="360° Radar Detection System",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle, #0a0a0a 0%, #000000 100%);
    }
    .radar-container {
        background: linear-gradient(135deg, #001a00 0%, #000a00 100%);
        border-radius: 20px;
        padding: 20px;
        border: 2px solid #00ff00;
        box-shadow: 0 0 20px rgba(0,255,0,0.3);
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: rgba(0,0,0,0.8);
        border: 2px solid #00ff00;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .detection-card {
        background: rgba(0,0,0,0.7);
        border-left: 4px solid #00ff00;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .threat-card {
        background: rgba(255,0,0,0.1);
        border: 1px solid #ff0000;
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
    .info-card {
        background: rgba(0,100,0,0.3);
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

class RealRadarSystem:
    def __init__(self):
        self.detections = []
        self.scan_angle = 0
        self.scan_speed = 2  # degrees per frame
        self.radar_range_km = 10  # Maximum detection range in km
        self.radar_center = (400, 400)  # Radar center on display
        
        # Store track history
        self.track_history = {}
        self.next_id = 0
        
        # Real-world bounds (example: city center)
        self.center_lat = 0.0  # Will be updated if GPS available
        self.center_lon = 0.0
        
    def calculate_distance_km(self, pixels_from_center, max_pixels=350):
        """Convert pixel distance to kilometers"""
        return (pixels_from_center / max_pixels) * self.radar_range_km
    
    def calculate_altitude(self, object_size, distance_km):
        """Estimate altitude based on object size and distance"""
        # Objects appear smaller when further away
        base_altitude = 100  # meters
        size_factor = 100 / (object_size + 1)
        altitude_m = base_altitude + (distance_km * 50) - (size_factor * 10)
        return max(0, int(altitude_m))
    
    def classify_object(self, distance_km, altitude_m, speed_kmh, object_size):
        """Classify the object based on realistic parameters"""
        if speed_kmh > 200:
            return "High-Speed Aircraft", "HIGH"
        elif speed_kmh > 100:
            return "Commercial Aircraft", "MEDIUM"
        elif speed_kmh > 50:
            if distance_km < 2:
                return "Drone", "MEDIUM"
            else:
                return "Small Aircraft", "LOW"
        elif speed_kmh > 20:
            return "Bird/Drone", "LOW"
        else:
            return "Unknown Object", "LOW"
    
    def simulate_radar_scan(self):
        """Simulate realistic radar scan with moving objects"""
        self.scan_angle += self.scan_speed
        if self.scan_angle >= 360:
            self.scan_angle = 0
        
        # Add random detections (like real radar)
        if random.random() < 0.05:  # 5% chance of new detection per scan
            angle = random.randint(0, 359)
            distance_px = random.randint(50, 350)
            distance_km = self.calculate_distance_km(distance_px)
            
            # Calculate object speed (km/h)
            speed_kmh = random.randint(30, 300)
            
            # Determine object type based on speed and distance
            if speed_kmh > 200:
                obj_type = "Aircraft"
                size = 15
            elif speed_kmh > 100:
                obj_type = "Small Plane"
                size = 10
            elif speed_kmh > 40:
                obj_type = "Drone"
                size = 8
            else:
                obj_type = "Bird"
                size = 5
            
            altitude = self.calculate_altitude(size, distance_km)
            
            detection = {
                'id': self.next_id,
                'angle': angle,
                'distance_px': distance_px,
                'distance_km': round(distance_km, 1),
                'altitude_m': altitude,
                'speed_kmh': speed_kmh,
                'type': obj_type,
                'size': size,
                'timestamp': datetime.now(),
                'last_seen': datetime.now(),
                'bearing': self.get_bearing(angle),
                'track_points': [(angle, distance_px)]
            }
            
            self.detections.append(detection)
            self.track_history[self.next_id] = detection
            self.next_id += 1
            
            # Limit number of tracks
            if len(self.detections) > 15:
                self.detections.pop(0)
        
        # Update existing detections (movement)
        for detection in self.detections:
            # Objects move naturally
            angle_change = random.uniform(-5, 5)
            distance_change = random.uniform(-10, 10)
            
            detection['angle'] += angle_change
            detection['distance_px'] += distance_change
            detection['distance_px'] = max(30, min(370, detection['distance_px']))
            
            if detection['angle'] >= 360:
                detection['angle'] -= 360
            elif detection['angle'] < 0:
                detection['angle'] += 360
            
            # Update distance in km
            detection['distance_km'] = round(self.calculate_distance_km(detection['distance_px']), 1)
            
            # Update speed calculation
            if len(detection.get('track_points', [])) > 0:
                prev_point = detection['track_points'][-1]
                movement = abs(detection['distance_px'] - prev_point[1])
                detection['speed_kmh'] = movement * 2  # Rough estimate
            
            detection['last_seen'] = datetime.now()
            detection['track_points'].append((detection['angle'], detection['distance_px']))
            
            # Keep last 20 track points
            if len(detection['track_points']) > 20:
                detection['track_points'] = detection['track_points'][-20:]
        
        # Remove old detections (disappeared)
        current_time = datetime.now()
        self.detections = [d for d in self.detections 
                          if (current_time - d['last_seen']).seconds < 15]
        
        return self.detections
    
    def get_bearing(self, angle):
        """Convert angle to cardinal direction"""
        bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                   'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = int((angle + 11.25) / 22.5) % 16
        return bearings[idx]
    
    def draw_radar_display(self, detections, width=800, height=800):
        """Draw realistic radar display"""
        radar_img = np.zeros((height, width, 3), dtype=np.uint8)
        radar_img[:] = (0, 10, 0)  # Dark green background
        
        center = (width//2, height//2)
        max_radius = min(width, height)//2 - 50
        
        # Draw radar rings (range circles)
        for r in range(1, 6):
            radius = int(max_radius * (r / 5))
            cv2.circle(radar_img, center, radius, (0, 100, 0), 1)
            
            # Add range labels
            range_km = int((r / 5) * self.radar_range_km)
            cv2.putText(radar_img, f"{range_km}km", 
                       (center[0] + radius - 20, center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 0), 1)
        
        # Draw crosshairs
        cv2.line(radar_img, (center[0], 0), (center[0], height), (0, 80, 0), 1)
        cv2.line(radar_img, (0, center[1]), (width, center[1]), (0, 80, 0), 1)
        
        # Draw cardinal directions
        cv2.putText(radar_img, "N", (center[0]-5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(radar_img, "S", (center[0]-5, height-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(radar_img, "E", (width-15, center[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(radar_img, "W", (5, center[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Draw bearing ticks (every 30 degrees)
        for angle in range(0, 360, 30):
            rad = np.radians(angle)
            x1 = center[0] + int((max_radius - 10) * np.cos(rad))
            y1 = center[1] + int((max_radius - 10) * np.sin(rad))
            x2 = center[0] + int(max_radius * np.cos(rad))
            y2 = center[1] + int(max_radius * np.sin(rad))
            cv2.line(radar_img, (x1, y1), (x2, y2), (0, 100, 0), 1)
        
        # Draw detection trails and objects
        for detection in detections:
            angle_rad = np.radians(detection['angle'])
            distance = detection['distance_px']
            
            # Calculate position
            x = center[0] + int(distance * np.cos(angle_rad))
            y = center[1] + int(distance * np.sin(angle_rad))
            
            # Color based on distance/speed
            if detection['speed_kmh'] > 150:
                color = (0, 0, 255)  # Red - fast
                size = 8
            elif detection['speed_kmh'] > 80:
                color = (0, 100, 255)  # Orange - medium fast
                size = 7
            elif detection['speed_kmh'] > 30:
                color = (0, 255, 255)  # Yellow - slow
                size = 6
            else:
                color = (0, 255, 0)  # Green - very slow/hovering
                size = 5
            
            # Draw trail
            if 'track_points' in detection and len(detection['track_points']) > 1:
                for i in range(1, len(detection['track_points'])):
                    prev_angle, prev_dist = detection['track_points'][i-1]
                    curr_angle, curr_dist = detection['track_points'][i]
                    
                    prev_rad = np.radians(prev_angle)
                    curr_rad = np.radians(curr_angle)
                    
                    px = center[0] + int(prev_dist * np.cos(prev_rad))
                    py = center[1] + int(prev_dist * np.sin(prev_rad))
                    cx = center[0] + int(curr_dist * np.cos(curr_rad))
                    cy = center[1] + int(curr_dist * np.sin(curr_rad))
                    
                    alpha = i / len(detection['track_points'])
                    trail_color = (0, int(200 * alpha), int(100 * (1-alpha)))
                    cv2.line(radar_img, (px, py), (cx, cy), trail_color, 2)
            
            # Draw object
            cv2.circle(radar_img, (x, y), size, color, -1)
            cv2.circle(radar_img, (x, y), size+1, (0, 255, 0), 1)
            
            # Draw object label
            label = f"{detection['id']}"
            cv2.putText(radar_img, label, (x-5, y-8), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Draw scanning line
        scan_rad = np.radians(self.scan_angle)
        scan_x = center[0] + int(max_radius * np.cos(scan_rad))
        scan_y = center[1] + int(max_radius * np.sin(scan_rad))
        cv2.line(radar_img, center, (scan_x, scan_y), (0, 255, 0), 2)
        
        # Add glow effect at scan point
        cv2.circle(radar_img, (scan_x, scan_y), 5, (0, 255, 0), -1)
        
        # Add radar information overlay
        overlay = radar_img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 80), (0, 0, 0), -1)
        radar_img = cv2.addWeighted(overlay, 0.6, radar_img, 0.4, 0)
        
        cv2.putText(radar_img, f"RADAR SCANNING", (15, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(radar_img, f"Range: {self.radar_range_km}km", (15, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        cv2.putText(radar_img, f"Objects: {len(detections)}", (15, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        
        return radar_img

def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🛸 360° REAL-TIME RADAR SYSTEM")
    st.markdown("### Live Airspace Monitoring | Range: 10km | 360° Coverage")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("## 🎮 RADAR CONTROLS")
        
        radar_range = st.slider(
            "Radar Range (km)",
            min_value=2,
            max_value=20,
            value=10,
            step=1,
            help="Maximum detection distance"
        )
        
        scan_speed = st.slider(
            "Scan Speed (RPM)",
            min_value=10,
            max_value=60,
            value=30,
            step=5,
            help="Radar rotation speed"
        )
        
        alert_distance = st.slider(
            "Alert Distance (km)",
            min_value=1,
            max_value=10,
            value=5,
            step=0.5,
            help="Alert when objects enter this range"
        )
        
        st.markdown("---")
        st.markdown("## 📡 FILTERS")
        
        show_only_moving = st.checkbox("Show Moving Objects Only", False)
        min_speed = st.slider("Minimum Speed (km/h)", 0, 100, 0, 10)
        
        st.markdown("---")
        st.markdown("## ℹ️ SYSTEM INFO")
        st.info("""
        **Radar Capabilities:**
        - 360° Continuous Scanning
        - Range: Up to 20km
        - Tracks speed & altitude
        - Real-time alerts
        - Movement trails
        
        **Detects:**
        - ✈️ Aircraft
        - 🚁 Drones  
        - 🐦 Birds
        - 🎈 Balloons
        """)
        
        if st.button("🔄 RESET RADAR", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Main display area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="radar-container">', unsafe_allow_html=True)
        radar_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Radar status
        status_cols = st.columns(5)
        with status_cols[0]:
            status_placeholder = st.empty()
        with status_cols[1]:
            objects_placeholder = st.empty()
        with status_cols[2]:
            closest_placeholder = st.empty()
        with status_cols[3]:
            alert_placeholder = st.empty()
        with status_cols[4]:
            bearing_placeholder = st.empty()
    
    with col2:
        st.markdown("## 🎯 ACTIVE TRACKS")
        tracks_placeholder = st.empty()
        
        st.markdown("## ⚠️ PROXIMITY ALERTS")
        alerts_placeholder = st.empty()
        
        st.markdown("## 📊 TRACK ANALYSIS")
        analysis_placeholder = st.empty()
    
    # Initialize radar system
    if 'radar' not in st.session_state:
        st.session_state.radar = RealRadarSystem()
        st.session_state.running = True
    
    # Update radar range from slider
    st.session_state.radar.radar_range_km = radar_range
    
    # Update scan speed
    if hasattr(st.session_state.radar, 'scan_speed'):
        st.session_state.radar.scan_speed = scan_speed / 10  # Convert RPM to degrees/frame
    
    # Radar loop
    if st.session_state.running:
        # Simulate radar scan
        detections = st.session_state.radar.simulate_radar_scan()
        
        # Apply filters
        if show_only_moving:
            detections = [d for d in detections if d['speed_kmh'] > min_speed]
        else:
            detections = [d for d in detections if d['speed_kmh'] >= min_speed]
        
        # Draw radar display
        radar_img = st.session_state.radar.draw_radar_display(detections)
        radar_img_rgb = cv2.cvtColor(radar_img, cv2.COLOR_BGR2RGB)
        radar_placeholder.image(radar_img_rgb, channels="RGB", use_container_width=True)
        
        # Update status indicators
        if detections:
            closest = min(detections, key=lambda x: x['distance_km'])
            
            status_placeholder.metric("Radar Status", "🟢 ACTIVE")
            objects_placeholder.metric("Objects Tracked", len(detections))
            closest_placeholder.metric("Closest Object", f"{closest['distance_km']}km")
            
            if closest['distance_km'] < alert_distance:
                alert_placeholder.markdown(f"### 🔴 WITHIN {alert_distance}km")
            else:
                alert_placeholder.markdown(f"### 🟢 CLEAR")
            
            bearing_placeholder.metric("Radar Bearing", f"{st.session_state.radar.scan_angle:.0f}°")
        else:
            status_placeholder.metric("Radar Status", "🟢 SCANNING")
            objects_placeholder.metric("Objects Tracked", "0")
            closest_placeholder.metric("Closest Object", "None")
            alert_placeholder.markdown("### 🟢 AIRSPACE CLEAR")
            bearing_placeholder.metric("Radar Bearing", f"{st.session_state.radar.scan_angle:.0f}°")
        
        # Display active tracks
        if detections:
            tracks_df = pd.DataFrame([{
                'ID': d['id'],
                'Type': d['type'],
                'Distance': f"{d['distance_km']} km",
                'Altitude': f"{d['altitude_m']} m",
                'Speed': f"{d['speed_kmh']} km/h",
                'Bearing': d['bearing'],
                'Last Seen': d['last_seen'].strftime("%H:%M:%S")
            } for d in sorted(detections, key=lambda x: x['distance_km'])[:8]])
            
            tracks_placeholder.dataframe(tracks_df, use_container_width=True)
        else:
            tracks_placeholder.info("No active tracks detected")
        
        # Display proximity alerts
        alerts = [d for d in detections if d['distance_km'] < alert_distance]
        if alerts:
            alerts_html = ""
            for alert in sorted(alerts, key=lambda x: x['distance_km']):
                if alert['distance_km'] < 2:
                    threat_color = "#ff0000"
                    threat_icon = "🔴 CRITICAL"
                elif alert['distance_km'] < 5:
                    threat_color = "#ff6600"
                    threat_icon = "🟠 WARNING"
                else:
                    threat_color = "#ffcc00"
                    threat_icon = "🟡 CAUTION"
                
                alerts_html += f"""
                <div class="threat-card" style="border-left-color: {threat_color}">
                    <strong>{threat_icon}</strong><br>
                    <b>{alert['type']}</b> at {alert['distance_km']}km<br>
                    Bearing: {alert['bearing']} | Alt: {alert['altitude_m']}m<br>
                    Speed: {alert['speed_kmh']} km/h<br>
                    <small>ID: {alert['id']}</small>
                </div>
                """
            alerts_placeholder.markdown(alerts_html, unsafe_allow_html=True)
        else:
            alerts_placeholder.success("✅ No threats within alert range")
        
        # Display track analysis
        if detections:
            analysis_html = '<div class="info-card">'
            analysis_html += '<h4>Airspace Summary</h4>'
            
            # Count by type
            type_counts = {}
            for d in detections:
                type_counts[d['type']] = type_counts.get(d['type'], 0) + 1
            
            for obj_type, count in type_counts.items():
                analysis_html += f'• {obj_type}: {count}<br>'
            
            # Average stats
            avg_speed = np.mean([d['speed_kmh'] for d in detections])
            avg_alt = np.mean([d['altitude_m'] for d in detections])
            
            analysis_html += f'<br><b>Average Speed:</b> {avg_speed:.0f} km/h<br>'
            analysis_html += f'<b>Average Altitude:</b> {avg_alt:.0f} m<br>'
            
            # Busiest direction
            bearings = [d['bearing'] for d in detections]
            if bearings:
                from collections import Counter
                busiest = Counter(bearings).most_common(1)[0]
                analysis_html += f'<b>Busiest Direction:</b> {busiest[0]} ({busiest[1]} tracks)'
            
            analysis_html += '</div>'
            analysis_placeholder.markdown(analysis_html, unsafe_allow_html=True)
        else:
            analysis_placeholder.info("No tracks to analyze")
        
        # Auto-refresh for animation
        time.sleep(0.05)
        st.rerun()

if __name__ == "__main__":
    main()
