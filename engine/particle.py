"""
particle.py - Hiệu ứng particle đơn giản (damage numbers, hit flash, drops)
"""
import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, vx, vy, life, size=4, text=None, font=None):
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.vx    = float(vx)
        self.vy    = float(vy)
        self.life  = float(life)
        self.max_life = float(life)
        self.size  = size
        self.text  = text
        self.font  = font

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt: float):
        self.x    += self.vx * dt
        self.y    += self.vy * dt
        self.vy   += 30 * dt   # gravity nhẹ
        self.life -= dt

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return
        alpha = max(0, int(255 * (self.life / self.max_life)))
        sx, sy = camera.world_to_screen(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if self.text and self.font:
            color_a = (*self.color[:3], alpha)
            surf = self.font.render(self.text, True, self.color)
            surf.set_alpha(alpha)
            screen.blit(surf, (sx - surf.get_width() // 2,
                               sy - surf.get_height() // 2))
        else:
            size = max(1, int(self.size * (self.life / self.max_life)))
            pygame.draw.circle(screen, self.color, (sx, sy), size)


class ParticleSystem:
    def __init__(self):
        self._particles: list[Particle] = []
        self._dmg_font = None

    def _get_font(self):
        if self._dmg_font is None:
            self._dmg_font = pygame.font.SysFont("Arial", 14, bold=True)
        return self._dmg_font

    def spawn_damage(self, wx: float, wy: float, damage: int,
                     critical: bool = False):
        """Số damage nổi lên đầu target."""
        color = (255, 50, 50) if not critical else (255, 215, 0)
        size  = 14 if not critical else 18
        font  = pygame.font.SysFont("Arial", size, bold=True)
        vx = random.uniform(-20, 20)
        vy = random.uniform(-60, -40)
        p = Particle(wx, wy - 10, color, vx, vy, 1.2,
                     text=str(damage), font=font)
        self._particles.append(p)

    def spawn_heal(self, wx: float, wy: float, amount: int):
        color = (50, 255, 100)
        font  = pygame.font.SysFont("Arial", 14, bold=True)
        vx = random.uniform(-15, 15)
        vy = random.uniform(-50, -35)
        p = Particle(wx, wy - 10, color, vx, vy, 1.0,
                     text=f"+{amount}", font=font)
        self._particles.append(p)

    def spawn_hit(self, wx: float, wy: float, color=(255, 200, 50), count=6):
        """Tia sáng khi đánh trúng."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self._particles.append(
                Particle(wx, wy, color, vx, vy,
                         random.uniform(0.2, 0.5), size=random.randint(2, 5)))

    def spawn_level_up(self, wx: float, wy: float):
        """Pháo hoa khi lên level."""
        colors = [(255, 215, 0), (255, 255, 100), (200, 255, 200),
                  (255, 150, 50), (150, 200, 255)]
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 150)
            color = random.choice(colors)
            self._particles.append(
                Particle(wx, wy, color,
                         math.cos(angle) * speed,
                         math.sin(angle) * speed - 50,
                         random.uniform(0.8, 1.5),
                         size=random.randint(3, 7)))

    def spawn_exp(self, wx: float, wy: float, exp: int):
        """Hiển thị EXP nhận được."""
        font = pygame.font.SysFont("Arial", 12)
        p = Particle(wx, wy - 20, (180, 180, 255), 0, -30, 1.0,
                     text=f"+{exp} EXP", font=font)
        self._particles.append(p)

    def update(self, dt: float):
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update(dt)

    def draw(self, screen: pygame.Surface, camera):
        for p in self._particles:
            p.draw(screen, camera)
