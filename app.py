# app.py - 360 Radar Detection System (Python 3.11 Compatible)
import streamlit as st
import cv2
import numpy as np
import time
from datetime import datetime
from collections import deque
import pandas as pd
import random
import math

# Page configuration
st.set_page_config(
    page_title="360 Radar Detection System",
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
        self.scan_speed = 3
        self.radar_range_km = 10
        self.next_id = 0
        
    def calculate_distance_km(self, pixels_from_center, max_pixels=350):
        """Convert pixel distance to kilometers"""
        return (pixels_from_center / max_pixels) * self.radar_range_km
    
    def calculate_altitude(self, object_size, distance_km):
        """Estimate altitude based on object size and distance"""
        base_altitude = 100
        size_factor = 100 / (object_size + 1)
        altitude_m = base_altitude + (distance_km * 50) - (size_factor * 10)
        return max(0, int(altitude_m))
    
    def get_bearing(self, angle):
        """Convert angle to cardinal direction"""
        bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                   'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = int((angle + 11.25) / 22.5) % 16
        return bearings[idx]
    
    def simulate_radar_scan(self):
        """Simulate realistic radar scan with moving objects"""
        self.scan_angle += self.scan_speed
        if self.scan_angle >= 360:
            self.scan_angle = 0
        
        # Add random detections
        if random.random() < 0.08:
            angle = random.randint(0, 359)
            distance_px = random.randint(50, 350)
            distance_km = self.calculate_distance_km(distance_px)
            speed_kmh = random.randint(20, 250)
            
            # Determine object type
            if speed_kmh > 180:
                obj_type = "Aircraft"
                size = 15
            elif speed_kmh > 100:
                obj_type = "Small Plane"
                size = 12
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
            self.next_id += 1
            
            if len(self.detections) > 12:
                self.detections.pop(0)
        
        # Update existing detections
        for detection in self.detections:
            angle_change = random.uniform(-4, 4)
            distance_change = random.uniform(-8, 8)
            
            detection['angle'] += angle_change
            detection['distance_px'] += distance_change
            detection['distance_px'] = max(30, min(370, detection['distance_px']))
            
            if detection['angle'] >= 360:
                detection['angle'] -= 360
            elif detection['angle'] < 0:
                detection['angle'] += 360
            
            detection['distance_km'] = round(self.calculate_distance_km(detection['distance_px']), 1)
            detection['bearing'] = self.get_bearing(detection['angle'])
            
            if len(detection.get('track_points', [])) > 0:
                prev_dist = detection['track_points'][-1][1]
                movement = abs(detection['distance_px'] - prev_dist)
                detection['speed_kmh'] = max(10, movement * 3)
            
            detection['last_seen'] = datetime.now()
            detection['track_points'].append((detection['angle'], detection['distance_px']))
            
            if len(detection['track_points']) > 20:
                detection['track_points'] = detection['track_points'][-20:]
        
        # Remove old detections
        current_time = datetime.now()
        self.detections = [d for d in self.detections 
                          if (current_time - d['last_seen']).seconds < 15]
        
        return self.detections
    
    def draw_radar_display(self, detections, width=800, height=800):
        """Draw realistic radar display"""
        radar_img = np.zeros((height, width, 3), dtype=np.uint8)
        radar_img[:] = (0, 10, 0)
        
        center = (width//2, height//2)
        max_radius = min(width, height)//2 - 50
        
        # Draw radar rings
        ring_step = max_radius / 5
        for r in range(1, 6):
            radius = int(ring_step * r)
            cv2.circle(radar_img, center, radius, (0, 100, 0), 1)
            range_km = int((r / 5) * self.radar_range_km)
            cv2.putText(radar_img, str(range_km) + "km", 
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
        
        # Draw bearing ticks
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = center[0] + int((max_radius - 10) * math.cos(rad))
            y1 = center[1] + int((max_radius - 10) * math.sin(rad))
            x2 = center[0] + int(max_radius * math.cos(rad))
            y2 = center[1] + int(max_radius * math.sin(rad))
            cv2.line(radar_img, (x1, y1), (x2, y2), (0, 100, 0), 1)
        
        # Draw detection trails and objects
        for detection in detections:
            angle_rad = math.radians(detection['angle'])
            distance = detection['distance_px']
            
            x = center[0] + int(distance * math.cos(angle_rad))
            y = center[1] + int(distance * math.sin(angle_rad))
            
            # Color based on speed
            if detection['speed_kmh'] > 150:
                color = (0, 0, 255)
                size = 8
            elif detection['speed_kmh'] > 80:
                color = (0, 100, 255)
                size = 7
            elif detection['speed_kmh'] > 30:
                color = (0, 255, 255)
                size = 6
            else:
                color = (0, 255, 0)
                size = 5
            
            # Draw trail
            if 'track_points' in detection and len(detection['track_points']) > 1:
                for i in range(1, len(detection['track_points'])):
                    prev_angle, prev_dist = detection['track_points'][i-1]
                    curr_angle, curr_dist = detection['track_points'][i]
                    
                    prev_rad = math.radians(prev_angle)
                    curr_rad = math.radians(curr_angle)
                    
                    px = center[0] + int(prev_dist * math.cos(prev_rad))
                    py = center[1] + int(prev_dist * math.sin(prev_rad))
                    cx = center[0] + int(curr_dist * math.cos(curr_rad))
                    cy = center[1] + int(curr_dist * math.sin(curr_rad))
                    
                    alpha = i / len(detection['track_points'])
                    trail_color = (0, int(200 * alpha), int(100 * (1-alpha)))
                    cv2.line(radar_img, (px, py), (cx, cy), trail_color, 2)
            
            # Draw object
            cv2.circle(radar_img, (x, y), size, color, -1)
            cv2.circle(radar_img, (x, y), size+1, (0, 255, 0), 1)
            
            # Draw ID label
            label = str(detection['id'])
            cv2.putText(radar_img, label, (x-5, y-8), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Draw scanning line
        scan_rad = math.radians(self.scan_angle)
        scan_x = center[0] + int(max_radius * math.cos(scan_rad))
        scan_y = center[1] + int(max_radius * math.sin(scan_rad))
        cv2.line(radar_img, center, (scan_x, scan_y), (0, 255, 0), 2)
        cv2.circle(radar_img, (scan_x, scan_y), 5, (0, 255, 0), -1)
        
        # Add info overlay
        overlay = radar_img.copy()
        cv2.rectangle(overlay, (10, 10), (250, 80), (0, 0, 0), -1)
        radar_img = cv2.addWeighted(overlay, 0.6, radar_img, 0.4, 0)
        
        cv2.putText(radar_img, "RADAR SCANNING", (15, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(radar_img, "Range: " + str(self.radar_range_km) + "km", (15, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        cv2.putText(radar_img, "Objects: " + str(len(detections)), (15, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        
        return radar_img

def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("360 REAL-TIME RADAR SYSTEM")
    st.markdown("### Live Airspace Monitoring | Range: 10km | 360 Coverage")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## RADAR CONTROLS")
        
        radar_range = st.slider(
            "Radar Range (km)",
            min_value=2.0,
            max_value=20.0,
            value=10.0,
            step=1.0
        )
        
        scan_speed = st.slider(
            "Scan Speed (RPM)",
            min_value=10,
            max_value=60,
            value=30,
            step=5
        )
        
        alert_distance = st.slider(
            "Alert Distance (km)",
            min_value=1.0,
            max_value=10.0,
            value=5.0,
            step=0.5
        )
        
        st.markdown("---")
        st.markdown("## FILTERS")
        
        min_speed = st.slider("Minimum Speed (km/h)", 0, 100, 0, 10)
        
        st.markdown("---")
        st.markdown("## SYSTEM INFO")
        
        st.info(
            "Radar Capabilities:\n"
            "- 360 Continuous Scanning\n"
            "- Range: Up to 20km\n"
            "- Tracks speed and altitude\n"
            "- Real-time alerts\n\n"
            "Detects:\n"
            "- Aircraft\n"
            "- Drones\n"
            "- Birds\n"
            "- Small Planes"
        )
        
        if st.button("RESET RADAR", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="radar-container">', unsafe_allow_html=True)
        radar_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status indicators
        status_cols = st.columns(4)
        with status_cols[0]:
            status_placeholder = st.empty()
        with status_cols[1]:
            objects_placeholder = st.empty()
        with status_cols[2]:
            closest_placeholder = st.empty()
        with status_cols[3]:
            bearing_placeholder = st.empty()
    
    with col2:
        st.markdown("## ACTIVE TRACKS")
        tracks_placeholder = st.empty()
        
        st.markdown("## PROXIMITY ALERTS")
        alerts_placeholder = st.empty()
        
        st.markdown("## TRACK ANALYSIS")
        analysis_placeholder = st.empty()
    
    # Initialize radar
    if 'radar' not in st.session_state:
        st.session_state.radar = RealRadarSystem()
        st.session_state.running = True
    
    # Update settings
    st.session_state.radar.radar_range_km = radar_range
    st.session_state.radar.scan_speed = scan_speed / 10
    
    # Main loop
    if st.session_state.running:
        # Get detections
        detections = st.session_state.radar.simulate_radar_scan()
        
        # Apply speed filter
        detections = [d for d in detections if d['speed_kmh'] >= min_speed]
        
        # Draw radar
        radar_img = st.session_state.radar.draw_radar_display(detections)
        radar_img_rgb = cv2.cvtColor(radar_img, cv2.COLOR_BGR2RGB)
        radar_placeholder.image(radar_img_rgb, channels="RGB", use_container_width=True)
        
        # Update status
        if detections:
            closest = min(detections, key=lambda x: x['distance_km'])
            
            status_placeholder.metric("Radar Status", "ACTIVE")
            objects_placeholder.metric("Objects Tracked", len(detections))
            closest_placeholder.metric("Closest Object", f"{closest['distance_km']} km")
            bearing_placeholder.metric("Radar Bearing", f"{st.session_state.radar.scan_angle:.0f}")
        else:
            status_placeholder.metric("Radar Status", "SCANNING")
            objects_placeholder.metric("Objects Tracked", "0")
            closest_placeholder.metric("Closest Object", "None")
            bearing_placeholder.metric("Radar Bearing", f"{st.session_state.radar.scan_angle:.0f}")
        
        # Display tracks table
        if detections:
            tracks_data = []
            for d in sorted(detections, key=lambda x: x['distance_km'])[:8]:
                tracks_data.append({
                    'ID': d['id'],
                    'Type': d['type'],
                    'Distance': f"{d['distance_km']} km",
                    'Altitude': f"{d['altitude_m']} m",
                    'Speed': f"{d['speed_kmh']} km/h",
                    'Bearing': d['bearing']
                })
            
            tracks_df = pd.DataFrame(tracks_data)
            tracks_placeholder.dataframe(tracks_df, use_container_width=True)
        else:
            tracks_placeholder.info("No active tracks detected")
        
        # Display alerts
        alerts = [d for d in detections if d['distance_km'] < alert_distance]
        if alerts:
            for alert in sorted(alerts, key=lambda x: x['distance_km']):
                if alert['distance_km'] < 2:
                    threat_icon = "CRITICAL"
                    threat_color = "#ff0000"
                elif alert['distance_km'] < 5:
                    threat_icon = "WARNING"
                    threat_color = "#ff6600"
                else:
                    threat_icon = "CAUTION"
                    threat_color = "#ffcc00"
                
                alert_html = f"""
                <div class="threat-card" style="border-left-color: {threat_color}">
                    <strong>{threat_icon}</strong><br>
                    <b>{alert['type']}</b> at {alert['distance_km']} km<br>
                    Bearing: {alert['bearing']} | Alt: {alert['altitude_m']} m<br>
                    Speed: {alert['speed_kmh']} km/h
                </div>
                """
                alerts_placeholder.markdown(alert_html, unsafe_allow_html=True)
        else:
            alerts_placeholder.success("No threats within alert range")
        
        # Display analysis
        if detections:
            type_counts = {}
            for d in detections:
                type_counts[d['type']] = type_counts.get(d['type'], 0) + 1
            
            avg_speed = sum(d['speed_kmh'] for d in detections) / len(detections)
            avg_alt = sum(d['altitude_m'] for d in detections) / len(detections)
            
            analysis_html = '<div class="info-card">'
            analysis_html += '<h4>Airspace Summary</h4>'
            
            for obj_type, count in type_counts.items():
                analysis_html += f"{obj_type}: {count}<br>"
            
            analysis_html += f"<br><b>Avg Speed:</b> {avg_speed:.0f} km/h<br>"
            analysis_html += f"<b>Avg Altitude:</b> {avg_alt:.0f} m"
            analysis_html += '</div>'
            
            analysis_placeholder.markdown(analysis_html, unsafe_allow_html=True)
        else:
            analysis_placeholder.info("No tracks to analyze")
        
        # Auto-refresh
        time.sleep(0.05)
        st.rerun()

if __name__ == "__main__":
    main()
