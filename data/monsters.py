"""
monsters.py - Dữ liệu quái vật MU Online
Dựa theo Monster.h / MonsterManager.cpp
"""

MONSTER_DATA = {
    # ── Lorencia ──────────────────────────────────────────────────────────
    "budge_dragon": {
        "id": 0, "name": "Budge Dragon",
        "char": "b", "color": (180, 80, 80),
        "level": 1, "hp": 30, "mp": 0,
        "atk_min": 3, "atk_max": 6,
        "defense": 2, "move_speed": 1.2, "atk_speed": 1.0,
        "exp": 8, "zen": (2, 8),
        "map": "lorencia", "ai": "walk_random",
        "aggro_range": 3, "atk_range": 1,
        "drops": [
            {"item": "small_healing_potion", "rate": 0.15},
            {"item": "zen",                  "rate": 0.80},
            {"item": "short_sword",          "rate": 0.03},
        ],
    },
    "hound": {
        "id": 1, "name": "Hound",
        "char": "h", "color": (160, 120, 60),
        "level": 3, "hp": 50, "mp": 0,
        "atk_min": 5, "atk_max": 10,
        "defense": 3, "move_speed": 1.5, "atk_speed": 1.2,
        "exp": 15, "zen": (3, 12),
        "map": "lorencia", "ai": "aggressive",
        "aggro_range": 4, "atk_range": 1,
        "drops": [
            {"item": "small_healing_potion", "rate": 0.20},
            {"item": "zen",                  "rate": 0.75},
            {"item": "leather_gloves",       "rate": 0.04},
        ],
    },
    "lich": {
        "id": 2, "name": "Lich",
        "char": "L", "color": (100, 100, 200),
        "level": 8, "hp": 100, "mp": 50,
        "atk_min": 12, "atk_max": 22,
        "defense": 8, "move_speed": 1.0, "atk_speed": 0.9,
        "exp": 45, "zen": (10, 30),
        "map": "lorencia", "ai": "aggressive",
        "aggro_range": 5, "atk_range": 1,
        "drops": [
            {"item": "healing_potion",  "rate": 0.20},
            {"item": "zen",             "rate": 0.70},
            {"item": "skull_shield",    "rate": 0.05},
            {"item": "jewel_of_bless", "rate": 0.01},
        ],
    },
    # ── Dungeon ───────────────────────────────────────────────────────────
    "skeleton_warrior": {
        "id": 10, "name": "Skeleton Warrior",
        "char": "S", "color": (210, 210, 180),
        "level": 15, "hp": 230, "mp": 0,
        "atk_min": 22, "atk_max": 38,
        "defense": 15, "move_speed": 1.3, "atk_speed": 1.4,
        "exp": 100, "zen": (20, 60),
        "map": "dungeon", "ai": "aggressive",
        "aggro_range": 5, "atk_range": 1,
        "drops": [
            {"item": "healing_potion",   "rate": 0.25},
            {"item": "zen",              "rate": 0.65},
            {"item": "ring_of_ice",      "rate": 0.03},
            {"item": "jewel_of_bless",  "rate": 0.02},
        ],
    },
    "elite_skeleton": {
        "id": 11, "name": "Elite Skeleton",
        "char": "E", "color": (230, 200, 50),
        "level": 22, "hp": 420, "mp": 0,
        "atk_min": 40, "atk_max": 60,
        "defense": 25, "move_speed": 1.4, "atk_speed": 1.5,
        "exp": 220, "zen": (40, 100),
        "map": "dungeon", "ai": "aggressive",
        "aggro_range": 6, "atk_range": 1,
        "drops": [
            {"item": "large_healing_potion", "rate": 0.20},
            {"item": "zen",                  "rate": 0.60},
            {"item": "plate_helm",           "rate": 0.04},
            {"item": "jewel_of_soul",        "rate": 0.02},
        ],
    },
    # ── Devias ────────────────────────────────────────────────────────────
    "ice_monster": {
        "id": 20, "name": "Ice Monster",
        "char": "I", "color": (150, 200, 255),
        "level": 30, "hp": 600, "mp": 0,
        "atk_min": 55, "atk_max": 80,
        "defense": 35, "move_speed": 1.1, "atk_speed": 1.2,
        "exp": 380, "zen": (60, 150),
        "map": "devias", "ai": "aggressive",
        "aggro_range": 5, "atk_range": 1,
        "drops": [
            {"item": "large_healing_potion", "rate": 0.25},
            {"item": "zen",                  "rate": 0.55},
            {"item": "ice_blade",            "rate": 0.04},
            {"item": "jewel_of_soul",        "rate": 0.02},
            {"item": "jewel_of_bless",       "rate": 0.02},
        ],
    },
    "yeti": {
        "id": 21, "name": "Yeti",
        "char": "Y", "color": (200, 240, 255),
        "level": 38, "hp": 900, "mp": 0,
        "atk_min": 75, "atk_max": 110,
        "defense": 50, "move_speed": 1.3, "atk_speed": 1.0,
        "exp": 600, "zen": (80, 200),
        "map": "devias", "ai": "aggressive",
        "aggro_range": 6, "atk_range": 1,
        "drops": [
            {"item": "large_healing_potion", "rate": 0.25},
            {"item": "zen",                  "rate": 0.50},
            {"item": "pad_armor",            "rate": 0.05},
            {"item": "jewel_of_life",        "rate": 0.02},
        ],
    },
    # ── Boss ──────────────────────────────────────────────────────────────
    "golden_budge_dragon": {
        "id": 100, "name": "Golden Budge Dragon",
        "char": "G", "color": (255, 215, 0),
        "level": 50, "hp": 5000, "mp": 500,
        "atk_min": 120, "atk_max": 180,
        "defense": 80, "move_speed": 1.5, "atk_speed": 1.8,
        "exp": 5000, "zen": (500, 1500),
        "map": "lorencia", "ai": "boss",
        "aggro_range": 8, "atk_range": 2,
        "drops": [
            {"item": "jewel_of_bless",  "rate": 0.50},
            {"item": "jewel_of_soul",   "rate": 0.40},
            {"item": "jewel_of_life",   "rate": 0.30},
            {"item": "chaos_weapon",    "rate": 0.10},
        ],
        "boss": True,
    },
    "balrog": {
        "id": 101, "name": "Balrog",
        "char": "B", "color": (220, 50, 50),
        "level": 80, "hp": 15000, "mp": 1000,
        "atk_min": 200, "atk_max": 300,
        "defense": 150, "move_speed": 1.2, "atk_speed": 1.5,
        "exp": 20000, "zen": (1000, 5000),
        "map": "dungeon", "ai": "boss",
        "aggro_range": 10, "atk_range": 2,
        "drops": [
            {"item": "jewel_of_bless",      "rate": 0.80},
            {"item": "jewel_of_soul",       "rate": 0.70},
            {"item": "jewel_of_life",       "rate": 0.50},
            {"item": "chaos_weapon",        "rate": 0.20},
            {"item": "excellent_armor",     "rate": 0.15},
        ],
        "boss": True,
    },
}

# Spawn points theo map
SPAWN_DATA = {
    "lorencia": [
        {"monster": "budge_dragon", "count": 8, "area": (5, 5, 20, 20)},
        {"monster": "hound",        "count": 6, "area": (15, 15, 30, 30)},
        {"monster": "lich",         "count": 4, "area": (25, 10, 38, 25)},
        {"monster": "golden_budge_dragon", "count": 1, "area": (18, 18, 22, 22)},
    ],
    "dungeon": [
        {"monster": "skeleton_warrior", "count": 10, "area": (5, 5, 35, 35)},
        {"monster": "elite_skeleton",   "count": 6,  "area": (15, 15, 35, 35)},
        {"monster": "balrog",           "count": 1,  "area": (18, 18, 22, 22)},
    ],
    "devias": [
        {"monster": "ice_monster", "count": 8, "area": (5, 5, 35, 35)},
        {"monster": "yeti",        "count": 5, "area": (20, 20, 38, 38)},
    ],
}
