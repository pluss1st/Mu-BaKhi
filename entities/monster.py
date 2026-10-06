"""
monster.py - Quái vật: AI, combat, drop
Dựa theo Monster.h / MonsterAI.cpp / MonsterManager.cpp
"""
import math
import random
import pygame
from data.maps   import TILE_SIZE
from data.items  import ITEMS
from engine.event_bus import bus, EVT_MONSTER_DIED, EVT_ITEM_DROPPED


class Monster:
    """
    Một instance quái vật trên bản đồ.
    """

    AGGRO_LOSE_DIST = 12.0   # mất aggro khi player đi xa hơn

    def __init__(self, monster_key: str, data: dict,
                 x: float, y: float, spawn_area: tuple):
        self.key        = monster_key
        self.data       = data
        self.name       = data["name"]
        self.x          = float(x)
        self.y          = float(y)
        self.spawn_x    = float(x)
        self.spawn_y    = float(y)
        self.spawn_area = spawn_area  # (x1,y1,x2,y2)

        self.level      = data["level"]
        self.max_hp     = data["hp"]
        self.hp         = float(data["hp"])
        self.atk_min    = data["atk_min"]
        self.atk_max    = data["atk_max"]
        self.defense    = data["defense"]
        self.move_speed = data["move_speed"]
        self.atk_speed  = data["atk_speed"]
        self.aggro_range = data["aggro_range"]
        self.atk_range   = data["atk_range"]
        self.ai_type    = data["ai"]
        self.is_boss    = data.get("boss", False)

        self.color      = data["color"]
        self.char       = data["char"]

        self.alive      = True
        self.target     = None   # player hiện tại đang nhắm
        self.atk_timer  = 0.0
        self.roam_timer = 0.0
        self.roam_target: tuple | None = None
        self.respawn_timer = 0.0
        self.is_respawning = False

        # Hiệu ứng bị đánh
        self.hit_flash = 0.0

    # ── Tính damage ───────────────────────────────────────────────────────
    def roll_damage(self) -> int:
        return random.randint(self.atk_min, self.atk_max)

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.defense // 2)
        self.hp = max(0.0, self.hp - dmg)
        self.hit_flash = 0.15
        if self.hp <= 0:
            self._die()
        return dmg

    def _die(self):
        self.alive      = False
        self.target     = None
        self.is_respawning = True
        # Respawn 30s thường, 5 phút boss
        self.respawn_timer = 300.0 if self.is_boss else 30.0
        bus.emit(EVT_MONSTER_DIED, monster=self)

    # ── Drop items ────────────────────────────────────────────────────────
    def generate_drops(self) -> list[dict]:
        """Trả về list item drop (mỗi item là dict {item_key, qty, x, y})."""
        drops = []
        for drop_rule in self.data.get("drops", []):
            if random.random() < drop_rule["rate"]:
                item_key = drop_rule["item"]
                if item_key == "zen":
                    lo, hi = self.data.get("zen", (1, 10))
                    amount = random.randint(lo, hi)
                    drops.append({"item_key": "zen", "qty": amount,
                                  "x": self.x + random.uniform(-1, 1),
                                  "y": self.y + random.uniform(-1, 1)})
                elif item_key in ITEMS:
                    drops.append({"item_key": item_key, "qty": 1,
                                  "x": self.x + random.uniform(-1.5, 1.5),
                                  "y": self.y + random.uniform(-1.5, 1.5)})
        return drops

    # ── AI update ─────────────────────────────────────────────────────────
    def update(self, dt: float, player, tilemap):
        if not self.alive:
            # Đếm respawn
            if self.is_respawning:
                self.respawn_timer -= dt
                if self.respawn_timer <= 0:
                    self._respawn()
            return

        self.atk_timer  = max(0.0, self.atk_timer - dt)
        self.roam_timer = max(0.0, self.roam_timer - dt)
        self.hit_flash  = max(0.0, self.hit_flash - dt)

        if self.ai_type == "walk_random":
            self._ai_roam(dt, tilemap)
        elif self.ai_type in ("aggressive", "boss"):
            self._ai_aggressive(dt, player, tilemap)

    def _respawn(self):
        x1, y1, x2, y2 = self.spawn_area
        self.x  = float(random.randint(x1, x2))
        self.y  = float(random.randint(y1, y2))
        self.hp = float(self.max_hp)
        self.alive         = True
        self.is_respawning = False
        self.target        = None

    def _dist_to_player(self, player) -> float:
        dx = player.x - self.x
        dy = player.y - self.y
        return math.sqrt(dx * dx + dy * dy)

    def _ai_roam(self, dt: float, tilemap):
        """Đi lang thang trong vùng spawn."""
        if self.roam_target is None or self.roam_timer <= 0:
            self.roam_timer = random.uniform(2.0, 5.0)
            x1, y1, x2, y2 = self.spawn_area
            self.roam_target = (
                random.uniform(x1, x2),
                random.uniform(y1, y2),
            )
        if self.roam_target:
            tx, ty = self.roam_target
            self._move_toward(tx, ty, dt, tilemap, self.move_speed * 0.5)
            if math.dist((self.x, self.y), (tx, ty)) < 0.3:
                self.roam_target = None

    def _ai_aggressive(self, dt: float, player, tilemap):
        """Đuổi player khi trong range, tấn công khi gần đủ."""
        dist = self._dist_to_player(player)

        # Detect player
        if dist <= self.aggro_range and player.alive:
            self.target = player
        elif dist > self.AGGRO_LOSE_DIST:
            self.target = None

        if self.target and self.target.alive:
            if dist <= self.atk_range + 0.5:
                # Trong tầm đánh
                if self.atk_timer <= 0:
                    self._attack_player()
                    self.atk_timer = 1.0 / self.atk_speed
            else:
                # Đuổi theo
                self._move_toward(player.x, player.y, dt, tilemap,
                                  self.move_speed)
        else:
            # Không có target → roam
            self._ai_roam(dt, tilemap)

    def _attack_player(self):
        if self.target and self.target.alive:
            dmg = self.roll_damage()
            self.target.take_damage(dmg)

    def _move_toward(self, tx, ty, dt, tilemap, speed):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.1:
            return
        nx = self.x + (dx / dist) * speed * dt
        ny = self.y + (dy / dist) * speed * dt
        if tilemap.is_walkable_f(nx, ny):
            self.x, self.y = nx, ny
        elif tilemap.is_walkable_f(nx, self.y):
            self.x = nx
        elif tilemap.is_walkable_f(self.x, ny):
            self.y = ny

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, camera, font: pygame.font.Font):
        if not self.alive:
            return
        sx, sy = camera.tile_to_screen(self.x, self.y)
        sx, sy = int(sx), int(sy)

        # Không vẽ nếu ngoài màn hình
        if (sx < -TILE_SIZE or sx > camera.screen_w + TILE_SIZE or
                sy < -TILE_SIZE or sy > camera.screen_h + TILE_SIZE):
            return

        r  = TILE_SIZE // 2 - 2
        cx = sx + TILE_SIZE // 2
        cy = sy + TILE_SIZE // 2

        # Flash khi bị đánh
        color = (255, 255, 255) if self.hit_flash > 0 else self.color
        if self.is_boss:
            # Boss hình vuông to hơn
            pygame.draw.rect(screen, color,
                             (sx + 2, sy + 2, TILE_SIZE - 4, TILE_SIZE - 4))
            pygame.draw.rect(screen, (255, 215, 0),
                             (sx + 2, sy + 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
        else:
            pygame.draw.circle(screen, color, (cx, cy), r)
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), r, 1)

        # Ký tự
        txt = font.render(self.char, True,
                          (0, 0, 0) if self.is_boss else (255, 255, 255))
        screen.blit(txt, (cx - txt.get_width() // 2,
                          cy - txt.get_height() // 2))

        # Thanh HP
        bar_w = TILE_SIZE - 4
        bar_h = 4
        bx    = sx + 2
        by    = sy - 7
        pygame.draw.rect(screen, (60, 0, 0), (bx, by, bar_w, bar_h))
        hp_w = int(bar_w * (self.hp / max(1, self.max_hp)))
        hp_c = (50, 200, 50) if not self.is_boss else (255, 100, 0)
        pygame.draw.rect(screen, hp_c, (bx, by, hp_w, bar_h))

        # Tên boss
        if self.is_boss:
            nm = font.render(self.name, True, (255, 215, 0))
            screen.blit(nm, (cx - nm.get_width() // 2, sy - 18))
