# app.py
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
import os

# Page configuration
st.set_page_config(
    page_title="Flying Object Detection System",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: rgba(0,0,0,0.7);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .detection-card {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }
    .metric-card {
        background: rgba(0,0,0,0.5);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .object-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin: 0.2rem;
        border-radius: 5px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 0.8rem;
    }
    .warning-box {
        background: rgba(255,100,100,0.2);
        border-left: 4px solid #ff4444;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background: rgba(100,100,255,0.2);
        border-left: 4px solid #4444ff;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class FlyingObjectDetector:
    def __init__(self):
        self.tracked_objects = {}
        self.next_id = 0
        self.object_history = {}
        self.detection_history = []
        self.fgbg = None
        self.prev_gray = None
        self.initialized = False
        
    def initialize_background_subtractor(self, frame_shape):
        """Initialize background subtractor with frame shape"""
        if self.fgbg is None:
            self.fgbg = cv2.createBackgroundSubtractorMOG2(
                history=500, 
                varThreshold=16, 
                detectShadows=True
            )
            self.initialized = True
        
    def detect_flying_objects(self, frame, sensitivity=0.5):
        """Detect moving objects in frame"""
        if frame is None or frame.size == 0:
            return []
        
        # Initialize background subtractor if needed
        if self.fgbg is None:
            self.initialize_background_subtractor(frame.shape)
        
        try:
            # Apply background subtraction
            fgmask = self.fgbg.apply(frame)
            
            # Apply threshold based on sensitivity
            threshold = int(20 * (1 - sensitivity))
            _, fgmask = cv2.threshold(fgmask, threshold, 255, cv2.THRESH_BINARY)
            
            # Remove noise
            fgmask = cv2.medianBlur(fgmask, 5)
            
            # Morphological operations to clean up
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
                    
                    # Classify object type based on shape and size
                    object_type = self.classify_object(w, h, area)
                    
                    detections.append({
                        'id': -1,  # Will be assigned during tracking
                        'bbox': (x, y, x+w, y+h),
                        'center': (x + w//2, y + h//2),
                        'area': area,
                        'width': w,
                        'height': h,
                        'type': object_type,
                        'confidence': min(0.95, area / 1000),
                        'timestamp': datetime.now()
                    })
            
            # Track objects
            tracked = self.track_objects(detections)
            
            # Update history
            self.detection_history.append({
                'timestamp': datetime.now(),
                'count': len(tracked),
                'objects': tracked.copy()
            })
            
            # Keep only last 500 detections
            if len(self.detection_history) > 500:
                self.detection_history = self.detection_history[-500:]
            
            return tracked
            
        except Exception as e:
            st.warning(f"Detection error: {str(e)}")
            return []
    
    def classify_object(self, width, height, area):
        """Classify the type of flying object"""
        aspect_ratio = width / height if height > 0 else 1
        
        # Size-based classification
        if area > 3000:
            if aspect_ratio > 1.8:
                return "Large Airplane"
            else:
                return "Helicopter"
        elif area > 1500:
            if aspect_ratio > 1.5:
                return "Small Airplane"
            else:
                return "Large Drone"
        elif area > 800:
            if aspect_ratio > 1.3:
                return "Medium Drone"
            else:
                return "Large Bird"
        elif area > 300:
            if aspect_ratio > 1.2:
                return "Small Drone"
            else:
                return "Medium Bird"
        elif area > 100:
            if aspect_ratio > 1.5:
                return "Small Bird"
            else:
                return "Bat/Insect"
        else:
            if aspect_ratio > 2:
                return "Distant Bird"
            else:
                return "Unknown Flying Object"
    
    def track_objects(self, detections):
        """Track objects across frames"""
        tracked_objects = []
        
        if not detections:
            # Still need to clean up old objects
            self.cleanup_old_objects()
            return tracked_objects
        
        for detection in detections:
            matched = False
            best_match_id = None
            best_distance = float('inf')
            
            # Try to match with existing objects
            for obj_id, obj in list(self.tracked_objects.items()):
                if obj.get('center'):
                    distance = np.sqrt(
                        (detection['center'][0] - obj['center'][0])**2 + 
                        (detection['center'][1] - obj['center'][1])**2
                    )
                    
                    # Type similarity bonus
                    type_bonus = 20 if obj.get('type') == detection['type'] else 0
                    adjusted_distance = distance - type_bonus
                    
                    if adjusted_distance < 50 and adjusted_distance < best_distance:
                        best_distance = adjusted_distance
                        best_match_id = obj_id
                        matched = True
            
            if matched and best_match_id is not None:
                # Update existing object
                obj = self.tracked_objects[best_match_id]
                self.tracked_objects[best_match_id] = {
                    'center': detection['center'],
                    'bbox': detection['bbox'],
                    'type': detection['type'],
                    'last_seen': datetime.now(),
                    'confidence': detection['confidence'],
                    'track_length': obj.get('track_length', 0) + 1,
                    'first_seen': obj.get('first_seen', datetime.now())
                }
                detection['id'] = best_match_id
            else:
                # Create new object
                detection['id'] = self.next_id
                self.tracked_objects[self.next_id] = {
                    'center': detection['center'],
                    'bbox': detection['bbox'],
                    'type': detection['type'],
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'confidence': detection['confidence'],
                    'track_length': 1
                }
                self.next_id += 1
            
            # Store history for trails
            if detection['id'] not in self.object_history:
                self.object_history[detection['id']] = deque(maxlen=30)
            self.object_history[detection['id']].append(detection['center'])
            
            tracked_objects.append(detection)
        
        # Clean up old objects
        self.cleanup_old_objects()
        
        return tracked_objects
    
    def cleanup_old_objects(self):
        """Remove objects not seen recently"""
        current_time = datetime.now()
        to_remove = []
        
        for obj_id, obj in self.tracked_objects.items():
            time_diff = (current_time - obj['last_seen']).total_seconds()
            if time_diff > 2.0:  # Remove after 2 seconds
                to_remove.append(obj_id)
        
        for obj_id in to_remove:
            del self.tracked_objects[obj_id]
            if obj_id in self.object_history:
                del self.object_history[obj_id]
    
    def draw_detections(self, frame, detections, show_trails=True, show_boxes=True, show_labels=True):
        """Draw detections on frame"""
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        display_frame = frame.copy()
        
        # Color map for different object types
        colors = {
            "Large Airplane": (0, 255, 0),      # Green
            "Small Airplane": (50, 200, 50),    # Light Green
            "Helicopter": (255, 255, 0),        # Cyan
            "Large Drone": (0, 165, 255),       # Orange
            "Medium Drone": (50, 150, 255),     # Light Orange
            "Small Drone": (100, 135, 255),     # Yellow-Orange
            "Large Bird": (255, 0, 0),          # Blue
            "Medium Bird": (200, 50, 50),       # Light Blue
            "Small Bird": (150, 100, 100),      # Lighter Blue
            "Bat/Insect": (0, 255, 255),        # Yellow
            "Distant Bird": (255, 100, 0),      # Light Blue-Green
            "Unknown Flying Object": (255, 255, 255)  # White
        }
        
        # Draw trails first (behind bounding boxes)
        if show_trails:
            for detection in detections:
                obj_id = detection['id']
                if obj_id in self.object_history:
                    trail = list(self.object_history[obj_id])
                    color = colors.get(detection['type'], (255, 255, 255))
                    
                    # Draw trail lines
                    for i in range(1, len(trail)):
                        alpha = i / len(trail)
                        trail_color = (
                            int(color[0] * alpha),
                            int(color[1] * alpha),
                            int(color[2] * alpha)
                        )
                        thickness = max(1, int(3 * alpha))
                        cv2.line(display_frame, trail[i-1], trail[i], trail_color, thickness)
        
        # Draw bounding boxes and labels
        for detection in detections:
            bbox = detection['bbox']
            obj_type = detection['type']
            confidence = detection['confidence']
            obj_id = detection['id']
            
            color = colors.get(obj_type, (255, 255, 255))
            
            if show_boxes:
                # Draw bounding box
                cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                
                # Draw center point
                cv2.circle(display_frame, detection['center'], 4, color, -1)
                
                # Draw confidence circle
                radius = int(15 * confidence)
                cv2.circle(display_frame, detection['center'], radius, color, 1)
            
            if show_labels:
                # Create label text
                label = f"ID:{obj_id} {obj_type}"
                if confidence > 0:
                    label += f" ({confidence:.0%})"
                
                # Calculate text size
                font_scale = 0.4
                thickness = 1
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
                )
                
                # Draw label background
                label_y = max(bbox[1] - 5, text_height + 10)
                cv2.rectangle(display_frame,
                            (bbox[0], label_y - text_height - 5),
                            (bbox[0] + text_width + 5, label_y + 5),
                            color, -1)
                
                # Draw label text
                cv2.putText(display_frame, label,
                          (bbox[0] + 2, label_y),
                          cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
                
                # Draw track length if significant
                if detection['id'] in self.tracked_objects:
                    track_length = self.tracked_objects[detection['id']].get('track_length', 0)
                    if track_length > 10:
                        track_label = f"Track: {track_length}f"
                        cv2.putText(display_frame, track_label,
                                  (bbox[0], bbox[3] + 15),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
        
        # Add info overlay
        active_count = len(detections)
        total_tracked = len(self.tracked_objects)
        
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (5, 5), (250, 70), (0, 0, 0), -1)
        display_frame = cv2.addWeighted(overlay, 0.3, display_frame, 0.7, 0)
        
        cv2.putText(display_frame, f"Active Objects: {active_count}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display_frame, f"Total Tracked: {total_tracked}", (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return display_frame
    
    def reset(self):
        """Reset the detector state"""
        self.tracked_objects = {}
        self.next_id = 0
        self.object_history = {}
        self.detection_history = []
        self.fgbg = None
        self.prev_gray = None
        self.initialized = False

def initialize_session_state():
    """Initialize all session state variables"""
    if 'detector' not in st.session_state:
        st.session_state.detector = FlyingObjectDetector()
    
    if 'detection_log' not in st.session_state:
        st.session_state.detection_log = []
    
    if 'is_detecting' not in st.session_state:
        st.session_state.is_detecting = False
    
    if 'frame_count' not in st.session_state:
        st.session_state.frame_count = 0
    
    if 'fps' not in st.session_state:
        st.session_state.fps = 0
    
    if 'last_time' not in st.session_state:
        st.session_state.last_time = time.time()
    
    if 'cap' not in st.session_state:
        st.session_state.cap = None
    
    if 'sim_objects' not in st.session_state:
        st.session_state.sim_objects = []

def create_simulation_objects():
    """Create random objects for simulation mode"""
    if not st.session_state.sim_objects:
        object_types = ['Airplane', 'Drone', 'Bird', 'Helicopter']
        for _ in range(random.randint(2, 6)):
            st.session_state.sim_objects.append({
                'pos': [random.randint(100, 540), random.randint(100, 380)],
                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                'type': random.choice(object_types),
                'size': random.randint(15, 40)
            })

def update_simulation_frame(frame):
    """Update frame with simulated flying objects"""
    if frame is None or frame.size == 0:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (30, 30, 50)  # Dark blue background
    
    # Create or update simulation objects
    create_simulation_objects()
    
    # Update and draw objects
    for obj in st.session_state.sim_objects:
        # Update position
        obj['pos'][0] += obj['vel'][0]
        obj['pos'][1] += obj['vel'][1]
        
        # Bounce off edges with damping
        if obj['pos'][0] < 50 or obj['pos'][0] > 590:
            obj['vel'][0] = -obj['vel'][0] * 0.95
            obj['pos'][0] = max(50, min(590, obj['pos'][0]))
        
        if obj['pos'][1] < 50 or obj['pos'][1] > 430:
            obj['vel'][1] = -obj['vel'][1] * 0.95
            obj['pos'][1] = max(50, min(430, obj['pos'][1]))
        
        # Draw object with different shapes based on type
        center = tuple(map(int, obj['pos']))
        
        if obj['type'] == 'Airplane':
            # Draw airplane shape
            pts = np.array([
                center,
                (center[0] - obj['size'], center[1] - obj['size']//2),
                (center[0] - obj['size']//2, center[1]),
                (center[0] - obj['size'], center[1] + obj['size']//2)
            ], np.int32)
            cv2.fillPoly(frame, [pts], (0, 255, 0))
            cv2.circle(frame, center, obj['size']//3, (0, 200, 0), -1)
            
        elif obj['type'] == 'Drone':
            # Draw drone (quadcopter shape)
            cv2.circle(frame, center, obj['size']//2, (0, 165, 255), -1)
            for angle in [0, 90, 180, 270]:
                rad = np.radians(angle)
                arm_end = (int(center[0] + obj['size'] * np.cos(rad)),
                          int(center[1] + obj['size'] * np.sin(rad)))
                cv2.line(frame, center, arm_end, (0, 165, 255), 2)
                cv2.circle(frame, arm_end, obj['size']//4, (0, 165, 255), -1)
                
        elif obj['type'] == 'Bird':
            # Draw bird shape
            cv2.ellipse(frame, center, (obj['size'], obj['size']//2), 
                       0, 0, 360, (255, 100, 0), -1)
            # Wing
            wing_angle = 30 * np.sin(time.time() * 10)
            wing_end = (int(center[0] + obj['size'] * np.cos(np.radians(wing_angle))),
                       int(center[1] - obj['size']//2))
            cv2.line(frame, center, wing_end, (255, 100, 0), 3)
            
        else:  # Helicopter
            cv2.ellipse(frame, center, (obj['size']//2, obj['size']), 
                       0, 0, 360, (255, 255, 0), -1)
            # Rotor
            rotor_angle = time.time() * 50
            rotor_end1 = (int(center[0] + obj['size'] * np.cos(rotor_angle)),
                         int(center[1] + obj['size'] * np.sin(rotor_angle)))
            rotor_end2 = (int(center[0] - obj['size'] * np.cos(rotor_angle)),
                         int(center[1] - obj['size'] * np.sin(rotor_angle)))
            cv2.line(frame, rotor_end1, rotor_end2, (255, 255, 0), 2)
        
        # Add label
        cv2.putText(frame, obj['type'], 
                   (center[0] - 20, center[1] - obj['size']//2 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    return frame

def main():
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🛸 Advanced Flying Object Detection System")
    st.markdown("### Real-time Detection of Airplanes, Drones, Birds, and Other Flying Objects")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎮 Controls")
        
        # Input source selection
        source_option = st.radio(
            "Select Input Source",
            ["📹 Webcam", "🎥 Simulation Mode", "📁 Upload Video"],
            help="Webcam requires browser permission. Simulation creates random flying objects."
        )
        
        st.markdown("---")
        st.markdown("## ⚙️ Detection Settings")
        
        sensitivity = st.slider(
            "Detection Sensitivity", 
            0.1, 1.0, 0.5, 0.05,
            help="Higher sensitivity detects more objects but may increase false positives"
        )
        
        min_object_size = st.slider(
            "Minimum Object Size", 
            50, 500, 100, 10,
            help="Ignore objects smaller than this size (in pixels)"
        )
        
        st.markdown("---")
        st.markdown("## 🎨 Display Options")
        
        show_trails = st.checkbox("Show Movement Trails", True)
        show_boxes = st.checkbox("Show Bounding Boxes", True)
        show_labels = st.checkbox("Show Labels", True)
        show_stats = st.checkbox("Show Statistics Panel", True)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Detector", use_container_width=True):
            st.session_state.detector.reset()
            st.session_state.detection_log = []
            st.session_state.sim_objects = []
            st.success("Detector reset successfully!")
        
        st.markdown("---")
        st.markdown("## 📊 About")
        st.info("""
        **Detected Object Types:**
        - ✈️ Large/Small Airplanes
        - 🚁 Helicopters
        - 🛸 Large/Medium/Small Drones
        - 🐦 Large/Medium/Small Birds
        - 🦋 Bats & Insects
        - 🎯 Distant Objects
        
        **Features:**
        - Real-time motion detection
        - Multi-object tracking
        - Movement trail visualization
        - Object classification by size/shape
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📹 Detection Feed")
        video_placeholder = st.empty()
        
        # Status indicators
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            detection_status = st.empty()
        with status_col2:
            object_count = st.empty()
        with status_col3:
            fps_display = st.empty()
    
    with col2:
        st.markdown("## 📋 Live Detection Log")
        log_placeholder = st.empty()
        
        if show_stats:
            st.markdown("## 📈 Current Objects")
            stats_placeholder = st.empty()
    
    # Handle video source
    cap = None
    
    if source_option == "📹 Webcam":
        st.info("📸 Webcam mode - Click 'Start Detection' to begin")
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.warning("⚠️ Webcam not accessible. Using simulation mode instead.")
                cap = None
                source_option = "🎥 Simulation Mode"
        except:
            st.warning("⚠️ Webcam error. Using simulation mode instead.")
            cap = None
            source_option = "🎥 Simulation Mode"
    
    elif source_option == "📁 Upload Video":
        uploaded_file = st.file_uploader(
            "Choose a video file", 
            type=['mp4', 'avi', 'mov', 'mkv', 'mpg', 'mpeg']
        )
        if uploaded_file is not None:
            # Save temporary file
            temp_path = "temp_video.mp4"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            cap = cv2.VideoCapture(temp_path)
            st.success(f"✅ Loaded: {uploaded_file.name}")
        else:
            cap = None
    
    else:  # Simulation Mode
        st.info("🎮 Simulation mode - Random flying objects will be generated")
        cap = None
    
    # Start/Stop buttons
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("🚀 Start Detection", type="primary", use_container_width=True):
            st.session_state.is_detecting = True
            st.session_state.detection_log = []
            st.session_state.frame_count = 0
            st.session_state.last_time = time.time()
            st.rerun()
    
    with btn_col2:
        if st.button("⏹️ Stop Detection", type="secondary", use_container_width=True):
            st.session_state.is_detecting = False
            if st.session_state.cap:
                st.session_state.cap.release()
                st.session_state.cap = None
            st.rerun()
    
    with btn_col3:
        if st.button("🗑️ Clear Log", use_container_width=True):
            st.session_state.detection_log = []
            st.success("Log cleared!")
    
    # Detection loop
    if st.session_state.is_detecting:
        frame_placeholder = st.empty()
        last_frame_time = time.time()
        
        # Create a container for the loop
        loop_container = st.empty()
        
        while st.session_state.is_detecting:
            loop_start = time.time()
            
            # Get frame from source
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    if source_option == "📁 Upload Video":
                        # Loop video
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        st.warning("End of video reached")
                        st.session_state.is_detecting = False
                        break
            else:
                # Simulation mode
                if frame_placeholder.empty():
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    frame[:] = (30, 30, 50)
                else:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    frame[:] = (30, 30, 50)
                
                frame = update_simulation_frame(frame)
            
            # Calculate FPS
            st.session_state.frame_count += 1
            current_time = time.time()
            time_diff = current_time - st.session_state.last_time
            
            if time_diff >= 1.0:
                st.session_state.fps = st.session_state.frame_count
                st.session_state.frame_count = 0
                st.session_state.last_time = current_time
            
            # Detect objects (only in non-simulation mode or for demo)
            if source_option != "🎥 Simulation Mode":
                detections = st.session_state.detector.detect_flying_objects(frame, sensitivity)
            else:
                # In simulation mode, treat simulation objects as detections
                detections = []
                for i, sim_obj in enumerate(st.session_state.sim_objects):
                    # Create detection from simulation object
                    pos = sim_obj['pos']
                    size = sim_obj['size']
                    detections.append({
                        'id': i,
                        'bbox': (int(pos[0]-size), int(pos[1]-size), 
                                int(pos[0]+size), int(pos[1]+size)),
                        'center': (int(pos[0]), int(pos[1])),
                        'area': size * size,
                        'width': size * 2,
                        'height': size * 2,
                        'type': sim_obj['type'],
                        'confidence': 0.85,
                        'timestamp': datetime.now()
                    })
            
            # Filter by size
            detections = [d for d in detections if d['area'] >= min_object_size]
            
            # Draw on frame
            if source_option != "🎥 Simulation Mode":
                display_frame = st.session_state.detector.draw_detections(
                    frame, detections, show_trails, show_boxes, show_labels
                )
            else:
                # For simulation, just show the frame with labels
                display_frame = frame
                
                # Add overlay info
                cv2.putText(display_frame, f"SIMULATION MODE", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(display_frame, f"Objects: {len(detections)}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Update status displays
            detection_status.metric("Detection Status", 
                                   "🟢 Active" if detections else "🟡 Monitoring")
            object_count.metric("Objects Detected", len(detections))
            fps_display.metric("FPS", st.session_state.fps)
            
            # Log detections
            for detection in detections:
                log_entry = {
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'ID': detection['id'],
                    'Type': detection['type'],
                    'Confidence': f"{detection.get('confidence', 0):.2f}",
                    'Area': detection.get('area', 0)
                }
                st.session_state.detection_log.append(log_entry)
                
                # Keep only last 100 entries
                if len(st.session_state.detection_log) > 100:
                    st.session_state.detection_log = st.session_state.detection_log[-100:]
            
            # Update log display
            if st.session_state.detection_log:
                log_df = pd.DataFrame(st.session_state.detection_log[-10:])
                log_placeholder.dataframe(log_df, use_container_width=True)
            
            # Update statistics
            if show_stats and detections:
                stats_data = []
                type_counts = {}
                
                for detection in detections:
                    obj_type = detection['type']
                    type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
                    
                    stats_data.append({
                        'ID': detection['id'],
                        'Type': detection['type'],
                        'Confidence': f"{detection.get('confidence', 0):.2f}",
                        'Area': detection.get('area', 0)
                    })
                
                # Show statistics
                stats_html = '<div class="detection-card">'
                stats_html += '<h4>📊 Object Breakdown</h4>'
                stats_html += '<div>'
                for obj_type, count in type_counts.items():
                    stats_html += f'<span class="object-badge">{obj_type}: {count}</span>'
                stats_html += '</div></div>'
                stats_placeholder.markdown(stats_html, unsafe_allow_html=True)
                
                # Show detailed table in expander
                with st.expander("Show Detailed Table"):
                    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            
            # Convert to RGB for display
            display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(display_frame_rgb, channels="RGB", use_container_width=True)
            
            # Control frame rate (target 30 FPS)
            loop_time = time.time() - loop_start
            sleep_time = max(0, 0.033 - loop_time)  # ~30 FPS
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Check if we should continue (allows stop button to work)
            if not st.session_state.is_detecting:
                break
    
    # Release resources when done
    if cap is not None:
        cap.release()
    
    # Footer
    st.markdown("---")
    st.markdown("### 🎯 Key Features")
    feature_cols = st.columns(4)
    with feature_cols[0]:
        st.markdown("✅ **Real-time Detection**")
        st.markdown("*Instant object identification*")
    with feature_cols[1]:
        st.markdown("✅ **Multi-object Tracking**")
        st.markdown("*Track multiple objects simultaneously*")
    with feature_cols[2]:
        st.markdown("✅ **Motion Analysis**")
        st.markdown("*Movement trails and patterns*")
    with feature_cols[3]:
        st.markdown("✅ **Smart Classification**")
        st.markdown("*9+ flying object types*")
    
    # Show detection history graph
    if len(st.session_state.detector.detection_history) > 1:
        st.markdown("## 📈 Detection History")
        
        # Prepare data for graph
        hist_data = []
        for h in st.session_state.detector.detection_history[-50:]:
            if isinstance(h, dict) and 'timestamp' in h and 'count' in h:
                hist_data.append({
                    'Time': h['timestamp'].strftime("%H:%M:%S"),
                    'Count': h['count']
                })
        
        if hist_data:
            hist_df = pd.DataFrame(hist_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_df['Time'],
                y=hist_df['Count'],
                mode='lines+markers',
                name='Objects Detected',
                line=dict(color='cyan', width=2),
                marker=dict(size=4, color='yellow')
            ))
            fig.update_layout(
                title="Objects Detected Over Time",
                xaxis_title="Time",
                yaxis_title="Number of Objects",
                height=300,
                plot_bgcolor='rgba(0,0,0,0.3)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Show camera permissions info if needed
    if source_option == "📹 Webcam" and not st.session_state.is_detecting:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **📸 Webcam Setup:**
        1. Click 'Start Detection' above
        2. Allow camera permissions when prompted by your browser
        3. Make sure no other application is using your camera
        4. For best results, ensure good lighting
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
