import streamlit as st
import numpy as np
import time
from datetime import datetime
import pandas as pd
import random
import math
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="Radar System",
    page_icon="🛸",
    layout="wide"
)

# Custom CSS for TV-style display
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle, #0a0a0a 0%, #000000 100%);
    }
    .radar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        background: #000000;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 0 30px rgba(0,255,0,0.2);
    }
    .tv-frame {
        border: 3px solid #333;
        border-radius: 15px;
        background: #000;
        padding: 10px;
        box-shadow: 0 0 20px rgba(0,255,0,0.1);
    }
    .scan-line {
        animation: scan 2s linear infinite;
    }
    @keyframes scan {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

class TVRadar:
    def __init__(self):
        self.targets = []
        self.rotation = 0
        self.range_km = 20
        self.next_id = 1
        self.scan_history = []
        
    def generate_targets(self):
        """Generate realistic radar targets"""
        # Add new targets randomly
        if random.random() < 0.15 and len(self.targets) < 12:
            distance = random.uniform(2, self.range_km)
            angle = random.uniform(0, 360)
            
            # Determine target type based on distance and random
            if distance < 5:
                target_type = random.choice(["Drone", "Bird"])
                speed = random.randint(30, 80)
                altitude = random.randint(50, 200)
            elif distance < 12:
                target_type = random.choice(["Small Aircraft", "Helicopter"])
                speed = random.randint(80, 180)
                altitude = random.randint(200, 800)
            else:
                target_type = random.choice(["Commercial Aircraft", "Military Aircraft"])
                speed = random.randint(180, 350)
                altitude = random.randint(800, 3000)
            
            target = {
                'id': self.next_id,
                'distance': round(distance, 1),
                'angle': angle,
                'speed': speed,
                'altitude': altitude,
                'type': target_type,
                'timestamp': datetime.now(),
                'history': [(angle, distance)]
            }
            self.targets.append(target)
            self.next_id += 1
        
        # Update existing targets (they move)
        for target in self.targets:
            # Targets move in direction
            angle_change = random.uniform(-3, 3)
            distance_change = random.uniform(-0.5, 0.5)
            
            target['angle'] += angle_change
            target['distance'] += distance_change
            
            # Keep within bounds
            target['distance'] = max(1, min(self.range_km, target['distance']))
            if target['angle'] >= 360:
                target['angle'] -= 360
            elif target['angle'] < 0:
                target['angle'] += 360
            
            # Update history
            target['history'].append((target['angle'], target['distance']))
            if len(target['history']) > 20:
                target['history'].pop(0)
            
            target['timestamp'] = datetime.now()
        
        # Remove old targets (disappeared)
        now = datetime.now()
        self.targets = [t for t in self.targets 
                       if (now - t['timestamp']).seconds < 20]
        
        return self.targets

def create_radar_image(targets, rotation, range_km, width=800, height=800):
    """Create a realistic TV-style radar image"""
    
    # Create blank radar screen
    img = Image.new('RGB', (width, height), color=(0, 5, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width // 2, height // 2)
    max_radius = min(width, height) // 2 - 40
    
    # Draw outer circle
    draw.ellipse([center[0] - max_radius, center[1] - max_radius,
                  center[0] + max_radius, center[1] + max_radius],
                 outline=(0, 100, 0), width=3)
    
    # Draw range rings (every 20% of range)
    for i in range(1, 6):
        radius = int(max_radius * (i / 5))
        draw.ellipse([center[0] - radius, center[1] - radius,
                      center[0] + radius, center[1] + radius],
                     outline=(0, 60, 0), width=1)
        
        # Add range labels
        range_label = int((i / 5) * range_km)
        label_x = center[0] + radius - 15
        label_y = center[1] + 5
        # Draw label background
        draw.rectangle([label_x-2, label_y-8, label_x+25, label_y+5], fill=(0, 5, 0))
        draw.text((label_x, label_y-8), f"{range_label}km", fill=(0, 100, 0))
    
    # Draw crosshairs (North-South, East-West lines)
    draw.line([(center[0], center[1] - max_radius), (center[0], center[1] + max_radius)],
              fill=(0, 50, 0), width=1)
    draw.line([(center[0] - max_radius, center[1]), (center[0] + max_radius, center[1])],
              fill=(0, 50, 0), width=1)
    
    # Draw cardinal direction labels
    draw.text((center[0]-5, center[1]-max_radius+15), "N", fill=(0, 200, 0), font_size=16)
    draw.text((center[0]-5, center[1]+max_radius-25), "S", fill=(0, 200, 0), font_size=16)
    draw.text((center[0]+max_radius-20, center[1]-8), "E", fill=(0, 200, 0), font_size=16)
    draw.text((center[0]-max_radius+10, center[1]-8), "W", fill=(0, 200, 0), font_size=16)
    
    # Draw degree ticks every 45 degrees
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        inner_radius = max_radius - 15
        x1 = center[0] + int(inner_radius * math.cos(rad))
        y1 = center[1] + int(inner_radius * math.sin(rad))
        x2 = center[0] + int(max_radius * math.cos(rad))
        y2 = center[1] + int(max_radius * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 80, 0), width=1)
    
    # Draw target trails (history)
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
                
                # Trail fades out
                alpha = i / len(target['history'])
                color_value = int(100 * alpha)
                draw.line([(prev_x, prev_y), (curr_x, curr_y)], 
                         fill=(0, color_value, 0), width=2)
    
    # Draw targets
    for target in targets:
        rad = math.radians(target['angle'])
        distance_ratio = target['distance'] / range_km
        x = center[0] + int(distance_ratio * max_radius * math.cos(rad))
        y = center[1] + int(distance_ratio * max_radius * math.sin(rad))
        
        # Color based on threat level (distance)
        if target['distance'] < 5:
            color = (255, 0, 0)  # Red - Close range
            size = 8
        elif target['distance'] < 12:
            color = (255, 100, 0)  # Orange - Medium range
            size = 7
        else:
            color = (0, 255, 0)  # Green - Long range
            size = 6
        
        # Draw target as blip with glow effect
        for r in range(size, 0, -2):
            alpha = 255 - (r * 50)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline=color)
        
        # Draw target ID
        draw.text((x+8, y-8), str(target['id']), fill=(0, 255, 0), font_size=10)
    
    # Draw rotating scan line
    rad = math.radians(rotation)
    scan_x = center[0] + int(max_radius * math.cos(rad))
    scan_y = center[1] + int(max_radius * math.sin(rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Draw glow at scan head
    for r in range(8, 0, -2):
        alpha = 255 - (r * 30)
        draw.ellipse([scan_x-r, scan_y-r, scan_x+r, scan_y+r], 
                    fill=(0, 255, 0), outline=(0, 255, 0))
    
    # Add radar info overlay (TV-style HUD)
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Top-left info panel
    overlay_draw.rectangle([10, 10, 250, 100], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    overlay_draw.text((20, 20), "RADAR SYSTEM", fill=(0, 255, 0), font_size=14)
    overlay_draw.text((20, 40), f"Range: {range_km} km", fill=(0, 200, 0), font_size=12)
    overlay_draw.text((20, 55), f"Mode: 360° Scan", fill=(0, 200, 0), font_size=12)
    overlay_draw.text((20, 70), f"Targets: {len(targets)}", fill=(0, 200, 0), font_size=12)
    
    # Bottom-left info panel
    overlay_draw.rectangle([10, height-80, 250, height-10], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    if targets:
        closest = min(targets, key=lambda x: x['distance'])
        overlay_draw.text((20, height-70), f"CLOSEST: {closest['type']}", fill=(0, 255, 0), font_size=11)
        overlay_draw.text((20, height-55), f"Distance: {closest['distance']} km", fill=(200, 200, 0), font_size=11)
        overlay_draw.text((20, height-40), f"Bearing: {closest['angle']:.0f}°", fill=(200, 200, 0), font_size=11)
    else:
        overlay_draw.text((20, height-55), "No Targets", fill=(0, 200, 0), font_size=12)
    
    # Bottom-right info panel
    overlay_draw.rectangle([width-200, height-80, width-10, height-10], fill=(0, 0, 0, 180), outline=(0, 100, 0))
    overlay_draw.text((width-190, height-70), "SYSTEM STATUS", fill=(0, 255, 0), font_size=11)
    overlay_draw.text((width-190, height-55), "Online", fill=(0, 255, 0), font_size=11)
    overlay_draw.text((width-190, height-40), f"Scan: {rotation:.0f}°", fill=(0, 200, 0), font_size=11)
    
    # Combine images
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    return img.convert('RGB')

def main():
    st.markdown('<div class="radar-container">', unsafe_allow_html=True)
    
    # Title
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #00ff00; text-shadow: 0 0 10px #00ff00;">🛸 360° RADAR SYSTEM</h1>
        <p style="color: #00aa00;">Real-Time Airspace Monitoring | Range: 20km | Full Coverage</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("## 🎮 RADAR CONTROLS")
        
        radar_range = st.slider("Detection Range", 5, 30, 20, 5)
        alert_distance = st.slider("Alert Zone", 1, 15, 5, 1)
        
        st.markdown("---")
        st.markdown("## 📡 FILTERS")
        
        min_speed = st.slider("Min Speed (km/h)", 0, 100, 0, 10)
        target_filter = st.multiselect(
            "Target Types",
            ["Drone", "Bird", "Small Aircraft", "Helicopter", "Commercial Aircraft", "Military Aircraft"],
            default=["Drone", "Small Aircraft", "Commercial Aircraft"]
        )
        
        st.markdown("---")
        st.markdown("## ℹ️ RADAR INFO")
        st.info(
            "**System Capabilities**\n\n"
            "• 360° Continuous Rotation\n"
            "• Range: Up to 30km\n"
            "• Real-time Target Tracking\n"
            "• Speed & Altitude Data\n"
            "• Movement Trail Display\n\n"
            "**Alert Levels**\n"
            "• 🟢 Green: >12km\n"
            "• 🟠 Orange: 5-12km\n"
            "• 🔴 Red: <5km"
        )
        
        if st.button("🔄 RESET RADAR", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Initialize radar
    if 'radar' not in st.session_state:
        st.session_state.radar = TVRadar()
        st.session_state.rotation = 0
    
    # Update radar rotation
    st.session_state.rotation += 4
    if st.session_state.rotation >= 360:
        st.session_state.rotation = 0
    
    # Generate targets
    targets = st.session_state.radar.generate_targets()
    
    # Apply filters
    if target_filter:
        targets = [t for t in targets if t['type'] in target_filter]
    targets = [t for t in targets if t['speed'] >= min_speed]
    
    # Update radar range
    st.session_state.radar.range_km = radar_range
    
    # Create radar image
    radar_img = create_radar_image(
        targets, 
        st.session_state.rotation, 
        radar_range,
        width=700,
        height=700
    )
    
    # Display radar
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="tv-frame">', unsafe_allow_html=True)
        st.image(radar_img, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Status metrics
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("RADAR STATUS", "🟢 ACTIVE")
        mcol2.metric("TARGETS", len(targets))
        mcol3.metric("RANGE", f"{radar_range} km")
        mcol4.metric("SCAN", f"{st.session_state.rotation:.0f}°")
    
    with col2:
        st.markdown("## 🎯 TARGET LIST")
        
        if targets:
            # Sort by distance
            targets_sorted = sorted(targets, key=lambda x: x['distance'])
            
            for target in targets_sorted[:8]:
                # Determine threat color
                if target['distance'] < alert_distance:
                    threat_color = "#ff0000"
                    threat_icon = "🔴"
                elif target['distance'] < alert_distance * 1.5:
                    threat_color = "#ff6600"
                    threat_icon = "🟠"
                else:
                    threat_color = "#00ff00"
                    threat_icon = "🟢"
                
                # Get bearing
                bearing = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((target['angle'] + 22.5) / 45) % 8]
                
                st.markdown(f"""
                <div style="background: #0a0a0a; border-left: 4px solid {threat_color}; 
                            border-radius: 8px; padding: 10px; margin: 8px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{threat_icon} {target['type']}</b>
                        <span style="color: {threat_color};">ID: {target['id']}</span>
                    </div>
                    <div style="font-size: 0.9em; margin-top: 5px;">
                        📍 Distance: <b>{target['distance']} km</b><br>
                        🧭 Bearing: <b>{bearing} ({target['angle']:.0f}°)</b><br>
                        ⚡ Speed: <b>{target['speed']} km/h</b><br>
                        📈 Altitude: <b>{target['altitude']} m</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No targets detected in current scan")
        
        st.markdown("## ⚠️ ALERTS")
        threats = [t for t in targets if t['distance'] < alert_distance]
        
        if threats:
            for threat in threats[:5]:
                if threat['distance'] < 3:
                    level = "🚨 CRITICAL THREAT"
                    color = "#ff0000"
                elif threat['distance'] < 7:
                    level = "⚠️ WARNING"
                    color = "#ff6600"
                else:
                    level = "ℹ️ CAUTION"
                    color = "#ffcc00"
                
                st.markdown(f"""
                <div style="background: #1a0000; border-left: 4px solid {color}; 
                            border-radius: 8px; padding: 8px; margin: 5px 0;">
                    <b>{level}</b><br>
                    {threat['type']} at {threat['distance']} km<br>
                    Approaching from {['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][int((threat['angle'] + 22.5) / 45) % 8]}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No active threats")
        
        # Statistics
        if targets:
            st.markdown("## 📊 STATISTICS")
            avg_speed = sum(t['speed'] for t in targets) / len(targets)
            avg_alt = sum(t['altitude'] for t in targets) / len(targets)
            
            st.metric("Avg Speed", f"{avg_speed:.0f} km/h")
            st.metric("Avg Altitude", f"{avg_alt:.0f} m")
            
            # Type breakdown
            type_count = {}
            for t in targets:
                type_count[t['type']] = type_count.get(t['type'], 0) + 1
            
            st.write("**Target Breakdown:**")
            for t, c in type_count.items():
                st.write(f"- {t}: {c}")
    
    # Auto-refresh for animation
    time.sleep(0.05)
    st.rerun()

if __name__ == "__main__":
    main()
