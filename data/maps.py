"""
maps.py - Dữ liệu bản đồ MU Online
Dựa theo Map.h / MapManager.cpp / Gate.cpp
"""

# Kích thước tile
TILE_SIZE = 32

# Tile types
TILE_GRASS = 0
TILE_STONE = 1
TILE_WATER = 2
TILE_WALL  = 3
TILE_ROAD  = 4
TILE_SNOW  = 5
TILE_ICE   = 6
TILE_DARK  = 7

TILE_COLORS = {
    TILE_GRASS: (60,  100, 50),
    TILE_STONE: (120, 120, 120),
    TILE_WATER: (40,  80,  160),
    TILE_WALL:  (80,  60,  40),
    TILE_ROAD:  (150, 130, 100),
    TILE_SNOW:  (220, 230, 240),
    TILE_ICE:   (180, 210, 240),
    TILE_DARK:  (40,  40,  50),
}

TILE_WALKABLE = {
    TILE_GRASS: True,
    TILE_STONE: True,
    TILE_WATER: False,
    TILE_WALL:  False,
    TILE_ROAD:  True,
    TILE_SNOW:  True,
    TILE_ICE:   True,
    TILE_DARK:  True,
}


# ── Hàm build map phải định nghĩa TRƯỚC khi dùng ─────────────────────────────

def _build_lorencia_map():
    W, H = 44, 44
    grid = [[TILE_GRASS] * W for _ in range(H)]
    for x in range(W):
        grid[0][x]   = TILE_WALL
        grid[H-1][x] = TILE_WALL
    for y in range(H):
        grid[y][0]   = TILE_WALL
        grid[y][W-1] = TILE_WALL
    # Đường chính
    for x in range(1, W-1):
        grid[21][x] = TILE_ROAD
        grid[22][x] = TILE_ROAD
    for y in range(1, H-1):
        grid[y][21] = TILE_ROAD
        grid[y][22] = TILE_ROAD
    # Vài vùng đá
    for x in range(5, 12):
        for y in range(5, 10):
            if (x + y) % 3 == 0:
                grid[y][x] = TILE_STONE
    # Nước ở góc
    for x in range(30, 36):
        for y in range(30, 36):
            grid[y][x] = TILE_WATER
    return grid


def _build_dungeon_map():
    W, H = 44, 44
    grid = [[TILE_DARK] * W for _ in range(H)]
    for x in range(W):
        grid[0][x]   = TILE_WALL
        grid[H-1][x] = TILE_WALL
    for y in range(H):
        grid[y][0]   = TILE_WALL
        grid[y][W-1] = TILE_WALL
    # Hành lang chữ thập
    for x in range(1, W-1):
        grid[22][x] = TILE_STONE
        grid[23][x] = TILE_STONE
    for y in range(1, H-1):
        grid[y][22] = TILE_STONE
        grid[y][23] = TILE_STONE
    # Phòng ở các góc
    for rx, ry in [(5, 5), (30, 5), (5, 30), (30, 30)]:
        for x in range(rx, rx + 8):
            for y in range(ry, ry + 8):
                if 0 <= x < W and 0 <= y < H:
                    grid[y][x] = TILE_STONE
    return grid


def _build_devias_map():
    W, H = 44, 44
    grid = [[TILE_SNOW] * W for _ in range(H)]
    for x in range(W):
        grid[0][x]   = TILE_WALL
        grid[H-1][x] = TILE_WALL
    for y in range(H):
        grid[y][0]   = TILE_WALL
        grid[y][W-1] = TILE_WALL
    # Đường tuyết
    for x in range(1, W-1):
        grid[21][x] = TILE_ROAD
        grid[22][x] = TILE_ROAD
    for y in range(1, H-1):
        grid[y][21] = TILE_ROAD
        grid[y][22] = TILE_ROAD
    # Vùng băng
    for x in range(28, 38):
        for y in range(28, 38):
            grid[y][x] = TILE_ICE
    return grid


# ── MAP_DATA khai báo SAU khi hàm đã định nghĩa ───────────────────────────────
MAP_DATA = {
    "lorencia": {
        "name":      "Lorencia",
        "width":     44,
        "height":    44,
        "bg_color":  (50, 80, 40),
        "music":     "lorencia",
        "safe_zone": (17, 17, 28, 28),
        "gates": [
            {"to_map": "dungeon", "at": (40, 20), "to_pos": (3, 20),  "label": "→ Dungeon"},
            {"to_map": "devias",  "at": (20, 2),  "to_pos": (20, 40), "label": "→ Devias"},
        ],
        "npcs": [
            {"id": "shop_warrior", "pos": (20, 21), "name": "Johan",  "char": "J", "color": (200, 200, 100)},
            {"id": "shop_wizard",  "pos": (22, 21), "name": "Anya",   "char": "A", "color": (180, 100, 220)},
            {"id": "shop_elf",     "pos": (24, 21), "name": "Lahap",  "char": "L", "color": (100, 200, 100)},
            {"id": "warehouse",    "pos": (21, 23), "name": "Titus",  "char": "W", "color": (200, 180, 100)},
        ],
        "layout": _build_lorencia_map(),
    },
    "dungeon": {
        "name":      "Dungeon",
        "width":     44,
        "height":    44,
        "bg_color":  (30, 30, 40),
        "music":     "dungeon",
        "safe_zone": (0, 0, 0, 0),
        "gates": [
            {"to_map": "lorencia", "at": (2, 20), "to_pos": (39, 20), "label": "→ Lorencia"},
        ],
        "npcs": [],
        "layout": _build_dungeon_map(),
    },
    "devias": {
        "name":      "Devias",
        "width":     44,
        "height":    44,
        "bg_color":  (180, 200, 220),
        "music":     "devias",
        "safe_zone": (17, 17, 28, 28),
        "gates": [
            {"to_map": "lorencia", "at": (20, 42), "to_pos": (20, 3), "label": "→ Lorencia"},
        ],
        "npcs": [
            {"id": "shop_warrior", "pos": (21, 21), "name": "Silvia", "char": "S", "color": (200, 200, 240)},
        ],
        "layout": _build_devias_map(),
    },
}
