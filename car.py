"""
Car physics - bicycle model with F1-style rendering
"""

import pygame
import numpy as np
from config import *


class Car:
    """Car with bicycle model physics"""
    
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        
        self.speed = 2.5
        self.steering_angle = 0
        
        self.length = CAR_LENGTH
        self.width = CAR_WIDTH
        self.wheelbase = WHEELBASE
        
        # Trail for visualization
        self.trail = []
        self.max_trail = 150
        
        self.body_color = ACCENT_BLUE
        self.accent_color = ACCENT_CYAN
        self.wing_color = (20, 20, 30)
        
    def update(self, steering_input, speed_input=None):
        """
        Update car position using the Kinematic Bicycle Model.
        
        This model treats the front and rear wheels as single points, 
        providing a realistic simulation of steering geometry.
        """
        self.steering_angle = np.clip(steering_input, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE)
        
        if speed_input is not None:
            self.speed = np.clip(speed_input, MIN_SPEED, MAX_SPEED)
        
        heading_rad = np.radians(self.angle)
        steering_rad = np.radians(self.steering_angle)
        
        # Calculate angular velocity based on wheelbases and steering angle
        # Formula: w = v / R, where R = wheelbase / tan(steering)
        if abs(self.steering_angle) > 0.1:
            turn_radius = self.wheelbase / np.tan(steering_rad)
            angular_velocity = self.speed / turn_radius
        else:
            angular_velocity = 0
        
        # Update state variables
        self.x += self.speed * np.cos(heading_rad)
        self.y += self.speed * np.sin(heading_rad)
        self.angle += np.degrees(angular_velocity)
        
        # Keep angle within [-180, 180] degrees
        while self.angle > 180:
            self.angle -= 360
        while self.angle < -180:
            self.angle += 360
        
        # Update position trail for visual effect
        self.trail.append((self.x, self.y, self.speed))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
    
    def get_front_position(self):
        """Get front axle position"""
        heading_rad = np.radians(self.angle)
        front_x = self.x + (self.length / 2) * np.cos(heading_rad)
        front_y = self.y + (self.length / 2) * np.sin(heading_rad)
        return front_x, front_y
    
    def render(self, screen):
        """Draw car and trail"""
        # Draw trail
        if len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                alpha = i / len(self.trail)
                thickness = max(1, int(3 * alpha))
                
                p1 = (int(self.trail[i-1][0]), int(self.trail[i-1][1]))
                p2 = (int(self.trail[i][0]), int(self.trail[i][1]))
                
                color = (
                    int(ACCENT_CYAN[0] * alpha),
                    int(ACCENT_CYAN[1] * alpha),
                    int(ACCENT_CYAN[2] * alpha)
                )
                pygame.draw.line(screen, color, p1, p2, thickness)
        
        # Glow effect
        glow_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.body_color, 40), (50, 50), 40)
        pygame.draw.circle(glow_surface, (*self.body_color, 25), (50, 50), 50)
        screen.blit(glow_surface, (int(self.x) - 50, int(self.y) - 50))
        
        # Rotation math
        heading_rad = np.radians(self.angle)
        cos_a = np.cos(heading_rad)
        sin_a = np.sin(heading_rad)
        
        def rotate_point(px, py):
            rx = px * cos_a - py * sin_a + self.x
            ry = px * sin_a + py * cos_a + self.y
            return (int(rx), int(ry))
        
        L = self.length
        W = self.width
        
        # Rear wing
        wing_w = W * 1.3
        wing_points = [
            rotate_point(-L/2 - 3, -wing_w/2),
            rotate_point(-L/2 - 3, wing_w/2),
            rotate_point(-L/2 + 2, wing_w/2 - 2),
            rotate_point(-L/2 + 2, -wing_w/2 + 2),
        ]
        pygame.draw.polygon(screen, self.wing_color, wing_points)
        pygame.draw.polygon(screen, ACCENT_RED, wing_points, 2)
        
        # Main body
        body_points = [
            rotate_point(L/2 + 5, 0),
            rotate_point(L/2 - 5, W/2 - 4),
            rotate_point(L/4, W/2 - 2),
            rotate_point(0, W/2),
            rotate_point(-L/4, W/2 + 2),
            rotate_point(-L/2, W/2 - 2),
            rotate_point(-L/2, -W/2 + 2),
            rotate_point(-L/4, -W/2 - 2),
            rotate_point(0, -W/2),
            rotate_point(L/4, -W/2 + 2),
            rotate_point(L/2 - 5, -W/2 + 4),
        ]
        
        # Shadow
        shadow_offset = 3
        shadow_points = [(p[0] + shadow_offset, p[1] + shadow_offset) for p in body_points]
        pygame.draw.polygon(screen, (10, 10, 15), shadow_points)
        
        pygame.draw.polygon(screen, self.body_color, body_points)
        pygame.draw.polygon(screen, self.accent_color, body_points, 2)
        
        # Cockpit
        cockpit_points = [
            rotate_point(L/6, W/4),
            rotate_point(-L/6, W/4),
            rotate_point(-L/6, -W/4),
            rotate_point(L/6, -W/4),
        ]
        pygame.draw.polygon(screen, (15, 15, 20), cockpit_points)
        pygame.draw.polygon(screen, (40, 40, 50), cockpit_points, 1)
        
        # Front wing
        fw_w = W * 1.4
        front_wing_l = [
            rotate_point(L/2, -fw_w/2),
            rotate_point(L/2 + 4, -fw_w/2 - 3),
            rotate_point(L/2 + 4, -W/2 + 2),
            rotate_point(L/2, -W/2 + 4),
        ]
        front_wing_r = [
            rotate_point(L/2, fw_w/2),
            rotate_point(L/2 + 4, fw_w/2 + 3),
            rotate_point(L/2 + 4, W/2 - 2),
            rotate_point(L/2, W/2 - 4),
        ]
        pygame.draw.polygon(screen, self.wing_color, front_wing_l)
        pygame.draw.polygon(screen, self.wing_color, front_wing_r)
        pygame.draw.polygon(screen, ACCENT_RED, front_wing_l, 1)
        pygame.draw.polygon(screen, ACCENT_RED, front_wing_r, 1)
        
        # Wheels
        wheel_w = 5
        wheel_h = 10
        
        wheel_positions = [
            (L/3, W/2 + 3),
            (L/3, -W/2 - 3),
            (-L/3, W/2 + 3),
            (-L/3, -W/2 - 3),
        ]
        
        for wx, wy in wheel_positions:
            wheel_points = [
                rotate_point(wx - wheel_h/2, wy - wheel_w/2),
                rotate_point(wx + wheel_h/2, wy - wheel_w/2),
                rotate_point(wx + wheel_h/2, wy + wheel_w/2),
                rotate_point(wx - wheel_h/2, wy + wheel_w/2),
            ]
            pygame.draw.polygon(screen, (30, 30, 35), wheel_points)
            pygame.draw.polygon(screen, (60, 60, 70), wheel_points, 1)
        
        # Center stripe
        stripe_points = [
            rotate_point(L/2 - 5, 2),
            rotate_point(L/2 - 5, -2),
            rotate_point(-L/3, -2),
            rotate_point(-L/3, 2),
        ]
        pygame.draw.polygon(screen, self.accent_color, stripe_points)
        
        # Number badge
        number_pos = rotate_point(-L/6, 0)
        pygame.draw.circle(screen, WHITE, number_pos, 6)
        
        # Steering indicator
        front_x, front_y = self.get_front_position()
        steer_rad = np.radians(self.angle + self.steering_angle)
        line_length = 20
        end_x = front_x + line_length * np.cos(steer_rad)
        end_y = front_y + line_length * np.sin(steer_rad)
        pygame.draw.line(screen, ACCENT_YELLOW, 
                        (int(front_x), int(front_y)), 
                        (int(end_x), int(end_y)), 2)
        pygame.draw.circle(screen, ACCENT_YELLOW, (int(end_x), int(end_y)), 4)
