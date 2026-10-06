"""
event_bus.py - Hệ thống sự kiện nội bộ (pub/sub) giữa các module
"""
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """
    Lightweight event bus. Các module subscribe theo tên event,
    game loop dispatch event khi cần.
    """

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable):
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable):
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event: str, **kwargs):
        for cb in list(self._listeners[event]):
            cb(**kwargs)


# Singleton dùng toàn project
bus = EventBus()

# ── Danh sách event constants ─────────────────────────────────────────────────
EVT_PLAYER_DIED      = "player_died"
EVT_PLAYER_LEVEL_UP  = "player_level_up"
EVT_MONSTER_DIED     = "monster_died"
EVT_ITEM_DROPPED     = "item_dropped"
EVT_ITEM_PICKED      = "item_picked"
EVT_MAP_CHANGE       = "map_change"
EVT_DAMAGE_DEALT     = "damage_dealt"
EVT_CHAT_MESSAGE     = "chat_message"
EVT_SKILL_USED       = "skill_used"
