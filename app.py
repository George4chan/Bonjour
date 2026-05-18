# app.py - Military-Grade Flying Object Detection System
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.graph_objs as go
import random
import math
from scipy.spatial.distance import cdist

# Page configuration
st.set_page_config(
    page_title="Military Air Defense System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for military theme
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
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
        background: rgba(0,0,0,0.7);
        border-left: 4px solid #ff0000;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .warning-card {
        background: rgba(255,0,0,0.2);
        border: 2px solid #ff0000;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .object-badge {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        margin: 0.2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .critical { background: #ff0000; color: white; }
    .high { background: #ff6600; color: white; }
    .medium { background: #ffcc00; color: black; }
    .low { background: #00ff00; color: black; }
</style>
""", unsafe_allow_html=True)

class MilitaryDetector:
    def __init__(self):
        self.tracked_objects = {}
        self.next_id = 0
        self.object_history = {}
        self.threat_history = []
        self.alerts = []
        self.fgbg = None
        
        # Military classification database
        self.military_objects = {
            # Combat Aircraft
            "F-16 Falcon": {"speed": 80, "size": (80, 120), "threat": "CRITICAL", "type": "Fighter Jet"},
            "F-22 Raptor": {"speed": 85, "size": (85, 125), "threat": "CRITICAL", "type": "Stealth Fighter"},
            "F-35 Lightning": {"speed": 75, "size": (80, 120), "threat": "CRITICAL", "type": "Stealth Fighter"},
            "Su-57": {"speed": 80, "size": (80, 120), "threat": "CRITICAL", "type": "Fighter Jet"},
            "Eurofighter": {"speed": 75, "size": (75, 115), "threat": "HIGH", "type": "Fighter Jet"},
            "MIG-29": {"speed": 70, "size": (75, 110), "threat": "HIGH", "type": "Fighter Jet"},
            
            # Bombers
            "B-2 Spirit": {"speed": 50, "size": (150, 200), "threat": "CRITICAL", "type": "Stealth Bomber"},
            "B-52 Stratofortress": {"speed": 45, "size": (180, 250), "threat": "HIGH", "type": "Bomber"},
            "Tu-95 Bear": {"speed": 40, "size": (160, 220), "threat": "HIGH", "type": "Bomber"},
            
            # Drones
            "MQ-9 Reaper": {"speed": 35, "size": (60, 100), "threat": "HIGH", "type": "Combat Drone"},
            "RQ-4 Global Hawk": {"speed": 30, "size": (100, 150), "threat": "MEDIUM", "type": "Recon Drone"},
            "Bayraktar TB2": {"speed": 25, "size": (50, 80), "threat": "MEDIUM", "type": "Combat Drone"},
            "Shahed-136": {"speed": 20, "size": (40, 60), "threat": "MEDIUM", "type": "Loitering Munition"},
            "Switchblade": {"speed": 15, "size": (20, 40), "threat": "HIGH", "type": "Suicide Drone"},
            
            # Helicopters
            "AH-64 Apache": {"speed": 30, "size": (60, 80), "threat": "HIGH", "type": "Attack Helicopter"},
            "Mi-24 Hind": {"speed": 35, "size": (65, 85), "threat": "HIGH", "type": "Attack Helicopter"},
            "UH-60 Black Hawk": {"speed": 25, "size": (55, 75), "threat": "MEDIUM", "type": "Utility Helicopter"},
            "Ka-52 Alligator": {"speed": 30, "size": (60, 80), "threat": "HIGH", "type": "Attack Helicopter"},
            
            # Missiles
            "Cruise Missile": {"speed": 100, "size": (30, 50), "threat": "CRITICAL", "type": "Missile"},
            "Ballistic Missile": {"speed": 150, "size": (20, 40), "threat": "CRITICAL", "type": "Missile"},
            "Rocket": {"speed": 90, "size": (15, 30), "threat": "HIGH", "type": "Rocket"},
            
            # Birds (false positives)
            "Large Bird": {"speed": 15, "size": (20, 40), "threat": "LOW", "type": "Non-Threat"},
            "Small Bird": {"speed": 10, "size": (10, 20), "threat": "LOW", "type": "Non-Threat"},
        }
        
        # Threat levels
        self.threat_levels = {
            "CRITICAL": {"color": "#ff0000", "icon": "🔴", "action": "IMMEDIATE INTERCEPT"},
            "HIGH": {"color": "#ff6600", "icon": "🟠", "action": "SCRAMBLE ALERT"},
            "MEDIUM": {"color": "#ffcc00", "icon": "🟡", "action": "MONITOR CLOSELY"},
            "LOW": {"color": "#00ff00", "icon": "🟢", "action": "TRACK ONLY"}
        }
    
    def detect_military_objects(self, frame, sensitivity=0.5):
        """Detect and classify military flying objects"""
        if frame is None:
            return []
        
        if self.fgbg is None:
            self.fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16)
        
        try:
            # Apply background subtraction
            fgmask = self.fgbg.apply(frame)
            thresh = int(20 * (1 - sensitivity))
            _, fgmask = cv2.threshold(fgmask, thresh, 255, cv2.THRESH_BINARY)
            
            # Clean up mask
            kernel = np.ones((3,3), np.uint8)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 1
                    
                    # Calculate object characteristics
                    speed = self.calculate_speed(contour, frame.shape)
                    classification = self.classify_military_object(w, h, area, aspect_ratio, speed)
                    
                    detection = {
                        'id': -1,
                        'bbox': (x, y, x+w, y+h),
                        'center': (x + w//2, y + h//2),
                        'width': w,
                        'height': h,
                        'area': area,
                        'speed': speed,
                        'classification': classification,
                        'threat_level': self.military_objects[classification]['threat'],
                        'object_type': self.military_objects[classification]['type'],
                        'confidence': min(0.95, area / 1500),
                        'timestamp': datetime.now()
                    }
                    detections.append(detection)
            
            # Track objects
            tracked = self.track_military_objects(detections)
            
            # Check for threats
            self.assess_threats(tracked)
            
            # Update history
            self.threat_history.append({
                'timestamp': datetime.now(),
                'count': len(tracked),
                'critical_count': sum(1 for d in tracked if d.get('threat_level') == 'CRITICAL'),
                'high_count': sum(1 for d in tracked if d.get('threat_level') == 'HIGH')
            })
            
            if len(self.threat_history) > 200:
                self.threat_history = self.threat_history[-200:]
            
            return tracked
            
        except Exception as e:
            return []
    
    def calculate_speed(self, contour, frame_shape):
        """Estimate object speed based on movement"""
        # This is a simplified estimation
        # In production, you'd calculate based on frame-to-frame movement
        return random.uniform(20, 150)  # Placeholder
    
    def classify_military_object(self, width, height, area, aspect_ratio, speed):
        """Classify the detected object as specific military hardware"""
        
        # Size-based primary classification
        if area > 20000:  # Very large
            if aspect_ratio > 1.5:
                return "B-52 Stratofortress"
            else:
                return "B-2 Spirit"
        
        elif area > 10000:  # Large aircraft
            if speed > 70:
                return "F-22 Raptor"
            elif speed > 50:
                return "F-16 Falcon"
            else:
                return "B-52 Stratofortress"
        
        elif area > 5000:  # Medium aircraft
            if aspect_ratio > 1.3:
                if speed > 60:
                    return "F-35 Lightning"
                else:
                    return "MQ-9 Reaper"
            else:
                return "AH-64 Apache"
        
        elif area > 2000:  # Small aircraft/drones
            if speed > 40:
                if aspect_ratio > 1.5:
                    return "RQ-4 Global Hawk"
                else:
                    return "Bayraktar TB2"
            else:
                return "UH-60 Black Hawk"
        
        elif area > 500:  # Very small
            if speed > 80:
                if aspect_ratio > 2:
                    return "Cruise Missile"
                else:
                    return "Ballistic Missile"
            else:
                return "Switchblade"
        
        else:  # Tiny objects
            if speed > 50:
                return "Rocket"
            else:
                return "Large Bird" if area > 200 else "Small Bird"
    
    def track_military_objects(self, detections):
        """Track objects across frames"""
        tracked = []
        
        for detection in detections:
            matched = False
            best_match = None
            best_dist = float('inf')
            
            for obj_id, obj in self.tracked_objects.items():
                if 'center' in obj:
                    dist = np.sqrt(
                        (detection['center'][0] - obj['center'][0])**2 +
                        (detection['center'][1] - obj['center'][1])**2
                    )
                    if dist < 60 and dist < best_dist:
                        best_dist = dist
                        best_match = obj_id
                        matched = True
            
            if matched and best_match is not None:
                # Update existing track
                self.tracked_objects[best_match].update({
                    'center': detection['center'],
                    'bbox': detection['bbox'],
                    'classification': detection['classification'],
                    'threat_level': detection['threat_level'],
                    'last_seen': datetime.now(),
                    'confidence': detection['confidence'],
                    'track_length': self.tracked_objects[best_match].get('track_length', 0) + 1,
                    'speed_history': self.tracked_objects[best_match].get('speed_history', []) + [detection.get('speed', 0)]
                })
                detection['id'] = best_match
            else:
                # New track
                detection['id'] = self.next_id
                self.tracked_objects[self.next_id] = {
                    'center': detection['center'],
                    'bbox': detection['bbox'],
                    'classification': detection['classification'],
                    'threat_level': detection['threat_level'],
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'confidence': detection['confidence'],
                    'track_length': 1,
                    'speed_history': [detection.get('speed', 0)]
                }
                self.next_id += 1
            
            # Store trajectory
            if detection['id'] not in self.object_history:
                self.object_history[detection['id']] = deque(maxlen=50)
            self.object_history[detection['id']].append(detection['center'])
            
            tracked.append(detection)
        
        # Cleanup old tracks
        current_time = datetime.now()
        to_remove = [oid for oid, obj in self.tracked_objects.items() 
                    if (current_time - obj['last_seen']).total_seconds() > 3]
        
        for oid in to_remove:
            del self.tracked_objects[oid]
            if oid in self.object_history:
                del self.object_history[oid]
        
        return tracked
    
    def assess_threats(self, detections):
        """Assess and generate alerts for threats"""
        critical_threats = [d for d in detections if d.get('threat_level') == 'CRITICAL']
        high_threats = [d for d in detections if d.get('threat_level') == 'HIGH']
        
        # Generate alerts for new critical threats
        for threat in critical_threats:
            if threat['id'] not in [a.get('id') for a in self.alerts[-10:]]:
                self.alerts.append({
                    'id': threat['id'],
                    'classification': threat['classification'],
                    'threat_level': threat['threat_level'],
                    'timestamp': datetime.now(),
                    'message': f"⚠️ CRITICAL THREAT: {threat['classification']} detected! Immediate intercept required!"
                })
        
        # Keep only recent alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
    
    def draw_military_display(self, frame, detections):
        """Draw military-style threat display"""
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        display = frame.copy()
        
        # Threat colors
        threat_colors = {
            "CRITICAL": (0, 0, 255),      # Red
            "HIGH": (0, 100, 255),        # Orange
            "MEDIUM": (0, 255, 255),      # Yellow
            "LOW": (0, 255, 0)            # Green
        }
        
        # Draw threat rings around critical objects
        for detection in detections:
            if detection.get('threat_level') == 'CRITICAL':
                center = detection['center']
                for r in range(20, 80, 20):
                    cv2.circle(display, center, r, (0, 0, 255), 2)
        
        # Draw tracked objects
        for detection in detections:
            bbox = detection['bbox']
            threat_level = detection.get('threat_level', 'LOW')
            color = threat_colors.get(threat_level, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(display, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 3)
            
            # Draw center
            cv2.circle(display, detection['center'], 5, color, -1)
            
            # Draw threat indicator
            threat_icon = self.threat_levels[threat_level]['icon']
            cv2.putText(display, threat_icon, (bbox[0] - 20, bbox[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Draw labels
            label = f"{detection['classification']} [{detection.get('threat_level', 'UNKNOWN')}]"
            if detection.get('speed', 0) > 0:
                label += f" {detection['speed']:.0f}km/h"
            
            # Label background
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(display, (bbox[0], bbox[1] - text_h - 5),
                         (bbox[0] + text_w + 10, bbox[1]), color, -1)
            cv2.putText(display, label, (bbox[0] + 5, bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Draw trajectory trail
            if detection['id'] in self.object_history:
                trail = list(self.object_history[detection['id']])
                for i in range(1, len(trail)):
                    alpha = i / len(trail)
                    trail_color = tuple(int(c * alpha) for c in color)
                    cv2.line(display, trail[i-1], trail[i], trail_color, 2)
        
        # Add HUD overlay
        overlay = display.copy()
        cv2.rectangle(overlay, (5, 5), (300, 120), (0, 0, 0), -1)
        display = cv2.addWeighted(overlay, 0.6, display, 0.4, 0)
        
        # HUD Information
        critical_count = sum(1 for d in detections if d.get('threat_level') == 'CRITICAL')
        high_count = sum(1 for d in detections if d.get('threat_level') == 'HIGH')
        
        cv2.putText(display, "MILITARY AIR DEFENSE SYSTEM", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(display, f"Active Tracks: {len(detections)}", (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, f"CRITICAL: {critical_count} | HIGH: {high_count}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Threat level indicator
        if critical_count > 0:
            threat_text = "⚠️ CRITICAL THREAT - IMMEDIATE ACTION REQUIRED ⚠️"
            cv2.putText(display, threat_text, (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return display

def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown("# 🛡️ MILITARY AIR DEFENSE SYSTEM")
    st.markdown("### Real-time Detection & Tracking of Military Aircraft, Drones, and Missiles")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎮 DEFENSE CONTROLS")
        
        mode = st.radio(
            "Sensor Mode",
            ["🎮 Simulation Mode", "📹 Webcam Feed", "📁 Intelligence File"],
            help="Select threat detection source"
        )
        
        st.markdown("---")
        st.markdown("## ⚙️ SENSOR SETTINGS")
        
        sensitivity = st.slider(
            "Detection Sensitivity", 
            0.1, 1.0, 0.7, 0.05,
            help="Higher sensitivity for threat detection"
        )
        
        alert_threshold = st.select_slider(
            "Alert Threshold",
            options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            value="HIGH",
            help="Minimum threat level to generate alerts"
        )
        
        st.markdown("---")
        st.markdown("## 🎨 DISPLAY OPTIONS")
        
        show_trails = st.checkbox("Show Trajectory Trails", True)
        show_threat_rings = st.checkbox("Show Threat Rings", True)
        show_hud = st.checkbox("Show HUD", True)
        
        st.markdown("---")
        
        if st.button("🔄 RESET SYSTEM", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📡 THREAT DETECTION FEED")
        video_placeholder = st.empty()
        
        # Status indicators
        status_cols = st.columns(4)
        with status_cols[0]:
            threat_level_placeholder = st.empty()
        with status_cols[1]:
            track_count_placeholder = st.empty()
        with status_cols[2]:
            critical_count_placeholder = st.empty()
        with status_cols[3]:
            fps_placeholder = st.empty()
    
    with col2:
        st.markdown("## ⚠️ ACTIVE THREATS")
        alerts_placeholder = st.empty()
        
        st.markdown("## 📊 THREAT ASSESSMENT")
        stats_placeholder = st.empty()
    
    # Initialize session state
    if 'detector' not in st.session_state:
        st.session_state.detector = MilitaryDetector()
        st.session_state.is_running = False
        st.session_state.threat_log = []
        st.session_state.frame_count = 0
        st.session_state.fps = 0
        st.session_state.last_time = time.time()
    
    # Start/Stop controls
    btn_cols = st.columns(2)
    with btn_cols[0]:
        if st.button("🚀 ACTIVATE SYSTEM", type="primary", use_container_width=True):
            st.session_state.is_running = True
            st.session_state.threat_log = []
            st.session_state.detector.alerts = []
    
    with btn_cols[1]:
        if st.button("🔒 STANDBY MODE", use_container_width=True):
            st.session_state.is_running = False
    
    # Main detection loop
    if st.session_state.is_running:
        # Handle different modes
        if mode == "🎮 Simulation Mode":
            # Simulation mode for testing
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (20, 20, 40)
            
            # Generate simulated military objects
            if not hasattr(st.session_state, 'sim_targets'):
                st.session_state.sim_targets = []
                military_types = [
                    "F-22 Raptor", "MQ-9 Reaper", "AH-64 Apache", 
                    "Cruise Missile", "B-2 Spirit", "Su-57"
                ]
                for i in range(random.randint(2, 5)):
                    st.session_state.sim_targets.append({
                        'pos': [random.randint(100, 540), random.randint(100, 380)],
                        'vel': [random.uniform(-2, 2), random.uniform(-2, 2)],
                        'type': random.choice(military_types),
                        'size': random.randint(20, 60)
                    })
            
            # Update and draw simulation targets
            for target in st.session_state.sim_targets:
                target['pos'][0] += target['vel'][0]
                target['pos'][1] += target['vel'][1]
                
                if target['pos'][0] < 50 or target['pos'][0] > 590:
                    target['vel'][0] = -target['vel'][0]
                if target['pos'][1] < 50 or target['pos'][1] > 430:
                    target['vel'][1] = -target['vel'][1]
                
                target['pos'][0] = max(50, min(590, target['pos'][0]))
                target['pos'][1] = max(50, min(430, target['pos'][1]))
                
                # Draw based on threat level
                threat_level = st.session_state.detector.military_objects[target['type']]['threat']
                color = (0, 0, 255) if threat_level == "CRITICAL" else (0, 100, 255)
                
                # Draw with label
                cv2.circle(frame, tuple(map(int, target['pos'])), target['size']//2, color, -1)
                cv2.putText(frame, target['type'], 
                          (int(target['pos'][0]) - 25, int(target['pos'][1]) - 15),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Process frame
            detections = st.session_state.detector.detect_military_objects(frame, sensitivity)
            display_frame = st.session_state.detector.draw_military_display(frame, detections)
            
        elif mode == "📹 Webcam Feed":
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("⚠️ Webcam not accessible")
                st.session_state.is_running = False
                return
            
            ret, frame = cap.read()
            if ret:
                detections = st.session_state.detector.detect_military_objects(frame, sensitivity)
                display_frame = st.session_state.detector.draw_military_display(frame, detections)
            cap.release()
        
        else:  # Intelligence File
            uploaded_file = st.file_uploader("Upload intelligence video", type=['mp4', 'avi', 'mov'])
            if uploaded_file:
                with open("temp_intel.mp4", "wb") as f:
                    f.write(uploaded_file.read())
                cap = cv2.VideoCapture("temp_intel.mp4")
                ret, frame = cap.read()
                if ret:
                    detections = st.session_state.detector.detect_military_objects(frame, sensitivity)
                    display_frame = st.session_state.detector.draw_military_display(frame, detections)
                cap.release()
            else:
                st.warning("No intelligence file loaded")
                st.session_state.is_running = False
                return
        
        # Calculate FPS
        st.session_state.frame_count += 1
        current_time = time.time()
        if current_time - st.session_state.last_time >= 1.0:
            st.session_state.fps = st.session_state.frame_count
            st.session_state.frame_count = 0
            st.session_state.last_time = current_time
        
        # Update displays
        critical_count = sum(1 for d in detections if d.get('threat_level') == 'CRITICAL')
        high_count = sum(1 for d in detections if d.get('threat_level') == 'HIGH')
        
        if critical_count > 0:
            threat_level_placeholder.markdown(f"### 🔴 THREAT LEVEL: CRITICAL")
        elif high_count > 0:
            threat_level_placeholder.markdown(f"### 🟠 THREAT LEVEL: HIGH")
        else:
            threat_level_placeholder.markdown(f"### 🟢 THREAT LEVEL: MONITORING")
        
        track_count_placeholder.metric("Active Tracks", len(detections))
        critical_count_placeholder.metric("CRITICAL THREATS", critical_count, delta_color="inverse")
        fps_placeholder.metric("System FPS", st.session_state.fps)
        
        # Display active threats
        if st.session_state.detector.alerts:
            alerts_html = ""
            for alert in st.session_state.detector.alerts[-5:]:
                threat_level = alert['threat_level']
                color = "#ff0000" if threat_level == "CRITICAL" else "#ff6600"
                alerts_html += f"""
                <div class="warning-card" style="border-left-color: {color}">
                    <strong>{alert['threat_level']}</strong><br>
                    {alert['message']}<br>
                    <small>{alert['timestamp'].strftime("%H:%M:%S")}</small>
                </div>
                """
            alerts_placeholder.markdown(alerts_html, unsafe_allow_html=True)
        else:
            alerts_placeholder.info("No active threats detected")
        
        # Display statistics
        if detections:
            threat_counts = {}
            type_counts = {}
            
            for d in detections:
                threat = d.get('threat_level', 'UNKNOWN')
                threat_counts[threat] = threat_counts.get(threat, 0) + 1
                
                obj_type = d.get('object_type', 'Unknown')
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            stats_html = '<div class="detection-card">'
            stats_html += '<h4>Threat Breakdown</h4>'
            for threat, count in threat_counts.items():
                css_class = "critical" if threat == "CRITICAL" else "high" if threat == "HIGH" else "medium"
                stats_html += f'<span class="object-badge {css_class}">{threat}: {count}</span>'
            
            stats_html += '<h4 style="margin-top: 10px">Asset Classification</h4>'
            for obj_type, count in type_counts.items():
                stats_html += f'<span class="object-badge">{obj_type}: {count}</span>'
            
            stats_html += '</div>'
            stats_placeholder.markdown(stats_html, unsafe_allow_html=True)
        else:
            stats_placeholder.info("No targets detected")
        
        # Display video feed
        if 'display_frame' in locals():
            display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(display_rgb, channels="RGB", use_container_width=True)
        
        # Auto-refresh for simulation
        if mode == "🎮 Simulation Mode":
            time.sleep(0.05)
            st.rerun()
    
    # Threat history graph
    if len(st.session_state.detector.threat_history) > 5:
        st.markdown("## 📈 THREAT HISTORY")
        
        hist_df = pd.DataFrame([{
            'Time': h['timestamp'].strftime("%H:%M:%S"),
            'Critical': h.get('critical_count', 0),
            'High': h.get('high_count', 0),
            'Total': h['count']
        } for h in st.session_state.detector.threat_history[-30:]])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df['Time'], y=hist_df['Critical'], 
                                 name='CRITICAL', line=dict(color='red', width=2)))
        fig.add_trace(go.Scatter(x=hist_df['Time'], y=hist_df['High'], 
                                 name='HIGH', line=dict(color='orange', width=2)))
        fig.add_trace(go.Scatter(x=hist_df['Time'], y=hist_df['Total'], 
                                 name='Total Tracks', line=dict(color='cyan', width=1, dash='dash')))
        
        fig.update_layout(
            height=300,
            plot_bgcolor='rgba(0,0,0,0.3)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            title="Threat Level Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("### 🛡️ System Capabilities")
    cols = st.columns(5)
    with cols[0]:
        st.markdown("**✈️ Fighter Jets**\nF-16, F-22, F-35, Su-57")
    with cols[1]:
        st.markdown("**🚁 Attack Helos**\nAH-64, Mi-24, Ka-52")
    with cols[2]:
        st.markdown("**🛸 Combat Drones**\nMQ-9, Bayraktar, Switchblade")
    with cols[3]:
        st.markdown("**💣 Missiles**\nCruise, Ballistic, Rockets")
    with cols[4]:
        st.markdown("**🎯 Threat Assessment**\nCritical/High/Medium/Low")

if __name__ == "__main__":
    main()
