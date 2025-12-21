"""
Vision-Based Autonomous Car Simulation
The car navigates using ONLY what its camera sees (OpenCV lane detection)
Pure Pursuit controller with first-person POV camera view
"""

import pygame
import cv2
import numpy as np
import sys
from config import *
from track import Track
from car import Car
from controllers import VisionPurePursuit, SpeedController


class Slider:
    """Interactive slider widget"""
    
    def __init__(self, x, y, width, min_val, max_val, initial, label, color=ACCENT_CYAN):
        self.x = x
        self.y = y
        self.width = width
        self.height = 24
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.color = color
        self.dragging = False
        self.knob_radius = 10
        
    def get_knob_x(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.x + int(ratio * self.width)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if (self.x <= mx <= self.x + self.width and 
                self.y - 5 <= my <= self.y + self.height + 5):
                self.dragging = True
                self._update_value(mx)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
    
    def _update_value(self, mx):
        mx = max(self.x, min(mx, self.x + self.width))
        ratio = (mx - self.x) / self.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
    
    def render(self, screen, font):
        # Label and value
        label_surface = font.render(self.label, True, (120, 125, 135))
        screen.blit(label_surface, (self.x, self.y - 18))
        
        value_str = f"{self.value:.1f}" if isinstance(self.value, float) else f"{int(self.value)}"
        value_surface = font.render(value_str, True, self.color)
        screen.blit(value_surface, (self.x + self.width - value_surface.get_width(), self.y - 18))
        
        # Track
        track_y = self.y + self.height // 2 - 3
        pygame.draw.rect(screen, (40, 45, 55), (self.x, track_y, self.width, 6), border_radius=3)
        
        # Filled portion
        knob_x = self.get_knob_x()
        if knob_x > self.x:
            pygame.draw.rect(screen, self.color, (self.x, track_y, knob_x - self.x, 6), border_radius=3)
        
        # Knob
        knob_y = self.y + self.height // 2
        pygame.draw.circle(screen, self.color, (knob_x, knob_y), self.knob_radius)
        pygame.draw.circle(screen, WHITE, (knob_x, knob_y), self.knob_radius, 2)


class ModernUI:
    """Modern UI overlay"""
    
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        
        self.font_large = pygame.font.Font(None, 42)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Sliders positioned for right panel
        self.speed_slider = Slider(WINDOW_WIDTH - 200, 250, 160, 1.0, 50.0, 5.0, "SPEED", ACCENT_GREEN)
        self.lookahead_slider = Slider(WINDOW_WIDTH - 200, 320, 160, 20, 150, 60, "LOOK-AHEAD", ACCENT_YELLOW)
        
    def draw_panel(self, x, y, width, height, title=None):
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 15, 25, 230), (0, 0, width, height), border_radius=12)
        pygame.draw.rect(panel, (60, 65, 80), (0, 0, width, height), 2, border_radius=12)
        pygame.draw.line(panel, ACCENT_BLUE, (15, 3), (width - 15, 3), 2)
        self.screen.blit(panel, (x, y))
        
        if title:
            title_surface = self.font_medium.render(title, True, (150, 155, 165))
            self.screen.blit(title_surface, (x + 15, y + 12))
    
    def draw_stat(self, x, y, label, value, value_color=ACCENT_CYAN):
        label_surface = self.font_small.render(label, True, (120, 125, 135))
        value_surface = self.font_medium.render(str(value), True, value_color)
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x, y + 18))
    
    def draw_steering_indicator(self, x, y, angle, max_angle):
        width, height = 140, 30
        pygame.draw.rect(self.screen, (40, 45, 55), (x, y, width, height), border_radius=6)
        
        center_x = x + width // 2
        pygame.draw.line(self.screen, (80, 85, 95), (center_x, y + 5), (center_x, y + height - 5), 2)
        
        normalized = np.clip(angle / max_angle, -1, 1)
        indicator_x = center_x + int(normalized * (width // 2 - 10))
        
        color = ACCENT_RED if abs(normalized) > 0.7 else ACCENT_YELLOW if abs(normalized) > 0.3 else ACCENT_GREEN
        pygame.draw.circle(self.screen, color, (indicator_x, y + height // 2), 8)
        pygame.draw.circle(self.screen, WHITE, (indicator_x, y + height // 2), 8, 2)
    
    def draw_camera_view(self, x, y, cv_frame):
        """Draw the camera POV in a panel"""
        if cv_frame is None:
            return
        
        # Convert BGR to RGB
        cv_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        
        # Scale down for display (smaller box requested)
        scale = 0.7
        org_h, org_w = cv_frame.shape[:2]
        new_w = int(org_w * scale)
        new_h = int(org_h * scale)
        
        # Resize frame
        resized_frame = cv2.resize(cv_frame, (new_w, new_h))
        
        # Panel
        panel_w, panel_h = new_w + 20, new_h + 45
        self.draw_panel(x, y, panel_w, panel_h, "DRIVER VIEW")
        
        # Convert to pygame surface
        pygame_frame = pygame.surfarray.make_surface(np.transpose(resized_frame, (1, 0, 2)))
        self.screen.blit(pygame_frame, (x + 10, y + 35))
        
        # Border with glow effect
        pygame.draw.rect(self.screen, ACCENT_CYAN, (x + 10, y + 35, new_w, new_h), 2)
        pygame.draw.rect(self.screen, (*ACCENT_CYAN, 50), (x + 8, y + 33, new_w + 4, new_h + 4), 1)


class Simulation:
    """Vision-based autonomous car simulation"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Vision-Based Autonomous Car - Pure Pursuit")
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        self.ui = ModernUI(self.screen)
        
        # Track (just for rendering - controller doesn't use it!)
        self.track = Track()
        start_x, start_y, start_angle = self.track.get_start_position()
        self.car = Car(start_x, start_y, start_angle)
        
        # Vision-based Pure Pursuit controller
        self.controller = VisionPurePursuit()
        self.speed_controller = SpeedController()
        
        # State
        self.running = True
        self.paused = False
        self.lap_count = 0
        self.lap_ready = False
        self.last_start_dist = 0
        
        # Track surface for vision processing
        self.track_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            self.ui.speed_slider.handle_event(event)
            self.ui.lookahead_slider.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
        
        # Apply slider values
        self.car.speed = self.ui.speed_slider.value
        self.controller.look_ahead_distance = self.ui.lookahead_slider.value
    
    def reset(self):
        start_x, start_y, start_angle = self.track.get_start_position()
        self.car = Car(start_x, start_y, start_angle)
        self.lap_count = 0
        self.lap_ready = False
        self.last_start_dist = 0
    
    def update(self):
        if self.paused:
            return
        
        # Render track only (for vision processing)
        self.track_surface.fill(GRASS_GREEN)
        self.track.render(self.track_surface)
        
        # Get steering from VISION-BASED controller
        steering = self.controller.calculate_steering(self.car, self.track_surface)
        
        # Get speed (reduces in turns)
        speed = self.speed_controller.calculate_speed(steering, self.car.speed)
        
        # Update car
        self.car.update(steering, speed)
        
        # Lap detection
        start_x, start_y, _ = self.track.get_start_position()
        dist_to_start = np.sqrt((self.car.x - start_x)**2 + (self.car.y - start_y)**2)
        
        # Robust lap counting: must travel far (lap_ready) then return
        if dist_to_start > 400:
            self.lap_ready = True
            
        if self.lap_ready and dist_to_start < 60:
            self.lap_count += 1
            self.lap_ready = False
            
        self.last_start_dist = dist_to_start
    
    def render(self):
        # Draw track
        self.track.render(self.screen)
        
        # Draw vision visualization (yellow lines)
        self._draw_vision_viz()
        
        # Draw car
        self.car.render(self.screen)
        
        # Draw UI
        self._draw_ui()
        
        pygame.display.flip()
        
    def _draw_vision_viz(self):
        """Draw what the vision system detects"""
        controller = self.controller
        
        # Draw lookahead line/point
        if hasattr(controller, 'viz_lookahead_point') and controller.viz_lookahead_point:
            lx, ly = controller.viz_lookahead_point
            
            # Yellow line from car to lookahead point
            pygame.draw.line(self.screen, (*ACCENT_YELLOW, 150),
                           (int(self.car.x), int(self.car.y)),
                           (int(lx), int(ly)), 2)
            
            # Look-ahead circle
            pygame.draw.circle(self.screen, ACCENT_YELLOW, (int(lx), int(ly)), 5)
            
            # Visual ring indicating lookahead distance scale
            # We scale this ring based on the slider value to show "extension"
            # Using look_ahead_distance directly for visualization scale
            ring_radius = int(controller.look_ahead_distance * 4) 
            pygame.draw.circle(self.screen, (*ACCENT_YELLOW, 50),
                             (int(self.car.x), int(self.car.y)),
                             ring_radius, 1)
    
    def _draw_ui(self):
        # Driver view camera (Top Left)
        camera_frame = self.controller.get_camera_view()
        self.ui.draw_camera_view(20, 20, camera_frame)
        
        # Controls panel (top right)
        self.ui.draw_panel(WINDOW_WIDTH - 220, 20, 200, 360, "TELEMETRY")
        
        # Lap counter
        self.ui.draw_stat(WINDOW_WIDTH - 200, 55, "LAPS", str(self.lap_count), ACCENT_CYAN)
        
        # Steering display
        self.ui.draw_stat(WINDOW_WIDTH - 200, 100, "STEERING", f"{self.car.steering_angle:.1f}°", ACCENT_YELLOW)
        self.ui.draw_steering_indicator(WINDOW_WIDTH - 200, 140, self.car.steering_angle, MAX_STEERING_ANGLE)
        
        # Lane position indicator
        lane_offset = (self.controller.lane_center - 0.5) * 100
        direction = "LEFT" if lane_offset < -5 else "RIGHT" if lane_offset > 5 else "CENTER"
        color = ACCENT_GREEN if direction == "CENTER" else ACCENT_YELLOW
        self.ui.draw_stat(WINDOW_WIDTH - 200, 185, "LANE", direction, color)
        
        # Sliders
        self.ui.speed_slider.render(self.screen, self.ui.font_small)
        self.ui.lookahead_slider.render(self.screen, self.ui.font_small)
        
        # "VISION-BASED" badge at top
        badge_w, badge_h = 220, 35
        badge_x = WINDOW_WIDTH // 2 - badge_w // 2
        badge_y = 15
        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*ACCENT_GREEN, 200), (0, 0, badge_w, badge_h), border_radius=17)
        pygame.draw.rect(badge, ACCENT_GREEN, (0, 0, badge_w, badge_h), 2, border_radius=17)
        self.screen.blit(badge, (badge_x, badge_y))
        
        badge_text = self.ui.font_medium.render("VISION-BASED", True, WHITE)
        self.screen.blit(badge_text, (badge_x + (badge_w - badge_text.get_width()) // 2, 
                                       badge_y + (badge_h - badge_text.get_height()) // 2))
        
        # Mode badge
        mode_w, mode_h = 180, 30
        mode_x = WINDOW_WIDTH // 2 - mode_w // 2
        mode_y = 55
        mode_badge = pygame.Surface((mode_w, mode_h), pygame.SRCALPHA)
        pygame.draw.rect(mode_badge, (40, 45, 55, 200), (0, 0, mode_w, mode_h), border_radius=15)
        self.screen.blit(mode_badge, (mode_x, mode_y))
        
        mode_text = self.ui.font_small.render("Pure Pursuit Controller", True, (150, 155, 165))
        self.screen.blit(mode_text, (mode_x + (mode_w - mode_text.get_width()) // 2,
                                     mode_y + (mode_h - mode_text.get_height()) // 2))
        
        # Hint bar
        hint_panel = pygame.Surface((350, 35), pygame.SRCALPHA)
        pygame.draw.rect(hint_panel, (15, 15, 25, 200), (0, 0, 350, 35), border_radius=8)
        self.screen.blit(hint_panel, (WINDOW_WIDTH // 2 - 175, WINDOW_HEIGHT - 50))
        
        hint = "[R] Reset    [SPACE] Pause    [ESC] Quit"
        hint_surf = pygame.font.Font(None, 22).render(hint, True, (120, 125, 135))
        self.screen.blit(hint_surf, (WINDOW_WIDTH // 2 - hint_surf.get_width() // 2, WINDOW_HEIGHT - 40))
        
        # Paused overlay
        if self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (0, 0, 0, 100), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(overlay, (0, 0))
            
            pause_text = pygame.font.Font(None, 72).render("PAUSED", True, WHITE)
            self.screen.blit(pause_text, pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))
    
    def run(self):
        print("\n" + "=" * 60)
        print("  VISION-BASED AUTONOMOUS CAR SIMULATION")
        print("  Car navigates using camera POV + OpenCV lane detection")
        print("=" * 60)
        print("\n  [R] Reset  [SPACE] Pause  [ESC] Quit")
        print("=" * 60 + "\n")
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    sim = Simulation()
    sim.run()
