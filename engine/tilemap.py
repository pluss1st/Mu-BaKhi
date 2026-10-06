"""
tilemap.py - Vẽ bản đồ tile và xử lý collision
"""
import pygame
from data.maps import TILE_COLORS, TILE_WALKABLE, TILE_SIZE, TILE_WALL, TILE_WATER
from engine.camera import Camera


class TileMap:
    """
    Quản lý và vẽ tile map cho 1 bản đồ.
    Hỗ trợ tile cache để tối ưu tốc độ render.
    """

    def __init__(self, map_key: str, map_info: dict):
        self.key      = map_key
        self.info     = map_info
        self.name     = map_info["name"]
        self.width    = map_info["width"]
        self.height   = map_info["height"]
        self.layout   = map_info["layout"]
        self.bg_color = map_info["bg_color"]
        self.gates    = map_info.get("gates", [])
        self.npcs     = map_info.get("npcs", [])
        self.safe_zone = map_info.get("safe_zone", (0, 0, 0, 0))
        self._tile_cache: dict[int, pygame.Surface] = {}
        self._build_tile_cache()

    # ── Cache surface cho từng loại tile ─────────────────────────────────
    def _build_tile_cache(self):
        for tile_id, color in TILE_COLORS.items():
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill(color)
            # Vẽ viền nhẹ để phân biệt tile
            darker = tuple(max(0, c - 20) for c in color)
            pygame.draw.rect(surf, darker,
                             (0, 0, TILE_SIZE, TILE_SIZE), 1)
            self._tile_cache[tile_id] = surf

    # ── Render bản đồ ─────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, camera: Camera):
        x0, y0, x1, y1 = camera.get_visible_tiles(self.width, self.height)

        for ty in range(y0, y1):
            for tx in range(x0, x1):
                tile_id = self.layout[ty][tx]
                surf    = self._tile_cache.get(tile_id)
                if surf:
                    sx, sy = camera.tile_to_screen(tx, ty)
                    screen.blit(surf, (int(sx), int(sy)))

        # Vẽ cổng
        for gate in self.gates:
            gx, gy = gate["at"]
            sx, sy = camera.tile_to_screen(gx, gy)
            if -TILE_SIZE < sx < camera.screen_w and -TILE_SIZE < sy < camera.screen_h:
                pygame.draw.rect(screen, (255, 215, 0),
                                 (int(sx)+2, int(sy)+2, TILE_SIZE-4, TILE_SIZE-4))
                pygame.draw.rect(screen, (200, 160, 0),
                                 (int(sx), int(sy), TILE_SIZE, TILE_SIZE), 2)

    # ── Kiểm tra walkable ─────────────────────────────────────────────────
    def is_walkable(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self.width or ty >= self.height:
            return False
        tile_id = self.layout[ty][tx]
        return TILE_WALKABLE.get(tile_id, False)

    def is_walkable_f(self, tx: float, ty: float) -> bool:
        return self.is_walkable(int(tx), int(ty))

    # ── Safe zone ─────────────────────────────────────────────────────────
    def in_safe_zone(self, tx: float, ty: float) -> bool:
        x1, y1, x2, y2 = self.safe_zone
        if x1 == x2 == y1 == y2 == 0:
            return False
        return x1 <= tx <= x2 and y1 <= ty <= y2

    # ── Tìm gate tại vị trí ──────────────────────────────────────────────
    def get_gate_at(self, tx: int, ty: int) -> dict | None:
        for gate in self.gates:
            gx, gy = gate["at"]
            if abs(gx - tx) <= 1 and abs(gy - ty) <= 1:
                return gate
        return None

    # ── Tìm NPC tại vị trí ───────────────────────────────────────────────
    def get_npc_at(self, tx: int, ty: int) -> dict | None:
        for npc in self.npcs:
            nx, ny = npc["pos"]
            if abs(nx - tx) <= 1 and abs(ny - ty) <= 1:
                return npc
        return None
