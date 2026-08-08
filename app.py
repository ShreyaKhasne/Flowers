import pygame
import cv2
import numpy as np
import time
import sys
import os

from hand_tracker import HandTracker
from flower_engine import FlowerEngine, THEMES
from sound_effects import ChimeSynthesizer

# Constants
WIDTH, HEIGHT = 1280, 720
FPS = 60

class HandFlowerApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("✨ Move Hand -> Flowers Follow Your Hand ✨")
        
        # Enable vsync and double buffer
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        # Engine Components
        self.tracker = HandTracker()
        self.engine = FlowerEngine(WIDTH, HEIGHT)
        self.synth = ChimeSynthesizer()

        # Try initializing webcam
        self.use_camera = True
        self.camera_available = self.tracker.init_camera(0)
        if not self.camera_available:
            self.use_camera = False

        # Display Options
        self.dark_canvas_mode = False  # False = Camera Overlay, True = Midnight Dark Canvas
        self.show_hand_skeleton = True
        self.is_paused = False

        # Fonts for HUD
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_hud = pygame.font.SysFont("Segoe UI", 15)
        self.font_small = pygame.font.SysFont("Segoe UI", 13)

        # Performance monitoring
        self.last_time = time.time()

    def run(self):
        running = True
        print("==========================================================")
        print("✨ HAND MOVEMENT FLOWER MAGIC STARTED ✨")
        print(" Controls:")
        print(" [1 - 5] : Switch Theme (Sakura, Cyber, Sunset, Lotus, Cosmic)")
        print(" [C]     : Toggle Camera Overlay vs. Dark Midnight Canvas")
        print(" [H]     : Toggle Glowing Hand Skeleton Overlay")
        print(" [M]     : Toggle Mouse Control Fallback")
        print(" [R]     : Clear Canvas")
        print(" [F]     : Flower Fireworks Explosion")
        print(" [SPACE] : Pause Physics")
        print(" [S]     : Save Screenshot")
        print(" [ESC/Q] : Quit")
        print("==========================================================")

        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(0.05, dt)  # Cap delta time to prevent physics explosions

            # Handle SDL Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click spawn flower bloom
                        mx, my = event.pos
                        self.engine.spawn_bloom(mx, my, size=50)
                        self.synth.play_chime()

            # Handle Mouse Movement (when moving mouse or as fallback)
            if pygame.mouse.get_focused():
                mx, my = pygame.mouse.get_pos()
                m_pressed = pygame.mouse.get_pressed()
                if m_pressed[0] or not self.camera_available:
                    self.engine.spawn_petals_at(mx, my, count=2)

            if not self.is_paused:
                # 1. Process Webcam Frame & Track Hands
                frame, hand_data_list = self.tracker.process_frame(self.screen.get_width(), self.screen.get_height())

                # 2. Update Flower Engine with Hand Data
                if hand_data_list:
                    self.engine.update_hand_trails(hand_data_list, dt)
                    
                    # Play chime audio on pinch gesture
                    for hand in hand_data_list:
                        if hand["is_pinching"]:
                            self.synth.play_chime()

                # Update Particles & Blooms
                self.engine.update(dt)

            # 3. Render Background / Frame
            if not self.dark_canvas_mode and frame is not None:
                # Render Camera Frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize frame to current window size
                frame_resized = cv2.resize(frame_rgb, (self.screen.get_width(), self.screen.get_height()))
                py_surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                self.screen.blit(py_surf, (0, 0))

                # Dark tint surface over video for better visual contrast
                tint = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                tint.fill((10, 10, 20, 120))
                self.screen.blit(tint, (0, 0))
            else:
                # Render Dark Gradient Canvas
                self.engine.draw_bg(self.screen)

            # 4. Render Floral System
            self.engine.draw(self.screen)

            # 5. Render Hand Skeleton (if enabled and hands detected)
            if self.show_hand_skeleton and hand_data_list:
                self.draw_hand_skeleton(hand_data_list)

            # 6. Render HUD Overlay
            self.draw_hud(hand_data_list)

            pygame.display.flip()

        self.cleanup()

    def handle_keydown(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return False
        elif event.key == pygame.K_1:
            self.engine.set_theme("sakura")
        elif event.key == pygame.K_2:
            self.engine.set_theme("cyberpunk")
        elif event.key == pygame.K_3:
            self.engine.set_theme("golden")
        elif event.key == pygame.K_4:
            self.engine.set_theme("lotus")
        elif event.key == pygame.K_5:
            self.engine.set_theme("cosmic")
        elif event.key == pygame.K_c:
            self.dark_canvas_mode = not self.dark_canvas_mode
        elif event.key == pygame.K_h:
            self.show_hand_skeleton = not self.show_hand_skeleton
        elif event.key == pygame.K_r:
            self.engine.particles.clear()
            self.engine.blooms.clear()
            self.engine.vines.clear()
        elif event.key == pygame.K_f:
            # Trigger flower fireworks
            w, h = self.screen.get_width(), self.screen.get_height()
            for _ in range(7):
                rx, ry = np.random.randint(100, w - 100), np.random.randint(100, h - 100)
                self.engine.spawn_bloom(rx, ry, size=np.random.randint(45, 70))
                self.synth.play_chime()
        elif event.key == pygame.K_SPACE:
            self.is_paused = not self.is_paused
        elif event.key == pygame.K_s:
            self.save_screenshot()
        return True

    def draw_hand_skeleton(self, hand_data_list):
        """Draws glowing neon hand joints and bone lines."""
        theme = self.engine.theme
        glow_color = theme["stem"] + (180,)
        joint_color = (255, 255, 255, 220)

        # MediaPipe Hand Connections (bones)
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)  # Pinky
        ]

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        for hand in hand_data_list:
            pts = hand["landmarks"]
            # Draw bones
            for p1_idx, p2_idx in connections:
                if p1_idx < len(pts) and p2_idx < len(pts):
                    p1 = (pts[p1_idx][0], pts[p1_idx][1])
                    p2 = (pts[p2_idx][0], pts[p2_idx][1])
                    pygame.draw.line(overlay, glow_color, p1, p2, 3)

            # Draw glowing fingertip aura
            for tip in hand["fingertips"]:
                pygame.draw.circle(overlay, (255, 255, 255, 120), tip, 8)
                pygame.draw.circle(overlay, theme["stem"] + (255,), tip, 4)

            # Highlight pinch position
            if hand["is_pinching"]:
                px, py = hand["pinch_pos"]
                pygame.draw.circle(overlay, (255, 255, 0, 200), (px, py), 16, 2)

        self.screen.blit(overlay, (0, 0))

    def draw_hud(self, hand_data_list):
        """Draws sleek glassmorphic HUD panel."""
        w = self.screen.get_width()
        
        # Translucent glass top bar
        bar_surf = pygame.Surface((w, 54), pygame.SRCALPHA)
        bar_surf.fill((15, 15, 25, 180))
        pygame.draw.line(bar_surf, (255, 255, 255, 40), (0, 53), (w, 53), 1)
        self.screen.blit(bar_surf, (0, 0))

        # Title
        t_title = self.font_title.render("✨ Move Hand -> Flowers Follow", True, (255, 255, 255))
        self.screen.blit(t_title, (18, 12))

        # Theme Name
        theme_name = self.engine.theme["name"]
        t_theme = self.font_hud.render(f"Theme: {theme_name}", True, (255, 220, 140))
        self.screen.blit(t_theme, (360, 16))

        # Status Badges
        num_hands = len(hand_data_list) if hand_data_list else 0
        hand_text = f"Hands: {num_hands} active" if num_hands > 0 else "Hands: Wave hand or move mouse!"
        t_hand = self.font_hud.render(hand_text, True, (140, 240, 180) if num_hands > 0 else (200, 200, 200))
        self.screen.blit(t_hand, (600, 16))

        # Stats (FPS + Particles)
        fps = int(self.clock.get_fps())
        particles = len(self.engine.particles) + len(self.engine.blooms)
        t_stats = self.font_hud.render(f"FPS: {fps}  |  Flowers/Petals: {particles}", True, (180, 220, 255))
        self.screen.blit(t_stats, (w - 280, 16))

        # Bottom Key Helper Legend
        legend_surf = pygame.Surface((w, 28), pygame.SRCALPHA)
        legend_surf.fill((10, 10, 15, 150))
        legend_text = "[1-5] Themes  |  [C] Camera/Dark  |  [H] Skeleton  |  [F] Flower Explosion  |  [R] Reset  |  [Pinch] Bloom"
        t_leg = self.font_small.render(legend_text, True, (200, 200, 220))
        legend_surf.blit(t_leg, (w // 2 - t_leg.get_width() // 2, 6))
        self.screen.blit(legend_surf, (0, self.screen.get_height() - 28))

    def save_screenshot(self):
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        filename = f"screenshots/flower_magic_{int(time.time())}.png"
        pygame.image.save(self.screen, filename)
        print(f"[Screenshot] Saved screenshot to {filename}")

    def cleanup(self):
        self.tracker.release()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = HandFlowerApp()
    app.run()
