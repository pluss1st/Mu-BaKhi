"""
classes.py - Định nghĩa 5 class nhân vật MU Online
DW (Dark Wizard), DK (Dark Knight), ELF (Fairy Elf), MG (Magic Gladiator), DL (Dark Lord)
"""

CLASS_DATA = {
    "DW": {
        "name": "Dark Wizard",
        "short": "DW",
        "color": (100, 120, 220),
        "description": "Pháp sư mạnh về ma thuật, yếu về thể lực",
        # Stats cơ bản level 1
        "base_str": 18,
        "base_agi": 18,
        "base_vit": 15,
        "base_ene": 30,
        # Tăng mỗi level
        "str_per_level": 1,
        "agi_per_level": 1,
        "vit_per_level": 1,
        "ene_per_level": 3,
        # HP/Mana công thức
        "hp_base": 60,
        "hp_per_vit": 1,
        "mp_base": 60,
        "mp_per_ene": 4,
        # Tốc độ
        "move_speed": 3.2,
        "attack_speed": 1.4,
        # Skills mặc định
        "skills": ["melee", "fire_ball", "ice_ball", "thunder_ball"],
        "weapon_types": ["staff", "sword"],
        "char": "W",  # ký tự đại diện trên bản đồ
    },
    "DK": {
        "name": "Dark Knight",
        "short": "DK",
        "color": (180, 50, 50),
        "description": "Chiến binh mạnh nhất, chuyên cận chiến",
        "base_str": 28,
        "base_agi": 20,
        "base_vit": 25,
        "base_ene": 10,
        "str_per_level": 3,
        "agi_per_level": 2,
        "vit_per_level": 2,
        "ene_per_level": 0,
        "hp_base": 110,
        "hp_per_vit": 2,
        "mp_base": 20,
        "mp_per_ene": 1,
        "move_speed": 3.0,
        "attack_speed": 1.8,
        "skills": ["melee", "slash", "twisting_slash", "death_stab"],
        "weapon_types": ["sword", "axe", "mace", "spear"],
        "char": "K",
    },
    "ELF": {
        "name": "Fairy Elf",
        "short": "ELF",
        "color": (50, 200, 100),
        "description": "Cung thủ nhanh nhẹn, hỗ trợ và tấn công từ xa",
        "base_str": 22,
        "base_agi": 25,
        "base_vit": 20,
        "base_ene": 15,
        "str_per_level": 1,
        "agi_per_level": 3,
        "vit_per_level": 1,
        "ene_per_level": 1,
        "hp_base": 80,
        "hp_per_vit": 1,
        "mp_base": 40,
        "mp_per_ene": 2,
        "move_speed": 3.8,
        "attack_speed": 2.2,
        "skills": ["melee", "triple_shot", "multi_shot", "heal", "defense_up"],
        "weapon_types": ["bow", "crossbow"],
        "char": "E",
    },
    "MG": {
        "name": "Magic Gladiator",
        "short": "MG",
        "color": (200, 150, 50),
        "description": "Kết hợp DK + DW, cân bằng cận chiến và phép thuật",
        "base_str": 26,
        "base_agi": 26,
        "base_vit": 26,
        "base_ene": 16,
        "str_per_level": 2,
        "agi_per_level": 2,
        "vit_per_level": 2,
        "ene_per_level": 2,
        "hp_base": 90,
        "hp_per_vit": 1,
        "mp_base": 40,
        "mp_per_ene": 3,
        "move_speed": 3.5,
        "attack_speed": 2.0,
        "skills": ["melee", "fire_slash", "power_slash", "thunder_ball"],
        "weapon_types": ["sword", "staff", "axe"],
        "char": "M",
    },
    "DL": {
        "name": "Dark Lord",
        "short": "DL",
        "color": (150, 50, 200),
        "description": "Lãnh chúa bóng tối, triệu hồi và lệnh cho quái vật",
        "base_str": 26,
        "base_agi": 20,
        "base_vit": 20,
        "base_ene": 15,
        "str_per_level": 3,
        "agi_per_level": 2,
        "vit_per_level": 2,
        "ene_per_level": 1,
        "hp_base": 100,
        "hp_per_vit": 2,
        "mp_base": 30,
        "mp_per_ene": 2,
        "move_speed": 3.3,
        "attack_speed": 1.6,
        "skills": ["melee", "fire_burst", "summon", "dark_horse_attack"],
        "weapon_types": ["scepter", "sword"],
        "char": "L",
    },
}

# Bảng EXP cần để lên level (dựa theo ExperienceTable.cpp)
EXP_TABLE = {}
for lv in range(1, 401):
    if lv <= 10:
        EXP_TABLE[lv] = lv * lv * lv * 10
    elif lv <= 50:
        EXP_TABLE[lv] = lv * lv * lv * 12
    elif lv <= 100:
        EXP_TABLE[lv] = lv * lv * lv * 15
    elif lv <= 200:
        EXP_TABLE[lv] = lv * lv * lv * 20
    else:
        EXP_TABLE[lv] = lv * lv * lv * 30
