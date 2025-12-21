"""
Vision-based Pure Pursuit controller
Uses OpenCV for lane detection from camera view
"""

import cv2
import numpy as np
import pygame
from config import *


class VisionSystem:
    """OpenCV lane detection"""
    
    def __init__(self):
        # Green color range for boundary detection
        self.green_lower = np.array([35, 80, 80])
        self.green_upper = np.array([85, 255, 255])
        
        self.cam_width = 480
        self.cam_height = 320
        
        self.lane_center = None
        self.left_boundary = None
        self.right_boundary = None
        self.camera_frame = None
        self.processed_frame = None
        
    def get_camera_pov(self, full_frame, car_x, car_y, car_angle):
        """
        Extract first-person camera view from car perspective using perspective warping.
        
        Args:
            full_frame: The global top-down view of the track.
            car_x, car_y: Current car coordinates.
            car_angle: Car heading in degrees.
            
        Returns:
            Warpped OpenCV frame representing the driver's POV.
        """
        h, w = full_frame.shape[:2]
        
        heading_rad = np.radians(car_angle)
        
        # Perspective Trapezoid Settings
        # These define the 'field of view' in front of the car
        near_dist = 20         # Start of the camera's view (in pixels)
        far_dist = 800         # How far the camera can see
        near_half_width = 80   # Width of view at the front bumper
        far_half_width = 1000  # Width of view at the horizon (simulates perspective)
        
        cos_h = np.cos(heading_rad)
        sin_h = np.sin(heading_rad)
        cos_perp = np.cos(heading_rad + np.pi/2)
        sin_perp = np.sin(heading_rad + np.pi/2)
        
        # Define the four points of the trapezoid in global coordinates
        # 1. Front-Left, 2. Front-Right, 3. Far-Right, 4. Far-Left
        src_points = np.float32([
            [car_x + near_dist * cos_h - near_half_width * cos_perp,
             car_y + near_dist * sin_h - near_half_width * sin_perp],
            [car_x + near_dist * cos_h + near_half_width * cos_perp,
             car_y + near_dist * sin_h + near_half_width * sin_perp],
            [car_x + far_dist * cos_h + far_half_width * cos_perp,
             car_y + far_dist * sin_h + far_half_width * sin_perp],
            [car_x + far_dist * cos_h - far_half_width * cos_perp,
             car_y + far_dist * sin_h - far_half_width * sin_perp],
        ])
        
        # Map these global points to the fixed camera frame size (rectanglar)
        dst_points = np.float32([
            [0, self.cam_height],
            [self.cam_width, self.cam_height],
            [self.cam_width, 0],
            [0, 0],
        ])
        
        # Calculate transform and warp the image
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        camera_view = cv2.warpPerspective(full_frame, matrix, (self.cam_width, self.cam_height))
        
        return camera_view
    
    def process_camera_view(self, camera_frame):
        """
        Detect lane boundaries and compute center deviation using HSV thresholding.
        
        Logic:
        1. Convert to HSV and isolate the green boundary lines.
        2. Scan multiple horizontal rows to find left/right boundary points.
        3. Average the centers of those rows to get a stable target path.
        """
        hsv = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2HSV)
        
        # Isolate green boundary pixels
        mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        
        # Morphological operations to remove noise/gaps
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Create visual overlay for the 'Driver View' UI
        self.processed_frame = camera_frame.copy()
        green_highlight = np.zeros_like(camera_frame)
        green_highlight[mask > 0] = [0, 255, 255] # Cyan glow for detected lanes
        self.processed_frame = cv2.addWeighted(self.processed_frame, 0.7, green_highlight, 0.5, 0)
        
        # Find lane center at multiple rows (Scanlines)
        h, w = mask.shape
        lane_centers = []
        
        # Sample at 80% (close), 60% (mid), 40% (far), 30% (horizon) height
        for row_pct in [0.8, 0.6, 0.4, 0.3]:
            row = int(h * row_pct)
            if row < 0 or row >= h:
                continue
            
            row_data = mask[row, :]
            green_pixels = np.where(row_data > 0)[0]
            
            if len(green_pixels) >= 2:
                # Find the horizontal bounds of the lane
                left = green_pixels.min()
                right = green_pixels.max()
                center = (left + right) / 2 / w # Normalize to 0-1
                lane_centers.append(center)
                
                # Draw visual debug markers
                cv2.circle(self.processed_frame, (int(center * w), row), 5, (255, 0, 255), -1) # Center point
                cv2.circle(self.processed_frame, (left, row), 3, (0, 255, 0), -1) # Left edge
                cv2.circle(self.processed_frame, (right, row), 3, (0, 255, 0), -1) # Right edge
        
        # Visual guide for true center
        cv2.line(self.processed_frame, (w // 2, 0), (w // 2, h), (0, 100, 255), 1)
        cv2.putText(self.processed_frame, "LANE SENSORS: ACTIVE", (10, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if lane_centers:
            # Weighted average: prioritize closer lane information for immediate steering
            weights = [0.4, 0.3, 0.2, 0.1][:len(lane_centers)]
            self.lane_center = sum(c * w for c, w in zip(lane_centers, weights)) / sum(weights)
            return self.lane_center
        
        # Default to center if no lanes detected
        return 0.5
    
    def process_frame(self, pygame_surface, car_x, car_y, car_angle):
        """Full pipeline: get camera view and process lanes"""
        # Convert pygame to OpenCV format
        frame = pygame.surfarray.array3d(pygame_surface)
        frame = np.transpose(frame, (1, 0, 2))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        self.camera_frame = self.get_camera_pov(frame, car_x, car_y, car_angle)
        lane_center = self.process_camera_view(self.camera_frame)
        
        return lane_center
    
    def get_display_frame(self):
        """Get processed frame for UI"""
        if self.processed_frame is not None:
            return self.processed_frame
        return self.camera_frame


class VisionPurePursuit:
    """Vision-based Pure Pursuit controller"""
    
    def __init__(self, look_ahead_distance=LOOK_AHEAD_DISTANCE):
        self.look_ahead_distance = look_ahead_distance
        self.vision = VisionSystem()
        self.lane_center = 0.5
        self.steering_error = 0
        self.viz_lookahead_point = None
        
    def calculate_steering(self, car, pygame_surface):
        """Calculate steering from vision"""
        self.lane_center = self.vision.process_frame(
            pygame_surface, car.x, car.y, car.angle
        )
        
        # Visualization point
        heading_rad = np.radians(car.angle)
        look_dist = self.look_ahead_distance * 4
        steering_rad = np.radians(car.steering_angle)
        
        lx = car.x + look_dist * np.cos(heading_rad + steering_rad)
        ly = car.y + look_dist * np.sin(heading_rad + steering_rad)
        self.viz_lookahead_point = (lx, ly)
        
        # Steering error from center
        self.steering_error = self.lane_center - 0.5
        
        # Pure pursuit steering
        GAIN_CONSTANT = 3000
        safe_look_ahead = max(self.look_ahead_distance, 1.0)
        steering = self.steering_error * (GAIN_CONSTANT / safe_look_ahead)
        
        return np.clip(steering, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE)
    
    def get_camera_view(self):
        """Get camera frame for display"""
        return self.vision.get_display_frame()
    
    def get_name(self):
        return "Pure Pursuit (Vision)"


class SpeedController:
    """Speed controller that slows for turns"""
    
    def __init__(self):
        self.target_speed = MAX_SPEED
        
    def calculate_speed(self, steering_angle, base_speed):
        """Reduce speed based on steering angle"""
        steering_factor = 1 - (abs(steering_angle) / MAX_STEERING_ANGLE) * 0.4
        return base_speed * max(steering_factor, 0.5)
