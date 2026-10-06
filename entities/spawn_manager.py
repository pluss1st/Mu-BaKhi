"""
spawn_manager.py - Quản lý spawn và drop item trên bản đồ
"""
import random
import pygame
from data.monsters import MONSTER_DATA, SPAWN_DATA
from data.maps     import TILE_SIZE
from entities.monster import Monster


class DropItem:
    """Item nằm trên mặt đất chờ nhặt."""
    LIFETIME = 60.0   # tự biến mất sau 60 giây

    def __init__(self, item_key: str, qty: int, x: float, y: float):
        self.item_key = item_key
        self.qty      = qty
        self.x        = x
        self.y        = y
        self.life     = self.LIFETIME
        self._blink   = 0.0

    def update(self, dt: float) -> bool:
        self.life   -= dt
        self._blink += dt
        return self.life > 0

    def draw(self, screen: pygame.Surface, camera, font, items_data: dict):
        sx, sy = camera.tile_to_screen(self.x, self.y)
        sx, sy = int(sx) + TILE_SIZE // 4, int(sy) + TILE_SIZE // 4

        item = items_data.get(self.item_key, {})
        color = item.get("color", (200, 200, 200))

        # Nhấp nháy khi gần hết thời gian
        if self.life < 10 and int(self._blink * 4) % 2 == 0:
            return

        size = TILE_SIZE // 2
        pygame.draw.rect(screen, (30, 30, 30),
                         (sx - 1, sy - 1, size + 2, size + 2))
        pygame.draw.rect(screen, color, (sx, sy, size, size))

        char = item.get("char", "?")
        t = font.render(char, True, (255, 255, 255))
        screen.blit(t, (sx + size // 2 - t.get_width() // 2,
                        sy + size // 2 - t.get_height() // 2))


class SpawnManager:
    """
    Quản lý toàn bộ quái vật và drop item trên 1 bản đồ.
    """

    def __init__(self, map_key: str):
        self.map_key   = map_key
        self.monsters: list[Monster] = []
        self.drops:    list[DropItem] = []
        self._init_spawns()

    def _init_spawns(self):
        spawn_rules = SPAWN_DATA.get(self.map_key, [])
        for rule in spawn_rules:
            mkey  = rule["monster"]
            count = rule["count"]
            area  = rule["area"]   # (x1, y1, x2, y2)
            mdata = MONSTER_DATA.get(mkey)
            if not mdata:
                continue
            x1, y1, x2, y2 = area
            for _ in range(count):
                x = random.uniform(x1, x2)
                y = random.uniform(y1, y2)
                self.monsters.append(Monster(mkey, mdata, x, y, area))

    # ── Update tất cả quái và drops ───────────────────────────────────────
    def update(self, dt: float, player, tilemap):
        for m in self.monsters:
            was_alive = m.alive
            m.update(dt, player, tilemap)
            # Nếu vừa chết → generate drops
            if was_alive and not m.alive:
                for drop in m.generate_drops():
                    self.drops.append(
                        DropItem(drop["item_key"], drop["qty"],
                                 drop["x"], drop["y"]))

        # Update drops
        self.drops = [d for d in self.drops if d.update(dt)]

    # ── Nhặt item ─────────────────────────────────────────────────────────
    def pick_nearby(self, player, items_data: dict) -> list[dict]:
        """Nhặt tất cả drop trong bán kính 1.5 tile quanh player."""
        picked = []
        remaining = []
        for d in self.drops:
            dist_sq = (d.x - player.x)**2 + (d.y - player.y)**2
            if dist_sq <= 1.5**2:
                picked.append({"item_key": d.item_key, "qty": d.qty})
            else:
                remaining.append(d)
        self.drops = remaining
        return picked

    # ── Lấy quái gần nhất ────────────────────────────────────────────────
    def nearest_monster(self, x: float, y: float,
                        max_dist: float = 99) -> Monster | None:
        best, best_d = None, max_dist
        for m in self.monsters:
            if not m.alive:
                continue
            d = ((m.x - x)**2 + (m.y - y)**2) ** 0.5
            if d < best_d:
                best_d = d
                best   = m
        return best

    def monster_at(self, tx: float, ty: float,
                   radius: float = 1.0) -> Monster | None:
        for m in self.monsters:
            if not m.alive:
                continue
            if abs(m.x - tx) <= radius and abs(m.y - ty) <= radius:
                return m
        return None

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, camera, font, items_data: dict):
        for d in self.drops:
            d.draw(screen, camera, font, items_data)
        for m in self.monsters:
            m.draw(screen, camera, font)
