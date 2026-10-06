"""
panels.py - Inventory panel, Character stats panel, Shop panel, Game Over screen
"""
import pygame
from data.items  import ITEMS, EQUIP_SLOTS
from data.skills import SKILLS

C_BG    = (20,  20,  30,  200)
C_PANEL = (35,  35,  55)
C_HDR   = (50,  60,  90)
C_GOLD  = (255, 215, 0)
C_WHITE = (255, 255, 255)
C_GRAY  = (150, 150, 160)
C_GREEN = (50,  200, 80)
C_RED   = (220, 50,  50)
C_BLUE  = (80,  130, 220)


def _panel_bg(screen, rect, alpha=210):
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    s.fill((20, 20, 35, alpha))
    screen.blit(s, rect.topleft)
    pygame.draw.rect(screen, (80, 80, 120), rect, 2)


class InventoryPanel:
    """
    Panel 10x6 grid hiển thị inventory + equipment slots.
    Click để equip/use, right-click để drop.
    """

    CELL    = 44
    COLS    = 8
    ROWS    = 8
    PAD     = 12

    def __init__(self, screen_w, screen_h):
        self.sw, self.sh = screen_w, screen_h
        pw = self.COLS * self.CELL + self.PAD * 2 + 160
        ph = self.ROWS * self.CELL + self.PAD * 2 + 50
        self.rect = pygame.Rect(
            screen_w // 2 - pw // 2,
            screen_h // 2 - ph // 2,
            pw, ph
        )
        self.font_sm = pygame.font.SysFont("Arial", 11)
        self.font_md = pygame.font.SysFont("Arial", 13, bold=True)
        self.hover_slot: int | None = None
        self.tooltip_text: list[str] = []

    def draw(self, screen: pygame.Surface, player):
        _panel_bg(screen, self.rect)

        # Tiêu đề
        t = self.font_md.render("INVENTORY", True, C_GOLD)
        screen.blit(t, (self.rect.x + self.PAD, self.rect.y + 12))
        pygame.draw.line(screen, (80, 80, 120),
                         (self.rect.x + self.PAD, self.rect.y + 32),
                         (self.rect.right - self.PAD, self.rect.y + 32))

        gx = self.rect.x + self.PAD
        gy = self.rect.y + 40

        for i in range(self.COLS * self.ROWS):
            col = i % self.COLS
            row = i // self.COLS
            x   = gx + col * self.CELL
            y   = gy + row * self.CELL
            cell_rect = pygame.Rect(x, y, self.CELL - 2, self.CELL - 2)

            # Nền ô
            bg_color = (50, 50, 70) if i != self.hover_slot else (70, 70, 100)
            pygame.draw.rect(screen, bg_color, cell_rect)
            pygame.draw.rect(screen, (80, 80, 110), cell_rect, 1)

            slot = player.inventory[i] if i < len(player.inventory) else None
            if slot:
                item_data = ITEMS.get(slot["item_key"], {})
                color     = item_data.get("color", C_WHITE)
                char      = item_data.get("char", "?")
                # Icon màu
                pygame.draw.rect(screen, color,
                                 (x + 4, y + 4, self.CELL - 10, self.CELL - 18))
                ct = self.font_sm.render(char, True, C_WHITE)
                screen.blit(ct, (x + self.CELL // 2 - 4, y + 10))
                # Qty
                if slot.get("qty", 1) > 1:
                    qt = self.font_sm.render(str(slot["qty"]), True, C_GOLD)
                    screen.blit(qt, (x + self.CELL - qt.get_width() - 3,
                                     y + self.CELL - 16))
                # Level
                if slot.get("level", 0) > 0:
                    lt = self.font_sm.render(f"+{slot['level']}", True, C_GREEN)
                    screen.blit(lt, (x + 2, y + 2))

        # Equipment panel (bên phải)
        self._draw_equipment(screen, player,
                             gx + self.COLS * self.CELL + 10,
                             gy)

        # Tooltip
        if self.hover_slot is not None and self.tooltip_text:
            self._draw_tooltip(screen)

    def _draw_equipment(self, screen, player, x, y):
        t = self.font_md.render("TRANG BỊ", True, C_GOLD)
        screen.blit(t, (x, y - 18))

        slot_order = ["weapon", "shield", "helmet", "armor",
                      "pants", "gloves", "boots", "ring", "pendant"]
        slot_labels = {
            "weapon": "Vũ khí", "shield": "Khiên",
            "helmet": "Mũ",     "armor":  "Giáp",
            "pants":  "Quần",   "gloves": "Găng",
            "boots":  "Giày",   "ring":   "Nhẫn",
            "pendant":"Dây",
        }

        for i, sl in enumerate(slot_order):
            ey = y + i * 18
            item = player.equipment.get(sl)
            lbl  = self.font_sm.render(
                f"{slot_labels[sl]}:", True, C_GRAY)
            screen.blit(lbl, (x, ey))
            if item:
                idata = ITEMS.get(item["item_key"], {})
                nm    = idata.get("name", item["item_key"])
                lv    = item.get("level", 0)
                nm_str = f"{nm}" + (f" +{lv}" if lv > 0 else "")
                nt = self.font_sm.render(nm_str, True, C_WHITE)
                screen.blit(nt, (x + 48, ey))
            else:
                nt = self.font_sm.render("--", True, (80, 80, 100))
                screen.blit(nt, (x + 48, ey))

        # Stats tổng kết
        sy = y + len(slot_order) * 18 + 10
        stats = [
            (f"ATK: {player.attack_min}-{player.attack_max}", C_RED),
            (f"DEF: {player.defense}", C_BLUE),
        ]
        for txt, color in stats:
            surf = self.font_sm.render(txt, True, color)
            screen.blit(surf, (x, sy))
            sy += 16

    def _draw_tooltip(self, screen: pygame.Surface):
        if not self.tooltip_text:
            return
        mpos = pygame.mouse.get_pos()
        lh   = 16
        tw   = max(len(t) * 7 for t in self.tooltip_text) + 16
        th   = len(self.tooltip_text) * lh + 10
        tx   = min(mpos[0] + 12, self.sw - tw - 5)
        ty   = min(mpos[1] + 12, self.sh - th - 5)
        tr   = pygame.Rect(tx, ty, tw, th)
        _panel_bg(screen, tr, alpha=240)
        for i, line in enumerate(self.tooltip_text):
            color = C_GOLD if i == 0 else C_WHITE
            surf  = self.font_sm.render(line, True, color)
            screen.blit(surf, (tx + 8, ty + 5 + i * lh))

    def handle_event(self, event: pygame.event.Event, player) -> str | None:
        """Trả về message nếu có action, None nếu không."""
        mpos = pygame.mouse.get_pos()
        gx   = self.rect.x + self.PAD
        gy   = self.rect.y + 40

        # Hover
        self.hover_slot  = None
        self.tooltip_text = []
        for i in range(self.COLS * self.ROWS):
            col = i % self.COLS
            row = i // self.COLS
            x   = gx + col * self.CELL
            y   = gy + row * self.CELL
            cr  = pygame.Rect(x, y, self.CELL - 2, self.CELL - 2)
            if cr.collidepoint(mpos):
                self.hover_slot = i
                slot = player.inventory[i] if i < len(player.inventory) else None
                if slot:
                    idata = ITEMS.get(slot["item_key"], {})
                    self.tooltip_text = [
                        idata.get("name", slot["item_key"]),
                        f"Loại: {idata.get('type', '?')}",
                    ]
                    for k in ("atk_min", "atk_max", "defense", "heal", "mana"):
                        if k in idata and idata[k]:
                            self.tooltip_text.append(
                                f"{k.replace('_',' ').title()}: {idata[k]}")
                    if slot.get("qty", 1) > 1:
                        self.tooltip_text.append(f"Số lượng: {slot['qty']}")
                break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hover_slot is not None:
                from entities.inventory import InventorySystem
                slot = player.inventory[self.hover_slot] if self.hover_slot < len(player.inventory) else None
                if slot:
                    idata = ITEMS.get(slot["item_key"], {})
                    if idata.get("usable"):
                        ok, msg = InventorySystem.use_item(player, self.hover_slot)
                        return msg
                    elif idata.get("slot"):
                        ok, msg = InventorySystem.equip_item(player, self.hover_slot)
                        return msg
        return None


class CharStatsPanel:
    """Panel stat + phân bổ điểm."""

    def __init__(self, screen_w, screen_h):
        self.sw, self.sh = screen_w, screen_h
        self.rect = pygame.Rect(screen_w // 2 - 160,
                                screen_h // 2 - 200, 320, 400)
        self.font_sm = pygame.font.SysFont("Arial", 12)
        self.font_md = pygame.font.SysFont("Arial", 14, bold=True)

    def draw(self, screen: pygame.Surface, player):
        _panel_bg(screen, self.rect)
        x, y = self.rect.x + 15, self.rect.y + 15

        t = self.font_md.render("NHÂN VẬT", True, C_GOLD)
        screen.blit(t, (x, y)); y += 24

        from data.classes import CLASS_DATA
        cls = CLASS_DATA[player.char_class]
        lines = [
            (f"Tên: {player.name}", C_WHITE),
            (f"Class: {cls['name']}", C_GOLD),
            (f"Level: {player.level} / 400", C_WHITE),
            ("", C_WHITE),
            (f"STR:  {player.stat_str:>4}   (+ Str/lv: {cls['str_per_level']})", C_WHITE),
            (f"AGI:  {player.stat_agi:>4}", C_WHITE),
            (f"VIT:  {player.stat_vit:>4}", C_WHITE),
            (f"ENE:  {player.stat_ene:>4}", C_WHITE),
            ("", C_WHITE),
            (f"HP:   {int(player.hp)}/{player.max_hp}", C_HP if True else C_WHITE),
            (f"MP:   {int(player.mp)}/{player.max_mp}", C_BLUE),
            ("", C_WHITE),
            (f"ATK:  {player.attack_min}-{player.attack_max}", (220, 80, 80)),
            (f"DEF:  {player.defense}", C_BLUE),
            (f"SPD:  {player.move_speed:.1f}", C_GREEN),
            ("", C_WHITE),
            (f"Điểm còn: {player.stat_points}", C_GOLD),
            (f"Zen: {player.zen:,}", (255, 215, 0)),
            (f"Kills: {player.kills}  Deaths: {player.deaths}", C_GRAY),
        ]

        # Button +STR, +AGI, +VIT, +ENE nếu có điểm
        stat_keys = ["stat_str", "stat_agi", "stat_vit", "stat_ene"]
        stat_names = ["STR", "AGI", "VIT", "ENE"]

        for txt, color in lines:
            if txt == "":
                y += 6; continue
            surf = self.font_sm.render(txt, True, color)
            screen.blit(surf, (x, y))
            y += 16

        # Nút phân bổ stat
        if player.stat_points > 0:
            y += 5
            for i, (sk, sn) in enumerate(zip(stat_keys, stat_names)):
                bx = x + i * 72
                br = pygame.Rect(bx, y, 65, 22)
                pygame.draw.rect(screen, (60, 80, 60), br)
                pygame.draw.rect(screen, C_GREEN, br, 1)
                bt = self.font_sm.render(f"+{sn}", True, C_WHITE)
                screen.blit(bt, (bx + 5, y + 4))
            self._stat_btn_y = y

    def handle_event(self, event: pygame.event.Event, player) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if player.stat_points <= 0:
                return None
            mpos = pygame.mouse.get_pos()
            x    = self.rect.x + 15
            stat_keys  = ["stat_str", "stat_agi", "stat_vit", "stat_ene"]
            stat_names = ["STR", "AGI", "VIT", "ENE"]
            y = getattr(self, "_stat_btn_y", -1)
            for i, (sk, sn) in enumerate(zip(stat_keys, stat_names)):
                bx = x + i * 72
                br = pygame.Rect(bx, y, 65, 22)
                if br.collidepoint(mpos):
                    setattr(player, sk, getattr(player, sk) + 1)
                    player.stat_points -= 1
                    player._recalc_max()
                    return f"+1 {sn} → {getattr(player, sk)}"
        return None


class GameOverScreen:
    def __init__(self, screen_w, screen_h):
        self.sw, self.sh = screen_w, screen_h
        self.font_xl = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_lg = pygame.font.SysFont("Arial", 22)
        self.font_md = pygame.font.SysFont("Arial", 16)
        self.timer   = 0.0
        self.active  = False

    def activate(self):
        self.active = True
        self.timer  = 0.0

    def update(self, dt: float):
        if self.active:
            self.timer += dt

    def draw(self, screen: pygame.Surface, player):
        if not self.active:
            return
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(200, int(self.timer * 100))))
        screen.blit(overlay, (0, 0))

        t1 = self.font_xl.render("GAME OVER", True, C_RED)
        t2 = self.font_lg.render(f"{player.name} đã ngã xuống!", True, C_WHITE)
        t3 = self.font_md.render(
            f"Kills: {player.kills}  Deaths: {player.deaths}  Level: {player.level}",
            True, C_GRAY)
        t4 = self.font_md.render("Nhấn R để hồi sinh  |  ESC để thoát",
                                  True, C_GOLD)

        cx = self.sw // 2
        screen.blit(t1, (cx - t1.get_width() // 2, self.sh // 2 - 100))
        screen.blit(t2, (cx - t2.get_width() // 2, self.sh // 2 - 40))
        screen.blit(t3, (cx - t3.get_width() // 2, self.sh // 2 + 10))
        screen.blit(t4, (cx - t4.get_width() // 2, self.sh // 2 + 60))


class MainMenuScreen:
    def __init__(self, screen_w, screen_h):
        self.sw, self.sh = screen_w, screen_h
        self.font_xl = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_lg = pygame.font.SysFont("Arial", 24)
        self.font_md = pygame.font.SysFont("Arial", 16)
        self.buttons = []
        self._build_buttons()
        self.hover   = None

    def _build_buttons(self):
        labels = [
            ("NEW GAME",  "new_game"),
            ("LOAD GAME", "load_game"),
            ("EXIT",      "exit"),
        ]
        bw, bh = 220, 44
        cx = self.sw // 2
        sy = self.sh // 2
        for i, (lbl, action) in enumerate(labels):
            rx = cx - bw // 2
            ry = sy + i * (bh + 12)
            self.buttons.append({
                "rect":   pygame.Rect(rx, ry, bw, bh),
                "label":  lbl,
                "action": action,
            })

    def handle_event(self, event: pygame.event.Event) -> str | None:
        mpos = pygame.mouse.get_pos()
        self.hover = None
        for btn in self.buttons:
            if btn["rect"].collidepoint(mpos):
                self.hover = btn["action"]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(mpos):
                    return btn["action"]
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "new_game"
        return None

    def draw(self, screen: pygame.Surface):
        screen.fill((10, 10, 20))
        # Tiêu đề
        t = self.font_xl.render("MU ONLINE", True, (255, 180, 0))
        screen.blit(t, (self.sw // 2 - t.get_width() // 2, self.sh // 3 - 60))
        s = self.font_lg.render("Offline Edition", True, (180, 180, 255))
        screen.blit(s, (self.sw // 2 - s.get_width() // 2, self.sh // 3))

        for btn in self.buttons:
            is_hov = self.hover == btn["action"]
            pygame.draw.rect(screen,
                             (70, 70, 120) if is_hov else (40, 40, 70),
                             btn["rect"], border_radius=6)
            pygame.draw.rect(screen,
                             (150, 150, 200) if is_hov else (80, 80, 130),
                             btn["rect"], 2, border_radius=6)
            lt = self.font_lg.render(btn["label"], True,
                                     (255, 215, 0) if is_hov else (200, 200, 220))
            screen.blit(lt, (btn["rect"].centerx - lt.get_width() // 2,
                             btn["rect"].centery - lt.get_height() // 2))

        ver = self.font_md.render("v1.0 - Python/Pygame", True, (80, 80, 100))
        screen.blit(ver, (self.sw - ver.get_width() - 10,
                          self.sh - ver.get_height() - 10))


class CharCreateScreen:
    """Màn hình tạo nhân vật."""

    def __init__(self, screen_w, screen_h):
        self.sw, self.sh = screen_w, screen_h
        self.font_xl = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_lg = pygame.font.SysFont("Arial", 18)
        self.font_md = pygame.font.SysFont("Arial", 14)
        self.font_sm = pygame.font.SysFont("Arial", 12)

        self._class_list = ["DW", "DK", "ELF", "MG", "DL"]
        self._class_idx  = 1   # DK mặc định
        self.name_input  = "Hero"
        self.name_active = False

    @property
    def selected_class(self):
        return self._class_list[self._class_idx]

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        if event.type == pygame.KEYDOWN:
            if self.name_active:
                if event.key == pygame.K_BACKSPACE:
                    self.name_input = self.name_input[:-1]
                elif event.key == pygame.K_RETURN:
                    self.name_active = False
                elif len(self.name_input) < 12:
                    if event.unicode.isprintable():
                        self.name_input += event.unicode
            if event.key == pygame.K_LEFT:
                self._class_idx = (self._class_idx - 1) % len(self._class_list)
            if event.key == pygame.K_RIGHT:
                self._class_idx = (self._class_idx + 1) % len(self._class_list)
            if event.key == pygame.K_RETURN and not self.name_active:
                return {"name": self.name_input or "Hero",
                        "char_class": self.selected_class}

        if event.type == pygame.MOUSEBUTTONDOWN:
            mpos = pygame.mouse.get_pos()
            # Click vào ô tên
            name_rect = pygame.Rect(self.sw // 2 - 120,
                                    self.sh // 2 - 60, 240, 32)
            self.name_active = name_rect.collidepoint(mpos)
            # Nút start
            start_rect = pygame.Rect(self.sw // 2 - 80,
                                     self.sh // 2 + 120, 160, 44)
            if start_rect.collidepoint(mpos):
                return {"name": self.name_input or "Hero",
                        "char_class": self.selected_class}
        return None

    def draw(self, screen: pygame.Surface):
        from data.classes import CLASS_DATA
        screen.fill((10, 10, 20))

        t = self.font_xl.render("TẠO NHÂN VẬT", True, (255, 215, 0))
        screen.blit(t, (self.sw // 2 - t.get_width() // 2, 40))

        cls = CLASS_DATA[self.selected_class]
        cx  = self.sw // 2
        cy  = self.sh // 2

        # Class selector
        prev_t = self.font_lg.render("◀", True, (200, 200, 200))
        next_t = self.font_lg.render("▶", True, (200, 200, 200))
        screen.blit(prev_t, (cx - 180, cy - 130))
        screen.blit(next_t, (cx + 160, cy - 130))

        # Class icon
        pygame.draw.circle(screen, cls["color"], (cx, cy - 100), 48)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy - 100), 48, 2)
        ct = self.font_xl.render(cls["char"], True, (255, 255, 255))
        screen.blit(ct, (cx - ct.get_width() // 2, cy - 118))

        # Class name
        cn = self.font_lg.render(cls["name"], True, (255, 215, 0))
        screen.blit(cn, (cx - cn.get_width() // 2, cy - 42))

        # Class description
        desc = self.font_md.render(cls["description"], True, (200, 200, 200))
        screen.blit(desc, (cx - desc.get_width() // 2, cy - 18))

        # Base stats
        stats = (f"STR:{cls['base_str']}  AGI:{cls['base_agi']}  "
                 f"VIT:{cls['base_vit']}  ENE:{cls['base_ene']}")
        st = self.font_sm.render(stats, True, (180, 180, 200))
        screen.blit(st, (cx - st.get_width() // 2, cy + 8))

        # Ô nhập tên
        name_rect = pygame.Rect(cx - 120, cy - 60, 240, 32)
        pygame.draw.rect(screen,
                         (60, 60, 90) if self.name_active else (40, 40, 60),
                         name_rect)
        pygame.draw.rect(screen,
                         (150, 150, 200) if self.name_active else (80, 80, 120),
                         name_rect, 2)
        nl = self.font_md.render("Tên nhân vật:", True, (180, 180, 200))
        screen.blit(nl, (cx - 120, cy - 78))
        nt = self.font_lg.render(
            self.name_input + ("|" if self.name_active else ""),
            True, (255, 255, 255))
        screen.blit(nt, (cx - 120 + 8, cy - 56))

        # Nút bắt đầu
        start_rect = pygame.Rect(cx - 80, cy + 120, 160, 44)
        pygame.draw.rect(screen, (50, 80, 50), start_rect, border_radius=6)
        pygame.draw.rect(screen, (100, 180, 100), start_rect, 2, border_radius=6)
        st2 = self.font_lg.render("BẮT ĐẦU", True, (255, 255, 200))
        screen.blit(st2, (cx - st2.get_width() // 2, cy + 128))

        hint = self.font_sm.render("← → đổi class   Click tên để sửa   Enter để xác nhận",
                                    True, (100, 100, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, self.sh - 30))
