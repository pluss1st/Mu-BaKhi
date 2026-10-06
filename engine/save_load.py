"""
save_load.py - Lưu/tải game (JSON file)
"""
import json
import os
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "saves")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def list_saves() -> list[dict]:
    ensure_save_dir()
    saves = []
    for fname in os.listdir(SAVE_DIR):
        if fname.endswith(".json"):
            path = os.path.join(SAVE_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saves.append({
                    "file":      fname,
                    "path":      path,
                    "name":      data.get("char_name", "Unknown"),
                    "class":     data.get("char_class", "?"),
                    "level":     data.get("level", 1),
                    "map":       data.get("current_map", "lorencia"),
                    "saved_at":  data.get("saved_at", ""),
                })
            except Exception:
                pass
    return sorted(saves, key=lambda s: s["saved_at"], reverse=True)


def save_game(player, slot_name: str = None) -> str:
    ensure_save_dir()
    if not slot_name:
        slot_name = f"{player.name}_{player.char_class}"
    fname = f"{slot_name}.json"
    path  = os.path.join(SAVE_DIR, fname)

    data = {
        "char_name":   player.name,
        "char_class":  player.char_class,
        "level":       player.level,
        "exp":         player.exp,
        "str":         player.stat_str,
        "agi":         player.stat_agi,
        "vit":         player.stat_vit,
        "ene":         player.stat_ene,
        "stat_points": player.stat_points,
        "hp":          player.hp,
        "mp":          player.mp,
        "zen":         player.zen,
        "current_map": player.current_map,
        "pos_x":       player.x,
        "pos_y":       player.y,
        "inventory":   _serialize_inventory(player.inventory),
        "equipment":   _serialize_equipment(player.equipment),
        "skill_slots": player.skill_slots,
        "kills":       player.kills,
        "deaths":      player.deaths,
        "saved_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_game(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _serialize_inventory(inventory: list) -> list:
    result = []
    for slot in inventory:
        if slot is None:
            result.append(None)
        else:
            result.append({
                "item_key": slot["item_key"],
                "qty":      slot.get("qty", 1),
                "level":    slot.get("level", 0),
                "options":  slot.get("options", []),
            })
    return result


def _serialize_equipment(equipment: dict) -> dict:
    result = {}
    for slot, item in equipment.items():
        if item is None:
            result[slot] = None
        else:
            result[slot] = {
                "item_key": item["item_key"],
                "level":    item.get("level", 0),
                "options":  item.get("options", []),
            }
    return result
