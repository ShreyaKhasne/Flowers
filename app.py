import pygame
import cv2
import numpy as np
import time
import sys
import os

from hand_tracker import HandTracker
from flower_engine import FlowerEngine, THEMES
from sound_effects import ChimeSynthesizer

WIDTH, HEIGHT = 1280, 720
FPS = 60

# Theme mapping for finger count gestures
THEME_KEYS = ["sakura", "cyberpunk", "golden", "lotus", "cosmic"]

class HandFlowerApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("✨ Move Hand -> Flowers Follow Your Hand ✨")
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.tracker = HandTracker()
        self.engine = FlowerEngine(WIDTH, HEIGHT)
        self.synth = ChimeSynthesizer()

        self.use_camera = True
        self.camera_available = self.tracker.init_camera(0)
        if not self.camera_available:
            self.use_camera = False

        self.dark_canvas_mode = False
        self.show_hand_skeleton = True
        self.is_paused = False

        # Gesture Theme Switcher State
        self.last_gesture_count = 0
        self.gesture_hold_start = 0
        self.theme_toast_msg = ""
        self.theme_toast_time = 0

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_hud = pygame.font.SysFont("Segoe UI", 15)
        self.font_toast = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 13)

        self.last_time = time.time()

    def run(self):
        running = True
        print("==========================================================")
        print("✨ HAND MOVEMENT FLOWER MAGIC STARTED ✨")
        print(" Controls:")
        print(" [1 - 5] / Hold 1-5 Fingers : Switch Theme (Sakura, Cyber, Sunset, Lotus, Cosmic)")
        print(" [C]                        : Toggle Camera Overlay vs. Dark Midnight Canvas")
        print(" [H]                        : Toggle Glowing Hand Skeleton Overlay")
        print(" [R]                        : Clear Canvas")
        print(" [F]                        : Flower Fireworks Explosion")
        print(" [SPACE]                    : Pause Physics")
        print(" [S]                        : Save Screenshot")
        print(" [ESC/Q]                    : Quit")
        print("==========================================================")

        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(0.05, dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        self.engine.spawn_bloom(mx, my, size=50)
                        self.synth.play_chime()

            if pygame.mouse.get_focused():
                mx, my = pygame.mouse.get_pos()
                m_pressed = pygame.mouse.get_pressed()
                if m_pressed[0] or not self.camera_available:
                    self.engine.spawn_petals_at(mx, my, count=2)

            if not self.is_paused:
                frame, hand_data_list = self.tracker.process_frame(self.screen.get_width(), self.screen.get_height())

                if hand_data_list:
                    self.engine.update_hand_trails(hand_data_list, dt)
                    
                    for hand in hand_data_list:
                        if hand["is_pinching"]:
                            self.synth.play_chime()

                    # Process Gesture Theme Switcher (Holding up 1 to 5 fingers!)
                    self.process_gesture_theme_switcher(hand_data_list)

                self.engine.update(dt)

            # Render Background
            if not self.dark_canvas_mode and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (self.screen.get_width(), self.screen.get_height()))
                py_surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                self.screen.blit(py_surf, (0, 0))

                tint = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                tint.fill((10, 10, 20, 120))
                self.screen.blit(tint, (0, 0))
            else:
                self.engine.draw_bg(self.screen)

            # Render Floral Engine
            self.engine.draw(self.screen)

            # Render Hand Skeleton
            if self.show_hand_skeleton and hand_data_list:
                self.draw_hand_skeleton(hand_data_list)

            # Render HUD & Toast Banner
            self.draw_hud(hand_data_list)

            pygame.display.flip()

        self.cleanup()

    def process_gesture_theme_switcher(self, hand_data_list):
        """Switches theme when holding up 1-5 fingers for 0.7 seconds."""
        if not hand_data_list:
            return

        hand = hand_data_list[0]
        # Ignore pinch gesture
        if hand["is_pinching"]:
            return

        f_count = hand["finger_count"]
        now = time.time()

        if 1 <= f_count <= 5:
            if f_count == self.last_gesture_count:
                if (now - self.gesture_hold_start) > 0.7:
                    target_theme = THEME_KEYS[f_count - 1]
                    if target_theme != self.engine.theme_key:
                        self.change_theme(target_theme, source=f"Gesture ({f_count} Finger{'s' if f_count>1 else ''})")
                        self.gesture_hold_start = now
            else:
                self.last_gesture_count = f_count
                self.gesture_hold_start = now
        else:
            self.last_gesture_count = 0

    def change_theme(self, theme_key, source="Keyboard"):
        self.engine.set_theme(theme_key)
        self.synth.play_chime()
        self.theme_toast_msg = f"✨ Theme Switched via {source}: {self.engine.theme['name']}"
        self.theme_toast_time = time.time()

    def handle_keydown(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            return False
        elif event.key == pygame.K_1:
            self.change_theme("sakura", "Keyboard [1]")
        elif event.key == pygame.K_2:
            self.change_theme("cyberpunk", "Keyboard [2]")
        elif event.key == pygame.K_3:
            self.change_theme("golden", "Keyboard [3]")
        elif event.key == pygame.K_4:
            self.change_theme("lotus", "Keyboard [4]")
        elif event.key == pygame.K_5:
            self.change_theme("cosmic", "Keyboard [5]")
        elif event.key == pygame.K_c:
            self.dark_canvas_mode = not self.dark_canvas_mode
        elif event.key == pygame.K_h:
            self.show_hand_skeleton = not self.show_hand_skeleton
        elif event.key == pygame.K_r:
            self.engine.particles.clear()
            self.engine.blooms.clear()
            self.engine.vines.clear()
        elif event.key == pygame.K_f:
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
        theme = self.engine.theme
        glow_color = theme["stem"] + (180,)

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        for hand in hand_data_list:
            pts = hand["landmarks"]
            for p1_idx, p2_idx in connections:
                if p1_idx < len(pts) and p2_idx < len(pts):
                    p1 = (pts[p1_idx][0], pts[p1_idx][1])
                    p2 = (pts[p2_idx][0], pts[p2_idx][1])
                    pygame.draw.line(overlay, glow_color, p1, p2, 3)

            for tip in hand["fingertips"]:
                pygame.draw.circle(overlay, (255, 255, 255, 120), tip, 8)
                pygame.draw.circle(overlay, theme["stem"] + (255,), tip, 4)

            if hand["is_pinching"]:
                px, py = hand["pinch_pos"]
                pygame.draw.circle(overlay, (255, 255, 0, 200), (px, py), 16, 2)

        self.screen.blit(overlay, (0, 0))

    def draw_hud(self, hand_data_list):
        w = self.screen.get_width()
        
        # Glass Top Bar
        bar_surf = pygame.Surface((w, 54), pygame.SRCALPHA)
        bar_surf.fill((15, 15, 25, 180))
        pygame.draw.line(bar_surf, (255, 255, 255, 40), (0, 53), (w, 53), 1)
        self.screen.blit(bar_surf, (0, 0))

        # Title
        t_title = self.font_title.render("✨ Move Hand -> Flowers Follow", True, (255, 255, 255))
        self.screen.blit(t_title, (18, 12))

        # Active Theme
        theme_name = self.engine.theme["name"]
        t_theme = self.font_hud.render(f"Theme: {theme_name}", True, (255, 220, 140))
        self.screen.blit(t_theme, (360, 16))

        # Hand & Finger Gesture Info
        if hand_data_list:
            fc = hand_data_list[0]["finger_count"]
            hand_text = f"Hand Active | Fingers: {fc}"
        else:
            hand_text = "Wave hand or move mouse!"
        t_hand = self.font_hud.render(hand_text, True, (140, 240, 180) if hand_data_list else (200, 200, 200))
        self.screen.blit(t_hand, (600, 16))

        # Stats
        fps = int(self.clock.get_fps())
        particles = len(self.engine.particles) + len(self.engine.blooms)
        t_stats = self.font_hud.render(f"FPS: {fps}  |  Flowers: {particles}", True, (180, 220, 255))
        self.screen.blit(t_stats, (w - 260, 16))

        # Toast Notification for Theme Switch
        now = time.time()
        if (now - self.theme_toast_time) < 2.5:
            toast_surf = pygame.Surface((520, 40), pygame.SRCALPHA)
            toast_surf.fill((30, 20, 50, 220))
            pygame.draw.rect(toast_surf, (255, 200, 100), (0, 0, 520, 40), 2, border_radius=8)
            t_msg = self.font_toast.render(self.theme_toast_msg, True, (255, 255, 255))
            toast_surf.blit(t_msg, (260 - t_msg.get_width() // 2, 8))
            self.screen.blit(toast_surf, (w // 2 - 260, 70))

        # Bottom Key Helper Legend
        legend_surf = pygame.Surface((w, 28), pygame.SRCALPHA)
        legend_surf.fill((10, 10, 15, 150))
        legend_text = "[1-5] Keys or Hold 1-5 Fingers: Switch Theme  |  [C] Camera/Dark  |  [F] Explosion  |  [Pinch] Bloom"
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
