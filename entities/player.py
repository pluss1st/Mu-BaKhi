"""
player.py - Nhân vật người chơi
Dựa theo User.h / User.cpp / DefaultClassInfo.cpp
"""
import math
import pygame
from data.classes import CLASS_DATA, EXP_TABLE
from data.skills  import SKILLS
from data.items   import EQUIP_SLOTS
from engine.event_bus import bus, EVT_PLAYER_LEVEL_UP, EVT_PLAYER_DIED


class Player:
    """
    Đại diện cho nhân vật người chơi.
    Xử lý: di chuyển, stats, level, exp, trang bị, skills.
    """

    MAX_LEVEL   = 400
    INV_SIZE    = 60   # số slot inventory

    def __init__(self, name: str, char_class: str,
                 x: float = 22.0, y: float = 22.0,
                 current_map: str = "lorencia"):
        self.name        = name
        self.char_class  = char_class
        self.current_map = current_map
        self.x = float(x)
        self.y = float(y)

        # Stats gốc từ class data
        cls = CLASS_DATA[char_class]
        self.stat_str  = cls["base_str"]
        self.stat_agi  = cls["base_agi"]
        self.stat_vit  = cls["base_vit"]
        self.stat_ene  = cls["base_ene"]
        self.stat_points = 0   # điểm chưa phân bổ

        # Level / EXP
        self.level = 1
        self.exp   = 0
        self.kills = 0
        self.deaths = 0

        # Tiền
        self.zen = 0

        # Trạng thái
        self.alive      = True
        self.invincible = False
        self.inv_timer  = 0.0

        # Di chuyển
        self.vx = 0.0
        self.vy = 0.0
        self._move_target = None   # (tx, ty) khi click chuột

        # Combat
        self.atk_timer  = 0.0
        self.skill_timer = {}
        self.target      = None
        self.buffs       = []

        # Trang bị — phải khởi tạo TRƯỚC _recalc_max()
        self.equipment = {s: None for s in EQUIP_SLOTS}

        # Inventory: list 60 slot
        self.inventory = [None] * self.INV_SIZE

        # HP / MP — tính SAU khi equipment đã có
        self._recalc_max()
        self.hp = float(self.max_hp)
        self.mp = float(self.max_mp)

        # Skill slots (key → skill_id)
        cls_skills = cls["skills"]
        self.skill_slots = {
            "1": cls_skills[0] if len(cls_skills) > 0 else None,
            "2": cls_skills[1] if len(cls_skills) > 1 else None,
            "3": cls_skills[2] if len(cls_skills) > 2 else None,
            "4": cls_skills[3] if len(cls_skills) > 3 else None,
            "5": cls_skills[4] if len(cls_skills) > 4 else None,
        }
        self.active_skill: str = "melee"

        # Màu / ký tự đại diện
        self.color = cls["color"]
        self.char  = cls["char"]

    # ── Tính lại max HP/MP từ stats ──────────────────────────────────────
    def _recalc_max(self):
        cls = CLASS_DATA[self.char_class]
        self.max_hp = (cls["hp_base"]
                       + self.stat_vit * cls["hp_per_vit"]
                       + self.level * 5)
        self.max_mp = (cls["mp_base"]
                       + self.stat_ene * cls["mp_per_ene"]
                       + self.level * 2)
        # Cộng bonus từ trang bị
        for slot, item in self.equipment.items():
            if item:
                self.max_hp += item.get("bonus_hp", 0)
                self.max_mp += item.get("bonus_mp", 0)

    # ── Tính attack damage ────────────────────────────────────────────────
    @property
    def attack_min(self) -> int:
        cls  = CLASS_DATA[self.char_class]
        base = int(self.stat_str * 0.5 + self.stat_agi * 0.2)
        wpn  = self.equipment.get("weapon")
        if wpn:
            base += wpn.get("atk_min", 0) + wpn.get("level", 0) * 3
        return max(1, base)

    @property
    def attack_max(self) -> int:
        cls  = CLASS_DATA[self.char_class]
        base = int(self.stat_str * 0.7 + self.stat_agi * 0.3)
        wpn  = self.equipment.get("weapon")
        if wpn:
            base += wpn.get("atk_max", 0) + wpn.get("level", 0) * 5
        return max(self.attack_min + 1, base)

    @property
    def defense(self) -> int:
        base = int(self.stat_agi * 0.3 + self.stat_vit * 0.1)
        for slot, item in self.equipment.items():
            if item:
                base += item.get("defense", 0) + item.get("level", 0) * 2
        # Buff defense
        for b in self.buffs:
            base += b.get("defense_up", 0)
        return max(0, base)

    @property
    def attack_speed(self) -> float:
        cls  = CLASS_DATA[self.char_class]
        base = cls["attack_speed"]
        spd  = self.stat_agi * 0.005
        wpn  = self.equipment.get("weapon")
        if wpn:
            spd += wpn.get("atk_speed", 0) * 0.05
        return max(0.3, base - spd)  # giây/đòn

    @property
    def move_speed(self) -> float:
        cls  = CLASS_DATA[self.char_class]
        base = cls["move_speed"]
        # Slow buff check
        for b in self.buffs:
            if b.get("slow"):
                base *= 0.5
        return base

    # ── Level / EXP ──────────────────────────────────────────────────────
    def gain_exp(self, amount: int):
        if self.level >= self.MAX_LEVEL:
            return
        self.exp += amount
        while (self.level < self.MAX_LEVEL
               and self.exp >= EXP_TABLE.get(self.level, 999999999)):
            self.exp -= EXP_TABLE[self.level]
            self._level_up()

    def _level_up(self):
        self.level += 1
        cls = CLASS_DATA[self.char_class]
        self.stat_str += cls["str_per_level"]
        self.stat_agi += cls["agi_per_level"]
        self.stat_vit += cls["vit_per_level"]
        self.stat_ene += cls["ene_per_level"]
        self.stat_points += 5   # 5 điểm tự do mỗi level
        self._recalc_max()
        self.hp = float(self.max_hp)
        self.mp = float(self.max_mp)
        bus.emit(EVT_PLAYER_LEVEL_UP,
                 player=self, level=self.level)

    def exp_percent(self) -> float:
        needed = EXP_TABLE.get(self.level, 1)
        return min(1.0, self.exp / needed) if needed > 0 else 1.0

    # ── HP / MP ───────────────────────────────────────────────────────────
    def take_damage(self, raw_damage: int) -> int:
        if not self.alive or self.invincible:
            return 0
        dmg = max(1, raw_damage - self.defense // 2)
        self.hp = max(0.0, self.hp - dmg)
        if self.hp <= 0:
            self._die()
        return dmg

    def heal(self, amount: int):
        self.hp = min(float(self.max_hp), self.hp + amount)

    def restore_mp(self, amount: int):
        self.mp = min(float(self.max_mp), self.mp + amount)

    def regen_tick(self, dt: float):
        """Tự hồi HP/MP theo thời gian."""
        if self.alive:
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.005 * dt)
            self.mp = min(self.max_mp, self.mp + self.max_mp * 0.008 * dt)

    def _die(self):
        self.alive  = False
        self.deaths += 1
        bus.emit(EVT_PLAYER_DIED, player=self)

    def respawn(self, x: float, y: float, current_map: str):
        self.alive       = True
        self.current_map = current_map
        self.x = x
        self.y = y
        self.hp = float(self.max_hp * 0.5)
        self.mp = float(self.max_mp * 0.5)
        self.invincible  = True
        self.inv_timer   = 3.0   # 3 giây bất tử sau hồi sinh
        # Mất 10% zen khi chết
        self.zen = int(self.zen * 0.90)

    # ── Di chuyển ─────────────────────────────────────────────────────────
    def set_move_target(self, tx: float, ty: float):
        self._move_target = (tx, ty)

    def move_toward(self, tx: float, ty: float, dt: float, tilemap) -> bool:
        """Di chuyển 1 bước về phía (tx, ty). Trả về True nếu đã đến nơi."""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.15:
            self.x, self.y = tx, ty
            return True
        spd = self.move_speed
        nx  = self.x + (dx / dist) * spd * dt
        ny  = self.y + (dy / dist) * spd * dt
        if tilemap.is_walkable_f(nx, ny):
            self.x, self.y = nx, ny
        elif tilemap.is_walkable_f(nx, self.y):
            self.x = nx
        elif tilemap.is_walkable_f(self.x, ny):
            self.y = ny
        return False

    def update_movement(self, dt: float, tilemap):
        if self._move_target:
            tx, ty = self._move_target
            done = self.move_toward(tx, ty, dt, tilemap)
            if done:
                self._move_target = None

    # ── Buffs ─────────────────────────────────────────────────────────────
    def add_buff(self, buff: dict):
        self.buffs.append(buff.copy())

    def update_buffs(self, dt: float):
        new_buffs = []
        for b in self.buffs:
            b["duration"] = b.get("duration", 0) - dt
            if b["duration"] > 0:
                new_buffs.append(b)
        self.buffs = new_buffs

    # ── Cooldown ──────────────────────────────────────────────────────────
    def update_timers(self, dt: float):
        self.atk_timer = max(0.0, self.atk_timer - dt)
        for sk in list(self.skill_timer):
            self.skill_timer[sk] = max(0.0, self.skill_timer[sk] - dt)
        if self.invincible:
            self.inv_timer -= dt
            if self.inv_timer <= 0:
                self.invincible = False
                self.inv_timer  = 0.0

    def can_attack(self) -> bool:
        return self.atk_timer <= 0 and self.alive

    def can_use_skill(self, skill_id: str) -> bool:
        if not self.alive:
            return False
        sk = SKILLS.get(skill_id)
        if not sk:
            return False
        if self.mp < sk["mp_cost"]:
            return False
        return self.skill_timer.get(skill_id, 0) <= 0

    # ── Main update ───────────────────────────────────────────────────────
    def update(self, dt: float, tilemap):
        self.update_timers(dt)
        self.update_buffs(dt)
        self.regen_tick(dt)
        self.update_movement(dt, tilemap)

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, camera, font: pygame.font.Font):
        from data.maps import TILE_SIZE
        sx, sy = camera.tile_to_screen(self.x, self.y)
        sx, sy = int(sx), int(sy)

        # Nhấp nháy khi invincible
        if self.invincible and int(self.inv_timer * 6) % 2 == 0:
            return

        # Shadow
        pygame.draw.ellipse(screen, (0, 0, 0, 80),
                            (sx + 6, sy + TILE_SIZE - 6,
                             TILE_SIZE - 12, 8))

        # Thân nhân vật (hình tròn)
        color = self.color
        r = TILE_SIZE // 2 - 2
        cx = sx + TILE_SIZE // 2
        cy = sy + TILE_SIZE // 2
        pygame.draw.circle(screen, color, (cx, cy), r)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), r, 2)

        # Ký tự class
        txt = font.render(self.char, True, (255, 255, 255))
        screen.blit(txt, (cx - txt.get_width() // 2,
                          cy - txt.get_height() // 2))

        # Thanh HP nhỏ
        bar_w = TILE_SIZE - 4
        bar_h = 4
        bx    = sx + 2
        by    = sy - 6
        pygame.draw.rect(screen, (80, 0, 0), (bx, by, bar_w, bar_h))
        hp_w = int(bar_w * (self.hp / max(1, self.max_hp)))
        pygame.draw.rect(screen, (220, 50, 50), (bx, by, hp_w, bar_h))

        # Tên
        nm = font.render(self.name, True, (255, 255, 100))
        screen.blit(nm, (cx - nm.get_width() // 2, sy - 16))
