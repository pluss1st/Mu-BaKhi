"""
camera.py - Camera theo dõi nhân vật, cuộn bản đồ
"""


class Camera:
    """
    Camera 2D: convert world coords → screen coords.
    Luôn giữ target (player) ở giữa màn hình.
    """

    def __init__(self, screen_w: int, screen_h: int, tile_size: int):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.tile_size = tile_size
        self.offset_x  = 0.0
        self.offset_y  = 0.0
        self._map_pw   = 0   # map width  in pixels
        self._map_ph   = 0   # map height in pixels

    def set_map_size(self, map_w_tiles: int, map_h_tiles: int):
        self._map_pw = map_w_tiles * self.tile_size
        self._map_ph = map_h_tiles * self.tile_size

    def update(self, target_x: float, target_y: float):
        """Cập nhật offset để target nằm giữa màn hình."""
        # target_x/y là tile coords → chuyển sang pixel
        tx_px = target_x * self.tile_size + self.tile_size // 2
        ty_px = target_y * self.tile_size + self.tile_size // 2

        self.offset_x = tx_px - self.screen_w // 2
        self.offset_y = ty_px - self.screen_h // 2

        # Clamp để không vượt ra ngoài bản đồ
        self.offset_x = max(0, min(self.offset_x, self._map_pw  - self.screen_w))
        self.offset_y = max(0, min(self.offset_y, self._map_ph - self.screen_h))

    def world_to_screen(self, wx: float, wy: float):
        """World pixel → screen pixel."""
        return (wx - self.offset_x, wy - self.offset_y)

    def tile_to_screen(self, tx: float, ty: float):
        """Tile coords → screen pixel (góc trên trái của tile)."""
        return (tx * self.tile_size - self.offset_x,
                ty * self.tile_size - self.offset_y)

    def screen_to_tile(self, sx: float, sy: float):
        """Screen pixel → tile coords (float)."""
        return ((sx + self.offset_x) / self.tile_size,
                (sy + self.offset_y) / self.tile_size)

    def get_visible_tiles(self, map_w: int, map_h: int):
        """Trả về range tile x/y cần vẽ (tối ưu, không vẽ tile ngoài màn hình)."""
        x0 = max(0, int(self.offset_x // self.tile_size) - 1)
        y0 = max(0, int(self.offset_y // self.tile_size) - 1)
        x1 = min(map_w, x0 + self.screen_w  // self.tile_size + 3)
        y1 = min(map_h, y0 + self.screen_h // self.tile_size + 3)
        return x0, y0, x1, y1
