import pygame
import pygame.gfxdraw as gfxdraw
import numpy as np
import math
import random
import time

# Visual Theme Color Palettes
THEMES = {
    "sakura": {
        "name": "Sakura Blossom 🌸",
        "bg_gradient": ((15, 10, 25), (35, 18, 40)),
        "petals": [(255, 183, 197), (255, 214, 224), (255, 143, 171), (255, 255, 255)],
        "flower_center": (255, 220, 100),
        "stem": (100, 180, 110),
        "glow": (255, 150, 180, 80)
    },
    "cyberpunk": {
        "name": "Neon Cyber Flora ✨",
        "bg_gradient": ((5, 5, 18), (15, 5, 30)),
        "petals": [(0, 245, 255), (255, 0, 127), (180, 0, 255), (0, 255, 170)],
        "flower_center": (255, 255, 0),
        "stem": (0, 255, 200),
        "glow": (0, 200, 255, 100)
    },
    "golden": {
        "name": "Golden Sunset 🌻",
        "bg_gradient": ((20, 12, 5), (40, 20, 10)),
        "petals": [(255, 190, 11), (251, 86, 7), (255, 0, 110), (255, 220, 100)],
        "flower_center": (90, 40, 15),
        "stem": (140, 190, 60),
        "glow": (255, 180, 50, 90)
    },
    "lotus": {
        "name": "Mystic Lotus Lagoon 🪷",
        "bg_gradient": ((8, 15, 25), (15, 30, 45)),
        "petals": [(216, 180, 254), (244, 114, 182), (167, 139, 250), (255, 255, 255)],
        "flower_center": (253, 224, 71),
        "stem": (52, 211, 153),
        "glow": (192, 132, 252, 90)
    },
    "cosmic": {
        "name": "Cosmic Sparkle 🌌",
        "bg_gradient": ((5, 5, 12), (12, 8, 25)),
        "petals": [(255, 255, 255), (147, 197, 253), (249, 168, 212), (196, 181, 253)],
        "flower_center": (255, 255, 200),
        "stem": (120, 220, 255),
        "glow": (180, 180, 255, 100)
    }
}

class PetalParticle:
    def __init__(self, x, y, color, scale=1.0, vx=0, vy=0, flower_type="sakura"):
        self.x = x
        self.y = y
        self.color = color
        self.scale = random.uniform(0.6, 1.4) * scale
        self.vx = vx + random.uniform(-1.5, 1.5)
        self.vy = vy + random.uniform(-2.0, -0.5)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4.0, 4.0)
        self.alpha = 255
        self.max_life = random.uniform(2.5, 5.0)
        self.life = self.max_life
        self.flower_type = flower_type
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, dt, wind_x=0.0, wind_y=0.0):
        self.life -= dt
        if self.life <= 0:
            return False

        # Sway oscillation & gravity physics
        self.phase += dt * 3.0
        sway = math.sin(self.phase) * 0.8
        
        self.vx += (sway + wind_x) * dt
        self.vy += (0.4 + wind_y) * dt  # Gentle downward gravity
        
        self.vx *= 0.96  # Drag
        self.vy *= 0.96

        self.x += self.vx
        self.y += self.vy
        self.rot += self.rot_speed

        # Fade out towards end of life
        life_ratio = self.life / self.max_life
        self.alpha = int(255 * min(1.0, life_ratio * 1.5))
        return True

    def draw(self, surface):
        if self.alpha <= 5:
            return

        size = int(12 * self.scale)
        if size < 3:
            return

        # Render rotated petal surface
        petal_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        c = self.color + (self.alpha,)

        # Draw organic petal shape
        pts = [
            (size, size // 4),
            (size + size // 2, size),
            (size, size + size // 2),
            (size - size // 2, size)
        ]
        pygame.draw.polygon(petal_surf, c, pts)
        gfxdraw.aapolygon(petal_surf, pts, c)

        # Rotate and blit
        rotated = pygame.transform.rotate(petal_surf, self.rot)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect, special_flags=pygame.BLEND_ALPHA_SDL2)


class BloomingFlower:
    def __init__(self, x, y, theme_key="sakura", max_size=45):
        self.x = x
        self.y = y
        self.theme_key = theme_key
        self.theme = THEMES.get(theme_key, THEMES["sakura"])
        self.max_size = max_size
        self.size = 0.0
        self.growth_speed = random.uniform(1.8, 2.5)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-0.5, 0.5)
        self.num_petals = random.choice([5, 6, 8, 12])
        self.life = 6.0  # Seconds to live
        self.max_life = 6.0
        self.alpha = 255

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False

        # Grow size smoothly
        if self.size < self.max_size:
            self.size += (self.max_size - self.size) * self.growth_speed * dt
            self.size = min(self.max_size, self.size)

        self.rotation += self.rot_speed

        # Fade out near end of life
        if self.life < 1.5:
            self.alpha = int(255 * (self.life / 1.5))

        return True

    def draw(self, surface):
        if self.size < 2 or self.alpha <= 5:
            return

        r_size = int(self.size)
        surf_size = r_size * 3
        flower_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = (surf_size // 2, surf_size // 2)

        petals_colors = self.theme["petals"]
        num_layers = 2

        # Draw layered flower petals
        for layer in range(num_layers, 0, -1):
            layer_scale = (layer / num_layers) * self.size
            petal_color = petals_colors[(layer - 1) % len(petals_colors)] + (self.alpha,)

            for i in range(self.num_petals):
                angle_deg = (360 / self.num_petals) * i + self.rotation * layer
                angle_rad = math.radians(angle_deg)

                # Petal tip coordinates
                px = center[0] + math.cos(angle_rad) * layer_scale
                py = center[1] + math.sin(angle_rad) * layer_scale

                # Control points for curved petal shape
                perp_rad = angle_rad + math.pi / 2
                cw = layer_scale * 0.45
                c1x = center[0] + math.cos(angle_rad) * (layer_scale * 0.5) + math.cos(perp_rad) * cw
                c1y = center[1] + math.sin(angle_rad) * (layer_scale * 0.5) + math.sin(perp_rad) * cw
                c2x = center[0] + math.cos(angle_rad) * (layer_scale * 0.5) - math.cos(perp_rad) * cw
                c2y = center[1] + math.sin(angle_rad) * (layer_scale * 0.5) - math.sin(perp_rad) * cw

                poly_pts = [
                    center,
                    (int(c1x), int(c1y)),
                    (int(px), int(py)),
                    (int(c2x), int(c2y))
                ]
                pygame.draw.polygon(flower_surf, petal_color, poly_pts)
                gfxdraw.aapolygon(flower_surf, poly_pts, petal_color)

        # Flower Center (Stamen core)
        center_color = self.theme["flower_center"] + (self.alpha,)
        center_r = max(2, int(self.size * 0.22))
        pygame.draw.circle(flower_surf, center_color, center, center_r)
        gfxdraw.aacircle(flower_surf, center[0], center[1], center_r, center_color)

        # Blit flower to main surface
        rect = flower_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(flower_surf, rect, special_flags=pygame.BLEND_ALPHA_SDL2)


class VineTrail:
    def __init__(self, max_points=35):
        self.points = []  # (x, y, timestamp)
        self.max_points = max_points

    def add_point(self, x, y):
        now = time.time()
        # Avoid redundant close points
        if self.points:
            last_x, last_y, _ = self.points[-1]
            if math.hypot(x - last_x, y - last_y) < 5:
                return
        self.points.append((x, y, now))
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def draw(self, surface, theme):
        if len(self.points) < 2:
            return

        now = time.time()
        stem_color = theme["stem"]

        # Filter active points (fade older than 1.5 seconds)
        active_pts = [(x, y, (1.5 - (now - t)) / 1.5) for x, y, t in self.points if (now - t) < 1.5]
        if len(active_pts) < 2:
            return

        for i in range(len(active_pts) - 1):
            p1 = active_pts[i]
            p2 = active_pts[i + 1]
            alpha = int(255 * max(0.0, min(1.0, (p1[2] + p2[2]) / 2)))
            thick = max(1, int(5 * (p1[2])))

            color_with_alpha = stem_color + (alpha,)
            
            # Draw line segment
            line_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(line_surf, color_with_alpha, (p1[0], p1[1]), (p2[0], p2[1]), thick)
            surface.blit(line_surf, (0, 0))


class FlowerEngine:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.theme_key = "sakura"
        self.theme = THEMES[self.theme_key]
        
        self.particles = []
        self.blooms = []
        self.vines = {}  # hand_idx -> VineTrail
        
        # Wind force field from fast movements
        self.wind_x = 0.0
        self.wind_y = 0.0

    def set_theme(self, theme_key):
        if theme_key in THEMES:
            self.theme_key = theme_key
            self.theme = THEMES[theme_key]
            print(f"[FlowerEngine] Switched theme to: {self.theme['name']}")

    def spawn_petals_at(self, x, y, count=3, vx=0, vy=0):
        colors = self.theme["petals"]
        for _ in range(count):
            c = random.choice(colors)
            p = PetalParticle(x, y, c, vx=vx*0.1, vy=vy*0.1, flower_type=self.theme_key)
            self.particles.append(p)

    def spawn_bloom(self, x, y, size=50):
        # Create a new blooming flower
        b = BloomingFlower(x, y, theme_key=self.theme_key, max_size=size)
        self.blooms.append(b)
        
        # Burst surrounding petals on bloom
        self.spawn_petals_at(x, y, count=15)

    def update_hand_trails(self, hand_data_list, dt):
        """Processes hand landmarks to spawn petals, vines, and trigger blooms."""
        # Decaying wind force
        self.wind_x *= 0.90
        self.wind_y *= 0.90

        if not hand_data_list:
            return

        for hand in hand_data_list:
            hand_idx = hand["hand_idx"]
            index_tip = hand["index_tip"]
            vx, vy = hand["velocity"]
            speed = hand["speed"]

            # Add wind force if hand is moving fast
            if speed > 300:
                self.wind_x += vx * 0.001
                self.wind_y += vy * 0.001

            # 1. Vine Trail
            if hand_idx not in self.vines:
                self.vines[hand_idx] = VineTrail()
            self.vines[hand_idx].add_point(index_tip[0], index_tip[1])

            # 2. Continuous Petal Emitter at Fingertips
            for tip in hand["fingertips"]:
                if random.random() < 0.6:  # Emit frequency
                    self.spawn_petals_at(tip[0], tip[1], count=1, vx=vx, vy=vy)

            # 3. Pinch Gesture -> Spawn Big Blooming Flower
            if hand["is_pinching"]:
                px, py = hand["pinch_pos"]
                # Only spawn if no recent bloom right at position
                too_close = any(math.hypot(b.x - px, b.y - py) < 30 for b in self.blooms)
                if not too_close:
                    self.spawn_bloom(px, py, size=random.randint(40, 65))

            # 4. Open Palm Sweep -> Burst Petal Shower
            if hand["is_open_palm"] and random.random() < 0.25:
                palm_x, palm_y = hand["palm_center"]
                self.spawn_petals_at(palm_x, palm_y, count=6, vx=vx, vy=vy)

    def update(self, dt):
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt, self.wind_x, self.wind_y)]
        
        # Limit max particles for 60 FPS performance
        if len(self.particles) > 400:
            self.particles = self.particles[-400:]

        # Update blooms
        self.blooms = [b for b in self.blooms if b.update(dt)]

    def draw_bg(self, surface):
        """Draws rich ambient background gradient for Dark Canvas mode."""
        c1, c2 = self.theme["bg_gradient"]
        h = surface.get_height()
        w = surface.get_width()
        
        # Fast 2-step gradient fill
        bg = pygame.Surface((w, h))
        for y in range(0, h, 4):
            r = y / h
            r_col = int(c1[0] * (1 - r) + c2[0] * r)
            g_col = int(c1[1] * (1 - r) + c2[1] * r)
            b_col = int(c1[2] * (1 - r) + c2[2] * r)
            pygame.draw.rect(bg, (r_col, g_col, b_col), (0, y, w, 4))
        surface.blit(bg, (0, 0))

    def draw(self, surface):
        # 1. Draw Vine Trails
        for vine in self.vines.values():
            vine.draw(surface, self.theme)

        # 2. Draw Blooming Flowers
        for b in self.blooms:
            b.draw(surface)

        # 3. Draw Petal Particles
        for p in self.particles:
            p.draw(surface)
