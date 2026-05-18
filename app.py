import streamlit as st
import numpy as np
import time
from datetime import datetime
import pandas as pd
import random
import math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="Radar System",
    page_icon="🛸",
    layout="wide"
)

# Custom CSS for stable display
st.markdown("""
<style>
    .stApp {
        background: #000000;
    }
    .main-header {
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
    }
    .radar-frame {
        background: #000000;
        border-radius: 20px;
        padding: 20px;
        border: 3px solid #00ff00;
        box-shadow: 0 0 30px rgba(0,255,0,0.3);
    }
    .target-card {
        background: #0a0a0a;
        border-left: 4px solid #00ff00;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
    }
    .alert-card {
        background: #1a0000;
        border-left: 4px solid #ff0000;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
    }
    .stMetric {
        background: #0a0a0a;
        border-radius: 10px;
        padding: 10px;
    }
    div[data-testid="stImage"] {
        background: #000000;
    }
</style>
""", unsafe_allow_html=True)

class StableRadar:
    def __init__(self):
        self.targets = []
        self.scan_angle = 0
        self.range_km = 20
        self.next_id = 1
        self.frame_count = 0
        
    def update_targets(self):
        """Update target positions"""
        # Add new targets (less frequently for stability)
        if random.random() < 0.08 and len(self.targets) < 10:
            distance = round(random.uniform(3, self.range_km), 1)
            angle = random.uniform(0, 360)
            
            # Classify by distance
            if distance < 6:
                target_type = random.choice(["Drone", "Bird"])
                speed = random.randint(40, 100)
                altitude = random.randint(80, 300)
            elif distance < 13:
                target_type = random.choice(["Small Aircraft", "Helicopter"])
                speed = random.randint(100, 220)
                altitude = random.randint(300, 1000)
            else:
                target_type = random.choice(["Commercial Jet", "Military Aircraft"])
                speed = random.randint(220, 400)
                altitude = random.randint(1000, 3500)
            
            self.targets.append({
                'id': self.next_id,
                'distance': distance,
                'angle': angle,
                'speed': speed,
                'altitude': altitude,
                'type': target_type,
                'timestamp': datetime.now(),
                'history': [(angle, distance)]
            })
            self.next_id += 1
        
        # Update existing targets
        for target in self.targets:
            # Move targets
            angle_change = random.uniform(-2, 2)
            distance_change = random.uniform(-0.3, 0.3)
            
            target['angle'] += angle_change
            target['distance'] += distance_change
            
            # Keep in bounds
            target['distance'] = max(1, min(self.range_km, target['distance']))
            if target['angle'] >= 360:
                target['angle'] -= 360
            elif target['angle'] < 0:
                target['angle'] += 360
            
            # Update history
            target['history'].append((target['angle'], target['distance']))
            if len(target['history']) > 15:
                target['history'].pop(0)
            
            target['timestamp'] = datetime.now()
        
        # Remove old targets
        now = datetime.now()
        self.targets = [t for t in self.targets 
                       if (now - t['timestamp']).seconds < 18]
        
        return self.targets

def create_stable_radar_image(targets, scan_angle, range_km, width=800, height=800):
    """Create a stable radar image that doesn't flicker"""
    
    # Create base image with dark green background
    img = Image.new('RGB', (width, height), color=(0, 8, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width // 2, height // 2)
    max_radius = min(width, height) // 2 - 50
    
    # Draw outer ring (always visible)
    draw.ellipse([center[0] - max_radius, center[1] - max_radius,
                  center[0] + max_radius, center[1] + max_radius],
                 outline=(0, 150, 0), width=3)
    
    # Draw range rings
    ring_colors = [(0, 60, 0), (0, 70, 0), (0, 80, 0), (0, 90, 0), (0, 100, 0)]
    for i in range(1, 6):
        radius = int(max_radius * (i / 5))
        color = ring_colors[i-1] if i-1 < len(ring_colors) else (0, 100, 0)
        draw.ellipse([center[0] - radius, center[1] - radius,
                      center[0] + radius, center[1] + radius],
                     outline=color, width=1)
        
        # Range labels
        range_km_label = int((i / 5) * range_km)
        label_x = center[0] + radius - 25
        label_y = center[1] + 5
        draw.rectangle([label_x-2, label_y-10, label_x+30, label_y+5], fill=(0, 8, 0))
        draw.text((label_x, label_y-8), f"{range_km_label}km", fill=(0, 120, 0))
    
    # Draw crosshairs
    draw.line([(center[0], center[1] - max_radius), (center[0], center[1] + max_radius)],
              fill=(0, 60, 0), width=1)
    draw.line([(center[0] - max_radius, center[1]), (center[0] + max_radius, center[1])],
              fill=(0, 60, 0), width=1)
    
    # Draw cardinal directions (always visible)
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    for i, direction in enumerate(directions):
        angle = i * 45
        rad = math.radians(angle)
        x = center[0] + int((max_radius + 15) * math.cos(rad))
        y = center[1] + int((max_radius + 15) * math.sin(rad))
        
        # Adjust position for corners
        if direction == 'N':
            x, y = center[0] - 5, center[1] - max_radius - 5
        elif direction == 'S':
            x, y = center[0] - 5, center[1] + max_radius + 5
        elif direction == 'E':
            x, y = center[0] + max_radius + 5, center[1] - 5
        elif direction == 'W':
            x, y = center[0] - max_radius - 15, center[1] - 5
        
        draw.text((x, y), direction, fill=(0, 180, 0))
    
    # Draw degree ticks
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        inner_x = center[0] + int((max_radius - 10) * math.cos(rad))
        inner_y = center[1] + int((max_radius - 10) * math.sin(rad))
        outer_x = center[0] + int(max_radius * math.cos(rad))
        outer_y = center[1] + int(max_radius * math.sin(rad))
        draw.line([(inner_x, inner_y), (outer_x, outer_y)], fill=(0, 80, 0), width=1)
    
    # Draw target trails (fading)
    for target in targets:
        if len(target['history']) > 1:
            for i in range(1, len(target['history'])):
                prev_angle, prev_dist = target['history'][i-1]
                curr_angle, curr_dist = target['history'][i]
                
                prev_rad = math.radians(prev_angle)
                curr_rad = math.radians(curr_angle)
                
                prev_x = center[0] + int((prev_dist / range_km) * max_radius * math.cos(prev_rad))
                prev_y = center[1] + int((prev_dist / range_km) * max_radius * math.sin(prev_rad))
                curr_x = center[0] + int((curr_dist / range_km) * max_radius * math.cos(curr_rad))
                curr_y = center[1] + int((curr_dist / range_km) * max_radius * math.sin(curr_rad))
                
                # Trail intensity based on position in history
                intensity = int(80 * (i / len(target['history'])))
                draw.line([(prev_x, prev_y), (curr_x, curr_y)], fill=(0, intensity, 0), width=2)
    
    # Draw targets
    for target in targets:
        rad = math.radians(target['angle'])
        distance_ratio = target['distance'] / range_km
        x = center[0] + int(distance_ratio * max_radius * math.cos(rad))
        y = center[1] + int(distance_ratio * max_radius * math.sin(rad))
        
        # Color based on distance (threat level)
        if target['distance'] < 5:
            color = (255, 0, 0)      # Red - Critical
            size = 9
            glow = (200, 0, 0)
        elif target['distance'] < 10:
            color = (255, 100, 0)    # Orange - Warning
            size = 8
            glow = (200, 80, 0)
        else:
            color = (0, 255, 0)      # Green - Safe
            size = 7
            glow = (0, 200, 0)
        
        # Draw glow effect
        for r in range(size + 2, size - 1, -1):
            draw.ellipse([x-r, y-r, x+r, y+r], fill=glow, outline=glow)
        
        # Draw target center
        draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color, outline=color)
        
        # Draw target ID
        draw.text((x+5, y-8), str(target['id']), fill=(0, 255, 0))
    
    # Draw scanning beam (rotating line)
    rad = math.radians(scan_angle)
    scan_x = center[0] + int(max_radius * math.cos(rad))
    scan_y = center[1] + int(max_radius * math.sin(rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Draw scan head glow
    for r in range(6, 0, -1):
        draw.ellipse([scan_x-r, scan_y-r, scan_x+r, scan_y+r], fill=(0, 255, 0), outline=(0, 255, 0))
    
    # Draw HUD overlay (always visible)
    # Top info bar
    draw.rectangle([10, 10, 280, 95], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    draw.text((20, 20), "RADAR SYSTEM", fill=(0, 255, 0))
    draw.text((20, 38), f"Range: {range_km} km", fill=(0, 200, 0))
    draw.text((20, 54), f"Targets: {len(targets)}", fill=(0, 200, 0))
    draw.text((20, 70), f"Scan: {scan_angle:.0f} deg", fill=(0, 200, 0))
    
    # Bottom info bar
    draw.rectangle([10, height-70, 280, height-10], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    if targets:
        closest = min(targets, key=lambda x: x['distance'])
        draw.text((20, height-60), "CLOSEST TARGET", fill=(0, 255, 0))
        draw.text((20, height-45), f"Type: {closest['type']}", fill=(200, 200, 0))
        draw.text((20, height-30), f"Dist: {closest['distance']} km", fill=(200, 200, 0))
    else:
        draw.text((20, height-45), "No Targets Detected", fill=(0, 200, 0))
    
    # Right side info
    draw.rectangle([width-180, 10, width-10, 95], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    draw.text((width-170, 20), "STATUS", fill=(0, 255, 0))
    draw.text((width-170, 38), "Online", fill=(0, 255, 0))
    draw.text((width-170, 54), f"Time: {datetime.now().strftime('%H:%M:%S')}", fill=(0, 200, 0))
    
    return img

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: #00ff00; text-shadow: 0 0 10px #00ff00;">🛸 360° RADAR SYSTEM</h1>
        <p style="color: #00aa00;">Real-Time Airspace Monitoring | Full Coverage | 20km Range</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎮 RADAR CONTROLS")
        
        radar_range = st.slider(
            "Detection Range (km)",
            min_value=5,
            max_value=30,
            value=20,
            step=5,
            key="range_slider"
        )
        
        alert_zone = st.slider(
            "Alert Zone (km)",
            min_value=2,
            max_value=15,
            value=8,
            step=1,
            key="alert_slider"
        )
        
        st.markdown("---")
        st.markdown("## 📡 TARGET FILTERS")
        
        min_speed = st.slider("Minimum Speed (km/h)", 0, 100, 0, 10, key="speed_slider")
        
        target_types = st.multiselect(
            "Target Types",
            ["Drone", "Bird", "Small Aircraft", "Helicopter", "Commercial Jet", "Military Aircraft"],
            default=["Drone", "Small Aircraft", "Commercial Jet", "Military Aircraft"],
            key="type_filter"
        )
        
        st.markdown("---")
        st.markdown("## ℹ️ INFORMATION")
        
        st.info(
            "**Radar Features**\n\n"
            "• 360° Continuous Scan\n"
            "• Real-time Target Tracking\n"
            "• Speed & Altitude Data\n"
            "• Movement Trails\n\n"
            "**Threat Levels**\n"
            "• 🟢 Green: >10 km\n"
            "• 🟠 Orange: 5-10 km\n"
            "• 🔴 Red: <5 km"
        )
        
        if st.button("🔄 RESET RADAR", use_container_width=True, key="reset_btn"):
            st.session_state.clear()
            st.rerun()
    
    # Initialize radar in session state (persists across reruns)
    if 'radar' not in st.session_state:
        st.session_state.radar = StableRadar()
        st.session_state.scan_angle = 0
        st.session_state.targets = []
    
    # Update scan angle (smooth rotation)
    st.session_state.scan_angle += 3
    if st.session_state.scan_angle >= 360:
        st.session_state.scan_angle = 0
    
    # Update targets
    st.session_state.radar.range_km = radar_range
    all_targets = st.session_state.radar.update_targets()
    
    # Apply filters
    filtered_targets = all_targets.copy()
    if target_types:
        filtered_targets = [t for t in filtered_targets if t['type'] in target_types]
    filtered_targets = [t for t in filtered_targets if t['speed'] >= min_speed]
    
    # Create radar image (stable)
    radar_image = create_stable_radar_image(
        filtered_targets,
        st.session_state.scan_angle,
        radar_range,
        width=700,
        height=700
    )
    
    # Layout
    col1, col2 = st.columns([1.8, 1.2])
    
    with col1:
        # Radar display
        st.markdown('<div class="radar-frame">', unsafe_allow_html=True)
        st.image(radar_image, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status metrics
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("RADAR STATUS", "🟢 ACTIVE")
        with metric_cols[1]:
            st.metric("TARGETS", len(filtered_targets))
        with metric_cols[2]:
            st.metric("RANGE", f"{radar_range} km")
        with metric_cols[3]:
            st.metric("SCAN", f"{st.session_state.scan_angle:.0f}°")
    
    with col2:
        st.markdown("## 🎯 ACTIVE TARGETS")
        
        if filtered_targets:
            # Sort by distance
            filtered_targets.sort(key=lambda x: x['distance'])
            
            for target in filtered_targets[:8]:
                # Determine threat level
                if target['distance'] < alert_zone:
                    if target['distance'] < 5:
                        threat = "🔴 CRITICAL"
                        border_color = "#ff0000"
                    else:
                        threat = "🟠 WARNING"
                        border_color = "#ff6600"
                else:
                    threat = "🟢 MONITOR"
                    border_color = "#00ff00"
                
                # Calculate bearing
                bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                           'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                bearing_idx = int((target['angle'] + 11.25) / 22.5) % 16
                bearing = bearings[bearing_idx]
                
                st.markdown(f"""
                <div style="background: #0a0a0a; border-left: 4px solid {border_color}; 
                            border-radius: 8px; padding: 12px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <b>{threat}</b>
                        <span style="color: #00ff00;">ID: {target['id']}</span>
                    </div>
                    <b>{target['type']}</b><br>
                    📍 Distance: <b>{target['distance']} km</b> ({bearing} {target['angle']:.0f}°)<br>
                    ⚡ Speed: <b>{target['speed']} km/h</b><br>
                    📈 Altitude: <b>{target['altitude']} m</b>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No targets detected in current scan range")
        
        st.markdown("## ⚠️ THREAT ALERTS")
        
        threats = [t for t in filtered_targets if t['distance'] < alert_zone]
        
        if threats:
            for threat in threats[:5]:
                if threat['distance'] < 5:
                    level = "🚨 CRITICAL THREAT"
                    bg_color = "#2a0000"
                elif threat['distance'] < 8:
                    level = "⚠️ HIGH THREAT"
                    bg_color = "#1a1000"
                else:
                    level = "ℹ️ CAUTION"
                    bg_color = "#0a1a00"
                
                st.markdown(f"""
                <div style="background: {bg_color}; border-left: 4px solid #ff0000; 
                            border-radius: 8px; padding: 10px; margin: 8px 0;">
                    <b>{level}</b><br>
                    {threat['type']} - {threat['distance']} km<br>
                    Speed: {threat['speed']} km/h | Alt: {threat['altitude']} m
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No threats in alert zone")
        
        # Statistics
        if filtered_targets:
            st.markdown("## 📊 AIRSPACE STATS")
            
            avg_speed = sum(t['speed'] for t in filtered_targets) / len(filtered_targets)
            avg_alt = sum(t['altitude'] for t in filtered_targets) / len(filtered_targets)
            
            stat_cols = st.columns(2)
            with stat_cols[0]:
                st.metric("Avg Speed", f"{avg_speed:.0f} km/h")
            with stat_cols[1]:
                st.metric("Avg Altitude", f"{avg_alt:.0f} m")
            
            # Type breakdown
            type_counts = {}
            for t in filtered_targets:
                type_counts[t['type']] = type_counts.get(t['type'], 0) + 1
            
            st.write("**Target Types:**")
            for t, c in type_counts.items():
                st.write(f"- {t}: {c}")
    
    # Auto-refresh for radar animation
    time.sleep(0.05)
    st.rerun()

if __name__ == "__main__":
    main()
