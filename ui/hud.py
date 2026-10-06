"""
hud.py - HUD: HP/MP bar, EXP bar, skill bar, minimap, chat log
"""
import pygame
from data.maps   import TILE_SIZE
from data.skills import SKILLS
from data.items  import ITEMS


# ── Màu sắc ──────────────────────────────────────────────────────────────────
C_HP    = (200, 40,  40)
C_MP    = (40,  80,  200)
C_EXP   = (180, 120, 255)
C_BG    = (20,  20,  30)
C_PANEL = (30,  30,  45)
C_GOLD  = (255, 215, 0)
C_WHITE = (255, 255, 255)
C_GRAY  = (150, 150, 160)
C_GREEN = (50,  200, 80)


class HUD:
    """
    Vẽ toàn bộ HUD overlay:
    - Thanh HP/MP/EXP
    - Skill bar (1-5)
    - Thông tin nhân vật (góc trái)
    - Minimap (góc phải)
    - Chat/log (góc trái dưới)
    - Thông báo (giữa trên)
    """

    LOG_MAX = 8
    MSG_DURATION = 3.0

    def __init__(self, screen_w: int, screen_h: int):
        self.sw = screen_w
        self.sh = screen_h
        self._init_fonts()
        self._log: list[dict] = []       # {text, color, life}
        self._notice: str = ""
        self._notice_timer = 0.0
        self._notice_color = C_GOLD

    def _init_fonts(self):
        pygame.font.init()
        self.font_sm  = pygame.font.SysFont("Arial", 12)
        self.font_md  = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_lg  = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_xl  = pygame.font.SysFont("Arial", 28, bold=True)

    # ── Public API ────────────────────────────────────────────────────────
    def log(self, text: str, color=C_WHITE):
        self._log.append({"text": text, "color": color,
                          "life": self.MSG_DURATION})
        if len(self._log) > self.LOG_MAX:
            self._log.pop(0)

    def notice(self, text: str, color=C_GOLD, duration: float = 2.5):
        self._notice       = text
        self._notice_timer = duration
        self._notice_color = color

    def update(self, dt: float):
        self._log = [m for m in self._log
                     if (m.__setitem__("life", m["life"] - dt) or True)
                     and m["life"] > 0]
        if self._notice_timer > 0:
            self._notice_timer -= dt

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface, player, tilemap, camera):
        self._draw_bars(screen, player)
        self._draw_skill_bar(screen, player)
        self._draw_char_info(screen, player)
        self._draw_minimap(screen, player, tilemap, camera)
        self._draw_log(screen)
        self._draw_notice(screen)
        self._draw_map_name(screen, tilemap)

    # ── Thanh HP / MP / EXP ───────────────────────────────────────────────
    def _draw_bars(self, screen: pygame.Surface, player):
        bw, bh = 220, 18
        mx     = 10
        my     = self.sh - 130

        # Nền
        panel_rect = pygame.Rect(mx - 5, my - 5, bw + 40, 80)
        s = pygame.Surface((panel_rect.w, panel_rect.h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        screen.blit(s, panel_rect.topleft)

        def bar(y, val, mx_val, color, label):
            pygame.draw.rect(screen, (50, 50, 60), (mx, y, bw, bh))
            filled = int(bw * (val / max(1, mx_val)))
            pygame.draw.rect(screen, color, (mx, y, filled, bh))
            pygame.draw.rect(screen, (100, 100, 120), (mx, y, bw, bh), 1)
            lbl = self.font_sm.render(
                f"{label}: {int(val)}/{mx_val}", True, C_WHITE)
            screen.blit(lbl, (mx + 4, y + 2))

        bar(my,      player.hp, player.max_hp, C_HP,  "HP")
        bar(my + 22, player.mp, player.max_mp, C_MP,  "MP")
        bar(my + 44, player.exp, max(1, 1),    C_EXP, "EXP")

        # EXP riêng (% tới level sau)
        from data.classes import EXP_TABLE
        needed = EXP_TABLE.get(player.level, 1)
        pygame.draw.rect(screen, (50, 50, 60), (mx, my + 44, bw, bh))
        exp_w = int(bw * player.exp_percent())
        pygame.draw.rect(screen, C_EXP, (mx, my + 44, exp_w, bh))
        pygame.draw.rect(screen, (100, 100, 120), (mx, my + 44, bw, bh), 1)
        lbl = self.font_sm.render(
            f"EXP: {player.exp}/{needed}", True, C_WHITE)
        screen.blit(lbl, (mx + 4, my + 46))

        # Zen
        zen_txt = self.font_sm.render(f"Zen: {player.zen:,}", True, C_GOLD)
        screen.blit(zen_txt, (mx, my + 66))

    # ── Skill bar ─────────────────────────────────────────────────────────
    def _draw_skill_bar(self, screen: pygame.Surface, player):
        n_slots = 5
        slot_sz = 48
        gap     = 4
        total_w = n_slots * slot_sz + (n_slots - 1) * gap
        sx      = self.sw // 2 - total_w // 2
        sy      = self.sh - 60

        for i, key in enumerate(["1", "2", "3", "4", "5"]):
            skill_id = player.skill_slots.get(key)
            x = sx + i * (slot_sz + gap)

            # Nền slot
            color_bg = (40, 40, 60) if skill_id else (20, 20, 30)
            pygame.draw.rect(screen, color_bg, (x, sy, slot_sz, slot_sz))

            # Skill đang chọn
            if player.active_skill == skill_id and skill_id:
                pygame.draw.rect(screen, C_GOLD, (x, sy, slot_sz, slot_sz), 2)
            else:
                pygame.draw.rect(screen, (80, 80, 100), (x, sy, slot_sz, slot_sz), 1)

            if skill_id:
                sk   = SKILLS.get(skill_id, {})
                name = sk.get("name", skill_id)[:8]
                color = sk.get("color", C_WHITE)

                # Màu icon
                icon_r = pygame.Rect(x + 4, sy + 4, slot_sz - 8, slot_sz - 20)
                pygame.draw.rect(screen, color, icon_r)

                # Cooldown overlay
                cd = player.skill_timer.get(skill_id, 0)
                if cd > 0:
                    max_cd = SKILLS[skill_id]["cooldown"]
                    overlay_h = int((slot_sz - 8) * (cd / max(1, max_cd)))
                    pygame.draw.rect(screen, (0, 0, 0, 180),
                                     (x + 4, sy + 4, slot_sz - 8, overlay_h))
                    cd_txt = self.font_sm.render(f"{cd:.1f}", True, C_WHITE)
                    screen.blit(cd_txt, (x + slot_sz // 2 - cd_txt.get_width() // 2,
                                         sy + slot_sz // 2 - 10))

                # Tên skill
                nt = self.font_sm.render(name, True, C_WHITE)
                screen.blit(nt, (x + slot_sz // 2 - nt.get_width() // 2,
                                 sy + slot_sz - 14))

            # Phím tắt
            kt = self.font_sm.render(key, True, C_GRAY)
            screen.blit(kt, (x + 3, sy + 2))

    # ── Thông tin nhân vật (góc trái trên) ───────────────────────────────
    def _draw_char_info(self, screen: pygame.Surface, player):
        x, y = 10, 10
        lines = [
            (f"{player.name}  [{player.char_class}]", C_GOLD),
            (f"Lv.{player.level}  Kills:{player.kills}", C_WHITE),
            (f"STR:{player.stat_str} AGI:{player.stat_agi} "
             f"VIT:{player.stat_vit} ENE:{player.stat_ene}", C_GRAY),
        ]
        for txt, color in lines:
            surf = self.font_sm.render(txt, True, color)
            screen.blit(surf, (x, y))
            y += 16

    # ── Minimap (góc phải trên) ───────────────────────────────────────────
    def _draw_minimap(self, screen: pygame.Surface, player, tilemap, camera):
        mm_w, mm_h = 140, 140
        mm_x = self.sw - mm_w - 10
        mm_y = 10
        scale_x = mm_w / tilemap.width
        scale_y = mm_h / tilemap.height

        # Nền
        bg = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        screen.blit(bg, (mm_x, mm_y))
        pygame.draw.rect(screen, (100, 100, 140),
                         (mm_x, mm_y, mm_w, mm_h), 1)

        # Vẽ tile (đơn giản, 1 pixel/tile khi scale nhỏ)
        from data.maps import TILE_COLORS, TILE_WALKABLE
        for ty in range(0, tilemap.height, 2):
            for tx in range(0, tilemap.width, 2):
                tile_id = tilemap.layout[ty][tx]
                color   = TILE_COLORS.get(tile_id, (50, 50, 50))
                px = mm_x + int(tx * scale_x)
                py = mm_y + int(ty * scale_y)
                pw = max(1, int(scale_x * 2))
                ph = max(1, int(scale_y * 2))
                pygame.draw.rect(screen, color, (px, py, pw, ph))

        # Cổng
        for gate in tilemap.gates:
            gx, gy = gate["at"]
            px = mm_x + int(gx * scale_x)
            py = mm_y + int(gy * scale_y)
            pygame.draw.rect(screen, C_GOLD, (px - 1, py - 1, 4, 4))

        # Player
        px = mm_x + int(player.x * scale_x)
        py = mm_y + int(player.y * scale_y)
        pygame.draw.circle(screen, (255, 255, 100), (px, py), 3)

        # Tên bản đồ
        nm = self.font_sm.render(tilemap.name, True, C_WHITE)
        screen.blit(nm, (mm_x + mm_w // 2 - nm.get_width() // 2,
                         mm_y + mm_h + 2))

    # ── Chat / log ────────────────────────────────────────────────────────
    def _draw_log(self, screen: pygame.Surface):
        x = 10
        y = self.sh - 145
        for msg in reversed(self._log):
            alpha = min(255, int(255 * (msg["life"] / self.MSG_DURATION)))
            surf  = self.font_sm.render(msg["text"], True, msg["color"])
            surf.set_alpha(alpha)
            y -= 15
            screen.blit(surf, (x, y))

    # ── Thông báo giữa màn hình ───────────────────────────────────────────
    def _draw_notice(self, screen: pygame.Surface):
        if self._notice_timer <= 0 or not self._notice:
            return
        alpha = min(255, int(255 * min(1.0, self._notice_timer / 0.5)))
        surf  = self.font_xl.render(self._notice, True, self._notice_color)
        surf.set_alpha(alpha)
        x = self.sw // 2 - surf.get_width() // 2
        y = self.sh // 2 - 80
        screen.blit(surf, (x, y))

    # ── Tên bản đồ hiện tại ───────────────────────────────────────────────
    def _draw_map_name(self, screen: pygame.Surface, tilemap):
        txt = self.font_md.render(f"📍 {tilemap.name}", True, C_GOLD)
        screen.blit(txt, (self.sw // 2 - txt.get_width() // 2, 8))
