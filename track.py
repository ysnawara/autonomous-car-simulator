"""
Track generation - stadium/oval shape
"""

import pygame
import numpy as np
from scipy import interpolate
from config import *


class Track:
    """Stadium-shaped track"""
    
    def __init__(self):
        self.centerline = self._generate_stadium_track()
        self.inner_boundary = []
        self.outer_boundary = []
        self._generate_boundaries()
        
    def _generate_stadium_track(self):
        """Generate stadium track shape"""
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2
        
        width = WINDOW_WIDTH * 0.65
        height = WINDOW_HEIGHT * 0.55
        
        w = width / 2
        h = height / 2
        r = h
        straight_len = w - r
        
        points = []
        num_curve = 80
        num_straight = 80
        
        # Top straight
        p_top_start = (cx - straight_len, cy - r)
        p_top_end = (cx + straight_len, cy - r)
        
        for i in range(num_straight):
            t = i / num_straight
            x = p_top_start[0] + (p_top_end[0] - p_top_start[0]) * t
            y = p_top_start[1]
            points.append((x, y))
            
        # Right semicircle
        for i in range(num_curve):
            angle = -np.pi/2 + (np.pi * i / num_curve)
            x = (cx + straight_len) + r * np.cos(angle)
            y = cy + r * np.sin(angle)
            points.append((x, y))
            
        # Bottom straight
        p_bot_start = (cx + straight_len, cy + r)
        p_bot_end = (cx - straight_len, cy + r)
        
        for i in range(num_straight):
            t = i / num_straight
            x = p_bot_start[0] + (p_bot_end[0] - p_bot_start[0]) * t
            y = p_bot_start[1]
            points.append((x, y))
            
        # Left semicircle
        for i in range(num_curve):
            angle = np.pi/2 + (np.pi * i / num_curve)
            x = (cx - straight_len) + r * np.cos(angle)
            y = cy + r * np.sin(angle)
            points.append((x, y))
            
        return points
    
    def _generate_boundaries(self):
        """Generate inner and outer track boundaries"""
        half_road = ROAD_WIDTH // 2
        n = len(self.centerline)
        
        for i in range(n):
            prev_idx = (i - 1) % n
            next_idx = (i + 1) % n
            
            prev_pt = np.array(self.centerline[prev_idx])
            curr_pt = np.array(self.centerline[i])
            next_pt = np.array(self.centerline[next_idx])
            
            tangent = (next_pt - prev_pt)
            length = np.linalg.norm(tangent)
            if length > 0:
                tangent = tangent / length
            
            normal = np.array([-tangent[1], tangent[0]])
            
            inner = curr_pt + normal * half_road
            outer = curr_pt - normal * half_road
            
            self.inner_boundary.append(tuple(inner))
            self.outer_boundary.append(tuple(outer))
    
    def get_start_position(self):
        """Get starting position"""
        start_idx = 10
        start_pos = self.centerline[start_idx]
        
        next_idx = (start_idx + 5) % len(self.centerline)
        next_pos = self.centerline[next_idx]
        dx = next_pos[0] - start_pos[0]
        dy = next_pos[1] - start_pos[1]
        angle = np.degrees(np.arctan2(dy, dx))
        
        return start_pos[0], start_pos[1], angle
    
    def render(self, screen):
        """Render the track"""
        # Dark background
        screen.fill((25, 30, 35))
        
        # Grass
        grass_color = (30, 50, 35)
        pygame.draw.rect(screen, grass_color, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Gravel runoff
        if len(self.outer_boundary) > 2:
            all_x = [p[0] for p in self.centerline]
            all_y = [p[1] for p in self.centerline]
            cx = sum(all_x) / len(all_x)
            cy = sum(all_y) / len(all_y)
            
            gravel_outer = []
            for pt in self.outer_boundary:
                dx = pt[0] - cx
                dy = pt[1] - cy
                length = np.sqrt(dx*dx + dy*dy)
                if length > 0:
                    gravel_outer.append((pt[0] + dx/length * 20, pt[1] + dy/length * 20))
            
            if len(gravel_outer) > 2:
                gravel_polygon = gravel_outer + list(reversed(self.outer_boundary))
                pygame.draw.polygon(screen, (55, 50, 45), gravel_polygon)
        
        # Road surface
        if len(self.inner_boundary) > 2 and len(self.outer_boundary) > 2:
            road_points = list(self.outer_boundary) + list(reversed(self.inner_boundary))
            pygame.draw.polygon(screen, TRACK_ASPHALT, road_points)
        
        # Green boundary lines
        if len(self.inner_boundary) > 1:
            inner_int = [(int(p[0]), int(p[1])) for p in self.inner_boundary]
            pygame.draw.lines(screen, BOUNDARY_COLOR, True, inner_int, BOUNDARY_WIDTH)
        
        if len(self.outer_boundary) > 1:
            outer_int = [(int(p[0]), int(p[1])) for p in self.outer_boundary]
            pygame.draw.lines(screen, BOUNDARY_COLOR, True, outer_int, BOUNDARY_WIDTH)
        
        # Start/finish line
        start_idx = 10
        p1 = self.inner_boundary[start_idx]
        p2 = self.outer_boundary[start_idx]
        pygame.draw.line(screen, WHITE, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 4)
