"""
inventory.py - Hệ thống inventory và trang bị
"""
from data.items  import ITEMS, EQUIP_SLOTS


class InventorySystem:
    """
    Helper logic xử lý inventory cho player.
    Inventory là list 60 slot, mỗi slot = None hoặc dict item.
    """

    @staticmethod
    def add_item(player, item_key: str, qty: int = 1) -> bool:
        """
        Thêm item vào inventory.
        Nếu stackable → stack vào slot cũ, nếu không → tìm slot trống.
        Trả về True nếu thành công.
        """
        item_data = ITEMS.get(item_key)
        if not item_data:
            return False

        # Tiền Zen → thêm thẳng vào player.zen
        if item_key == "zen":
            player.zen += qty
            return True

        stackable = item_data.get("stackable", False)
        max_stack = item_data.get("max_stack", 1)

        if stackable:
            # Tìm slot đã có item đó
            for slot in player.inventory:
                if slot and slot["item_key"] == item_key:
                    space = max_stack - slot["qty"]
                    add   = min(space, qty)
                    slot["qty"] += add
                    qty -= add
                    if qty <= 0:
                        return True

        # Tìm slot trống
        for i in range(len(player.inventory)):
            if player.inventory[i] is None:
                player.inventory[i] = {
                    "item_key": item_key,
                    "qty":      min(qty, max_stack),
                    "level":    0,
                    "options":  [],
                }
                return True

        return False  # Inventory đầy

    @staticmethod
    def remove_item(player, slot_idx: int, qty: int = 1) -> bool:
        slot = player.inventory[slot_idx]
        if slot is None:
            return False
        if slot["qty"] > qty:
            slot["qty"] -= qty
            return True
        player.inventory[slot_idx] = None
        return True

    @staticmethod
    def equip_item(player, inv_slot: int) -> tuple[bool, str]:
        """
        Trang bị item từ inventory.
        Trả về (success, message).
        """
        slot = player.inventory[inv_slot]
        if slot is None:
            return False, "Không có item"

        item_key  = slot["item_key"]
        item_data = ITEMS.get(item_key)
        if not item_data:
            return False, "Item không hợp lệ"

        # Kiểm tra class restriction
        allowed_classes = item_data.get("classes", [])
        if allowed_classes and player.char_class not in allowed_classes:
            return False, f"Class {player.char_class} không thể dùng item này"

        # Kiểm tra req_str
        req_str = item_data.get("req_str", 0)
        req_agi = item_data.get("req_agi", 0)
        if player.stat_str < req_str:
            return False, f"Cần STR {req_str} (bạn có {player.stat_str})"
        if player.stat_agi < req_agi:
            return False, f"Cần AGI {req_agi} (bạn có {player.stat_agi})"

        equip_slot = item_data.get("slot")
        if not equip_slot:
            return False, "Item không thể trang bị"

        # Tháo item cũ → trả về inventory
        old = player.equipment.get(equip_slot)
        if old:
            InventorySystem.add_item(player, old["item_key"])

        # Trang bị item mới
        player.equipment[equip_slot] = {
            "item_key": item_key,
            "level":    slot.get("level", 0),
            "options":  slot.get("options", []),
            **{k: v for k, v in item_data.items()},
        }
        player.inventory[inv_slot] = None
        player._recalc_max()
        return True, f"Đã trang bị {item_data['name']}"

    @staticmethod
    def unequip_item(player, equip_slot: str) -> tuple[bool, str]:
        """Tháo trang bị → trả về inventory."""
        item = player.equipment.get(equip_slot)
        if not item:
            return False, "Không có gì trang bị ở slot này"
        ok = InventorySystem.add_item(player, item["item_key"])
        if ok:
            player.equipment[equip_slot] = None
            player._recalc_max()
            return True, "Đã tháo trang bị"
        return False, "Inventory đầy"

    @staticmethod
    def use_item(player, inv_slot: int) -> tuple[bool, str]:
        """Sử dụng item (potion...)."""
        slot = player.inventory[inv_slot]
        if slot is None:
            return False, "Không có item"
        item_data = ITEMS.get(slot["item_key"])
        if not item_data or not item_data.get("usable"):
            return False, "Không thể sử dụng"

        subtype = item_data.get("subtype", "")
        if subtype == "hp":
            heal = item_data.get("heal", 0)
            actual = min(heal, player.max_hp - player.hp)
            player.heal(int(heal))
            InventorySystem.remove_item(player, inv_slot, 1)
            return True, f"Hồi {int(actual)} HP"
        elif subtype == "mp":
            mana = item_data.get("mana", 0)
            player.restore_mp(int(mana))
            InventorySystem.remove_item(player, inv_slot, 1)
            return True, f"Hồi {mana} MP"

        return False, "Không thể sử dụng"

    @staticmethod
    def count_item(player, item_key: str) -> int:
        total = 0
        for slot in player.inventory:
            if slot and slot["item_key"] == item_key:
                total += slot["qty"]
        return total
