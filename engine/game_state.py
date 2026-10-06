"""
game_state.py - Quản lý trạng thái game (menu, playing, paused, game_over)
"""
from enum import Enum, auto


class State(Enum):
    MAIN_MENU   = auto()
    CHAR_SELECT = auto()
    CHAR_CREATE = auto()
    PLAYING     = auto()
    PAUSED      = auto()
    INVENTORY   = auto()
    SHOP        = auto()
    GAME_OVER   = auto()
    LEVEL_UP    = auto()


class GameStateManager:
    """Stack-based state machine."""

    def __init__(self):
        self._stack: list[State] = [State.MAIN_MENU]

    @property
    def current(self) -> State:
        return self._stack[-1]

    def push(self, state: State):
        self._stack.append(state)

    def pop(self) -> State:
        if len(self._stack) > 1:
            return self._stack.pop()
        return self._stack[-1]

    def change(self, state: State):
        self._stack[-1] = state

    def is_playing(self) -> bool:
        return self.current == State.PLAYING

    def is_overlay(self) -> bool:
        """Các state overlay lên PLAYING (inventory, shop, pause)."""
        return self.current in (State.INVENTORY, State.SHOP,
                                State.PAUSED, State.LEVEL_UP)
