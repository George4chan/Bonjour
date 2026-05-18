import streamlit as st
import numpy as np
import time
from datetime import datetime
import pandas as pd
import random
import math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="360° Military Radar System",
    page_icon="🛸",
    layout="wide"
)

# Custom CSS for military green theme
st.markdown("""
<style>
    .stApp {
        background: #0a0f0a;
    }
    .main-container {
        background: #0a0f0a;
        padding: 20px;
    }
    .radar-title {
        text-align: center;
        margin-bottom: 20px;
    }
    .radar-title h1 {
        color: #00ff00;
        text-shadow: 0 0 10px #00ff00;
        font-family: monospace;
        font-size: 28px;
        margin: 0;
    }
    .radar-title p {
        color: #00aa00;
        font-family: monospace;
        font-size: 14px;
        margin: 5px 0;
    }
    .specs-box {
        background: #0a1a0a;
        border: 1px solid #00ff00;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .specs-title {
        color: #00ff00;
        font-family: monospace;
        font-weight: bold;
        font-size: 14px;
        border-bottom: 1px solid #00ff00;
        margin-bottom: 8px;
    }
    .target-table {
        background: #0a1a0a;
        border: 1px solid #00ff00;
        border-radius: 5px;
        padding: 10px;
    }
    .status-ok {
        color: #00ff00;
    }
    .status-warning {
        color: #ffaa00;
    }
    .status-critical {
        color: #ff0000;
    }
    .data-row {
        font-family: monospace;
        font-size: 12px;
        padding: 4px;
        border-bottom: 1px solid #00aa00;
    }
</style>
""", unsafe_allow_html=True)

class MilitaryRadar:
    def __init__(self):
        self.targets = []
        self.scan_angle = 0
        self.range_km = 200  # 200km range like in spec
        self.next_id = 1
        self.rotation_speed = 3  # degrees per frame
        
    def generate_targets(self):
        """Generate realistic military targets"""
        # Add new targets
        if random.random() < 0.12 and len(self.targets) < 15:
            distance = round(random.uniform(5, self.range_km), 1)
            angle = random.uniform(0, 360)
            
            # Classify targets
            if distance < 15:
                target_type = random.choice(["Drone", "UAV", "Helicopter"])
                speed = random.randint(80, 250)
                altitude = random.randint(100, 3000)
            elif distance < 50:
                target_type = random.choice(["Aircraft", "Helicopter", "Drone"])
                speed = random.randint(250, 600)
                altitude = random.randint(3000, 8000)
            elif distance < 120:
                target_type = random.choice(["Aircraft", "Fighter Jet"])
                speed = random.randint(600, 900)
                altitude = random.randint(8000, 15000)
            else:
                target_type = random.choice(["Aircraft", "Bomber"])
                speed = random.randint(700, 1000)
                altitude = random.randint(10000, 20000)
            
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
            angle_change = random.uniform(-1.5, 1.5)
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
        
        # Remove old targets
        now = datetime.now()
        self.targets = [t for t in self.targets 
                       if (now - t['timestamp']).seconds < 25]
        
        return self.targets

def create_military_radar(targets, scan_angle, range_km, width=800, height=800):
    """Create military-style radar display like the image"""
    
    img = Image.new('RGB', (width, height), color=(0, 10, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width // 2, height // 2)
    max_radius = min(width, height) // 2 - 60
    
    # Draw outer circle
    draw.ellipse([center[0] - max_radius, center[1] - max_radius,
                  center[0] + max_radius, center[1] + max_radius],
                 outline=(0, 200, 0), width=3)
    
    # Draw range rings (at 20%, 40%, 60%, 80%, 100% of range)
    for i in range(1, 6):
        radius = int(max_radius * (i / 5))
        draw.ellipse([center[0] - radius, center[1] - radius,
                      center[0] + radius, center[1] + radius],
                     outline=(0, 80, 0), width=1)
        
        # Range labels
        range_label = int((i / 5) * range_km)
        label_x = center[0] + radius - 30
        label_y = center[1] + 5
        draw.rectangle([label_x-2, label_y-10, label_x+35, label_y+5], fill=(0, 10, 0))
        draw.text((label_x, label_y-8), f"{range_label}km", fill=(0, 150, 0))
    
    # Draw crosshairs
    draw.line([(center[0], center[1] - max_radius), (center[0], center[1] + max_radius)],
              fill=(0, 60, 0), width=1)
    draw.line([(center[0] - max_radius, center[1]), (center[0] + max_radius, center[1])],
              fill=(0, 60, 0), width=1)
    
    # Draw bearing lines and labels (every 45 degrees like in image)
    bearings = [
        (0, "NORTH", 0), (45, "NORTHEAST", 45), (90, "EAST", 90),
        (135, "SOUTHEAST", 135), (180, "SOUTH", 180), (225, "SOUTHWEST", 225),
        (270, "WEST", 270), (315, "NORTHWEST", 315)
    ]
    
    for angle, label, deg in bearings:
        rad = math.radians(angle)
        # Line from inner to outer
        inner_radius = max_radius - 15
        x1 = center[0] + int(inner_radius * math.cos(rad))
        y1 = center[1] + int(inner_radius * math.sin(rad))
        x2 = center[0] + int(max_radius * math.cos(rad))
        y2 = center[1] + int(max_radius * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 100, 0), width=2)
        
        # Label placement
        label_radius = max_radius + 20
        label_x = center[0] + int(label_radius * math.cos(rad))
        label_y = center[1] + int(label_radius * math.sin(rad))
        
        # Adjust for cardinals
        if angle == 0:
            label_x, label_y = center[0] - 25, center[1] - max_radius - 15
        elif angle == 90:
            label_x, label_y = center[0] + max_radius + 10, center[1] - 8
        elif angle == 180:
            label_x, label_y = center[0] - 25, center[1] + max_radius + 10
        elif angle == 270:
            label_x, label_y = center[0] - max_radius - 50, center[1] - 8
        
        draw.text((label_x, label_y), f"{label}\n{deg}°", fill=(0, 200, 0), align="center")
    
    # Draw degree ticks every 45 degrees
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        inner_x = center[0] + int((max_radius - 8) * math.cos(rad))
        inner_y = center[1] + int((max_radius - 8) * math.sin(rad))
        outer_x = center[0] + int(max_radius * math.cos(rad))
        outer_y = center[1] + int(max_radius * math.sin(rad))
        draw.line([(inner_x, inner_y), (outer_x, outer_y)], fill=(0, 150, 0), width=2)
    
    # Draw target trails
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
                
                intensity = int(100 * (i / len(target['history'])))
                draw.line([(prev_x, prev_y), (curr_x, curr_y)], fill=(0, intensity, 0), width=2)
    
    # Draw targets
    for target in targets:
        rad = math.radians(target['angle'])
        distance_ratio = target['distance'] / range_km
        x = center[0] + int(distance_ratio * max_radius * math.cos(rad))
        y = center[1] + int(distance_ratio * max_radius * math.sin(rad))
        
        # Color based on threat/distance
        if target['distance'] < 20:
            color = (255, 0, 0)      # Red - Critical (within 20km)
            size = 10
        elif target['distance'] < 50:
            color = (255, 100, 0)    # Orange - High threat (20-50km)
            size = 9
        elif target['distance'] < 100:
            color = (255, 255, 0)    # Yellow - Medium threat (50-100km)
            size = 8
        else:
            color = (0, 255, 0)      # Green - Low threat (100km+)
            size = 7
        
        # Draw target blip with glow
        for r in range(size + 3, size - 1, -1):
            glow_color = tuple(int(c * 0.5) for c in color)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=glow_color, outline=glow_color)
        
        # Draw target center
        draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color, outline=color)
        
        # Draw target ID
        draw.text((x+8, y-10), f"TG1-{target['id']:03d}", fill=(0, 255, 0))
    
    # Draw scanning beam
    rad = math.radians(scan_angle)
    scan_x = center[0] + int(max_radius * math.cos(rad))
    scan_y = center[1] + int(max_radius * math.sin(rad))
    draw.line([center, (scan_x, scan_y)], fill=(0, 255, 0), width=2)
    
    # Draw scan head
    for r in range(8, 0, -1):
        draw.ellipse([scan_x-r, scan_y-r, scan_x+r, scan_y+r], fill=(0, 255, 0), outline=(0, 255, 0))
    
    # Add compass rose in center
    draw.ellipse([center[0]-20, center[1]-20, center[0]+20, center[1]+20], fill=(0, 20, 0), outline=(0, 100, 0))
    draw.line([(center[0], center[1]-15), (center[0], center[1]+15)], fill=(0, 150, 0), width=1)
    draw.line([(center[0]-15, center[1]), (center[0]+15, center[1])], fill=(0, 150, 0), width=1)
    draw.text((center[0]-4, center[1]-12), "N", fill=(0, 255, 0))
    
    return img

def main():
    # Title section
    st.markdown("""
    <div class="radar-title">
        <h1>360° MILITARY RADAR SYSTEM</h1>
        <p>ALL-ROUND SURVEILLANCE · ALL-WEATHER · HIGH PRECISION</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout: Radar on top, specs and targets below
    col1, col2 = st.columns([2.2, 1])
    
    with col1:
        # Radar display
        radar_container = st.container()
        
    with col2:
        # System specifications panel
        st.markdown("""
        <div class="specs-box">
            <div class="specs-title">SYSTEM SPECIFICATIONS</div>
            <div style="font-family: monospace; font-size: 12px; color: #00aa00;">
                360° SURVEILLANCE DISPLAY<br>
                RADAR TYPE: 3D AESA<br>
                FREQUENCY: X-BAND<br>
                DETECTION RANGE: 200KM<br>
                ALTITUDE RANGE: 100M - 30KM<br>
                ROTATION: 360° CONTINUOUS<br>
                UPDATE RATE: 1SEC<br>
                TARGET TRACKING: 1000+<br>
                OPERATING TEMP: -40°C TO +55°C<br>
                POWER SUPPLY: 24VDC/10KW
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # System status
        st.markdown("""
        <div class="specs-box">
            <div class="specs-title">SYSTEM STATUS</div>
            <div style="font-family: monospace; font-size: 12px;">
                <span style="color: #00ff00;">●</span> RADAR SYSTEM: <span style="color: #00ff00;">OPERATIONAL</span><br>
                <span style="color: #00ff00;">●</span> COMMUNICATIONS: <span style="color: #00ff00;">OPERATIONAL</span><br>
                <span style="color: #00ff00;">●</span> POWER SUPPLY: <span style="color: #00ff00;">OPERATIONAL</span><br>
                <span style="color: #00ff00;">●</span> SIGNAL PROCESSING: <span style="color: #00ff00;">OPERATIONAL</span><br>
                <span style="color: #00ff00;">●</span> SIGNAL STRENGTH: <span style="color: #00ff00;">98%</span><br>
                <span style="color: #00ff00;">●</span> SYSTEM HEALTH: <span style="color: #00ff00;">100%</span><br>
                <span style="color: #00ff00;">●</span> POWER LEVEL: <span style="color: #00ff00;">87%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize radar
    if 'radar' not in st.session_state:
        st.session_state.radar = MilitaryRadar()
        st.session_state.scan_angle = 0
    
    # Update radar
    st.session_state.scan_angle += 3
    if st.session_state.scan_angle >= 360:
        st.session_state.scan_angle = 0
    
    targets = st.session_state.radar.generate_targets()
    
    # Create and display radar image
    radar_img = create_military_radar(targets, st.session_state.scan_angle, 200, width=700, height=700)
    
    with col1:
        st.image(radar_img, use_container_width=True)
    
    # Detected Targets Table
    st.markdown("---")
    st.markdown('<div class="specs-title" style="font-size: 18px;">DETECTED TARGETS</div>', unsafe_allow_html=True)
    
    if targets:
        # Prepare table data
        targets_sorted = sorted(targets, key=lambda x: x['distance'])
        
        table_data = []
        for i, t in enumerate(targets_sorted[:10]):
            # Status based on distance
            if t['distance'] < 20:
                status = "🔴 CRITICAL"
            elif t['distance'] < 50:
                status = "🟠 HIGH"
            elif t['distance'] < 100:
                status = "🟡 MEDIUM"
            else:
                status = "🟢 LOW"
            
            # Get bearing
            bearings = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                       'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            bearing_idx = int((t['angle'] + 11.25) / 22.5) % 16
            bearing = bearings[bearing_idx]
            
            table_data.append({
                "ID": f"TG1-{t['id']:03d}",
                "TYPE": t['type'],
                "RANGE": f"{t['distance']} km",
                "AZIMUTH": f"{bearing} {t['angle']:.0f}°",
                "ALTITUDE": f"{t['altitude']/1000:.1f} km",
                "SPEED": f"{t['speed']} km/h",
                "STATUS": status
            })
        
        # Display as DataFrame
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "TYPE": st.column_config.TextColumn("TYPE", width="small"),
                "RANGE": st.column_config.TextColumn("RANGE", width="small"),
                "AZIMUTH": st.column_config.TextColumn("AZIMUTH", width="small"),
                "ALTITUDE": st.column_config.TextColumn("ALTITUDE", width="small"),
                "SPEED": st.column_config.TextColumn("SPEED", width="small"),
                "STATUS": st.column_config.TextColumn("STATUS", width="medium"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Summary stats
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Targets", len(targets))
        with col2:
            critical = len([t for t in targets if t['distance'] < 20])
            st.metric("Critical (<20km)", critical)
        with col3:
            aircraft = len([t for t in targets if t['type'] == "Aircraft"])
            st.metric("Aircraft", aircraft)
        with col4:
            drones = len([t for t in targets if t['type'] in ["Drone", "UAV"]])
            st.metric("Drones/UAVs", drones)
        with col5:
            closest = min(targets, key=lambda x: x['distance'])
            st.metric("Closest Target", f"{closest['distance']} km")
    else:
        st.info("No targets detected")
    
    # Auto-refresh for animation
    time.sleep(0.05)
    st.rerun()

if __name__ == "__main__":
    main()
