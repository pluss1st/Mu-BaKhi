"""
combat.py - Hệ thống chiến đấu
Dựa theo Attack.cpp / CustomAttack.cpp / Skill.cpp
"""
import math
import random
import pygame
from data.skills     import SKILLS
from data.items      import ITEMS
from engine.event_bus import bus, EVT_DAMAGE_DEALT, EVT_SKILL_USED


class CombatSystem:
    """
    Xử lý toàn bộ logic combat:
    - Player attack monster
    - Skill usage
    - Projectile management
    """

    def __init__(self, particle_system):
        self.particles   = particle_system
        self.projectiles: list[dict] = []

    # ── Player đánh thường ────────────────────────────────────────────────
    def player_attack(self, player, monster) -> int:
        if not player.can_attack():
            return 0
        if not monster.alive:
            return 0

        dist = math.dist((player.x, player.y), (monster.x, monster.y))
        if dist > 1.8:
            return 0

        dmg_raw  = random.randint(player.attack_min, player.attack_max)
        critical = (random.random() < 0.05 + player.stat_agi * 0.001)
        if critical:
            dmg_raw = int(dmg_raw * 1.5)

        dmg = monster.take_damage(dmg_raw)
        player.atk_timer = player.attack_speed

        # Particles
        mx_px = monster.x * 32 + 16
        my_px = monster.y * 32 + 16
        self.particles.spawn_damage(mx_px, my_px, dmg, critical)
        self.particles.spawn_hit(mx_px, my_px)

        # EXP nếu monster chết
        if not monster.alive:
            exp = monster.data["exp"]
            # EXP penalty nếu level chênh lệch nhiều
            lv_diff = player.level - monster.level
            if lv_diff > 10:
                exp = max(1, int(exp * (0.9 ** (lv_diff - 10))))
            player.gain_exp(exp)
            self.particles.spawn_exp(mx_px, my_px, exp)
            # Zen
            lo, hi = monster.data.get("zen", (0, 0))
            player.zen += random.randint(lo, hi)
            player.kills += 1

        bus.emit(EVT_DAMAGE_DEALT, source=player, target=monster,
                 damage=dmg, critical=critical)
        return dmg

    # ── Sử dụng skill ─────────────────────────────────────────────────────
    def player_use_skill(self, player, skill_id: str,
                         monsters: list, target_x: float, target_y: float):
        """
        Kích hoạt skill:
        - attack: damage trực tiếp hoặc projectile
        - support: heal, buff
        """
        if not player.can_use_skill(skill_id):
            return

        sk = SKILLS.get(skill_id)
        if not sk:
            return

        # Tiêu MP
        player.mp -= sk["mp_cost"]
        player.skill_timer[skill_id] = sk["cooldown"]

        sk_type = sk["type"]
        bus.emit(EVT_SKILL_USED, player=player, skill_id=skill_id)

        if sk_type == "attack":
            self._skill_attack(player, sk, skill_id, monsters,
                               target_x, target_y)

        elif sk_type == "support":
            if skill_id == "heal":
                heal_amt = int(player.max_hp * sk["heal_pct"])
                player.heal(heal_amt)
                self.particles.spawn_heal(
                    player.x * 32 + 16, player.y * 32 + 16, heal_amt)

        elif sk_type == "buff":
            eff = sk.get("effect", {})
            buff = {
                "defense_up": eff.get("defense_up", 0),
                "duration":   eff.get("duration", 0),
            }
            player.add_buff(buff)

        elif sk_type == "summon":
            # Placeholder — trong full game sẽ spawn pet/minion
            pass

    def _skill_attack(self, player, sk: dict, skill_id: str,
                      monsters: list, tx: float, ty: float):
        mult     = sk.get("damage_mult", 1.0)
        rng      = sk.get("range", 1)
        is_aoe   = sk.get("aoe", False)
        aoe_r    = sk.get("aoe_radius", 0)
        is_proj  = sk.get("projectile", False)

        dmg_raw = int(random.randint(player.attack_min, player.attack_max) * mult
                      + player.stat_ene * 0.3)

        if is_proj:
            # Tạo projectile bay về phía target
            self._spawn_projectile(player, sk, skill_id, dmg_raw, tx, ty, is_aoe, aoe_r, monsters)
        else:
            # Melee / instant AoE
            self._apply_skill_damage(player, dmg_raw, monsters,
                                     tx, ty, rng, is_aoe, aoe_r, sk)

    def _spawn_projectile(self, player, sk, skill_id, dmg, tx, ty, is_aoe, aoe_r, monsters):
        dx = tx - player.x
        dy = ty - player.y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        spd  = 8.0
        color_map = {
            "fire":      (255, 140, 0),
            "ice":       (180, 220, 255),
            "lightning": (255, 255, 100),
            "physical":  (200, 200, 200),
            "fire":      (255, 100, 0),
            "dark":      (150, 50, 200),
        }
        element = sk.get("element", "physical")
        color   = color_map.get(element, (255, 255, 255))

        self.projectiles.append({
            "x":         float(player.x),
            "y":         float(player.y),
            "vx":        (dx / dist) * spd,
            "vy":        (dy / dist) * spd,
            "damage":    dmg,
            "range":     sk.get("range", 6),
            "is_aoe":    is_aoe,
            "aoe_r":     aoe_r,
            "color":     color,
            "skill":     sk,
            "owner":     player,
            "monsters":  monsters,
            "life":      sk.get("range", 6) / spd,
            "effect":    sk.get("effect", {}),
        })

    def _apply_skill_damage(self, player, dmg_raw, monsters,
                            cx, cy, rng, is_aoe, aoe_r, sk):
        effect = sk.get("effect", {})
        if is_aoe:
            for m in monsters:
                if not m.alive:
                    continue
                dist = math.dist((m.x, m.y), (cx, cy))
                if dist <= aoe_r:
                    self._hit_monster(player, m, dmg_raw, effect)
        else:
            # Nhắm nearest trong range
            best = None
            best_dist = rng + 0.5
            for m in monsters:
                if not m.alive:
                    continue
                dist = math.dist((player.x, player.y), (m.x, m.y))
                if dist < best_dist:
                    best_dist = dist
                    best = m
            if best:
                self._hit_monster(player, best, dmg_raw, effect)

    def _hit_monster(self, player, monster, dmg_raw, effect: dict):
        critical = random.random() < 0.08 + player.stat_agi * 0.001
        if critical:
            dmg_raw = int(dmg_raw * 1.5)
        dmg = monster.take_damage(dmg_raw)

        mx_px = monster.x * 32 + 16
        my_px = monster.y * 32 + 16
        self.particles.spawn_damage(mx_px, my_px, dmg, critical)
        self.particles.spawn_hit(mx_px, my_px, color=(255, 180, 50))

        # Apply effect (slow, etc.)
        if effect.get("slow"):
            monster.move_speed = max(0.3, monster.data["move_speed"] * 0.4)
            # Sẽ restore sau vài giây (đơn giản hóa: reset khi respawn)

        if not monster.alive:
            exp = monster.data["exp"]
            lv_diff = player.level - monster.level
            if lv_diff > 10:
                exp = max(1, int(exp * (0.9 ** (lv_diff - 10))))
            player.gain_exp(exp)
            self.particles.spawn_exp(mx_px, my_px, exp)
            lo, hi = monster.data.get("zen", (0, 0))
            player.zen += random.randint(lo, hi)
            player.kills += 1

    # ── Cập nhật projectiles ──────────────────────────────────────────────
    def update(self, dt: float):
        alive_proj = []
        for p in self.projectiles:
            p["x"]    += p["vx"] * dt
            p["y"]    += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                # AoE khi hết life
                if p["is_aoe"]:
                    self._apply_skill_damage(
                        p["owner"], p["damage"], p["monsters"],
                        p["x"], p["y"], 0, True, p["aoe_r"], p["skill"])
                continue
            # Kiểm tra va chạm với quái
            hit = False
            for m in p["monsters"]:
                if not m.alive:
                    continue
                if math.dist((p["x"], p["y"]), (m.x, m.y)) < 0.8:
                    if p["is_aoe"]:
                        self._apply_skill_damage(
                            p["owner"], p["damage"], p["monsters"],
                            m.x, m.y, 0, True, p["aoe_r"], p["skill"])
                    else:
                        self._hit_monster(p["owner"], m, p["damage"], p["skill"].get("effect", {}))
                    hit = True
                    break
            if not hit:
                alive_proj.append(p)
        self.projectiles = alive_proj

    # ── Vẽ projectiles ────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, camera):
        for p in self.projectiles:
            sx, sy = camera.tile_to_screen(p["x"], p["y"])
            pygame.draw.circle(screen, p["color"],
                               (int(sx + 16), int(sy + 16)), 6)
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(sx + 16), int(sy + 16)), 6, 1)
