"""
main.py - Entry point game MU Online Offline
Chạy: py main.py
Yêu cầu: pip install pygame
"""
import sys
import os
import pygame
import math

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── Imports game modules ──────────────────────────────────────────────────────
from data.maps              import MAP_DATA, TILE_SIZE
from data.items             import ITEMS
from data.skills            import SKILLS
from engine.camera          import Camera
from engine.tilemap         import TileMap
from engine.game_state      import GameStateManager, State
from engine.event_bus       import bus, EVT_PLAYER_LEVEL_UP, EVT_PLAYER_DIED, EVT_MONSTER_DIED
from engine.particle        import ParticleSystem
from engine.save_load       import save_game, load_game, list_saves
from entities.player        import Player
from entities.combat        import CombatSystem
from entities.spawn_manager import SpawnManager
from entities.inventory     import InventorySystem
from ui.hud                 import HUD
from ui.panels              import (InventoryPanel, CharStatsPanel,
                                    GameOverScreen, MainMenuScreen,
                                    CharCreateScreen)
from ui.touch_controls      import TouchControlsOverlay

# ── Cấu hình ─────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS                = 60
TITLE              = "MU Online – Offline Edition"

# Phát hiện Android
import os as _os
ANDROID = _os.path.exists("/sdcard") and not _os.path.exists("C:\\")

# Android dùng fullscreen
if ANDROID:
    SCREEN_W, SCREEN_H = 0, 0   # fullscreen native resolution

C_BG = (20, 20, 30)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        if ANDROID:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            sw = self.screen.get_width()
            sh = self.screen.get_height()
        else:
            sw, sh = SCREEN_W, SCREEN_H
            self.screen = pygame.display.set_mode((sw, sh))
        self.sw = sw
        self.sh = sh
        self.clock   = pygame.time.Clock()
        self.running = True

        # ── Core systems ──────────────────────────────────────────────────
        self.states      = GameStateManager()
        self.particles   = ParticleSystem()
        self.camera      = Camera(sw, sh, TILE_SIZE)
        self.combat      = CombatSystem(self.particles)

        # ── UI ────────────────────────────────────────────────────────────
        self.hud         = HUD(sw, sh)
        self.inv_panel   = InventoryPanel(sw, sh)
        self.stat_panel  = CharStatsPanel(sw, sh)
        self.gameover    = GameOverScreen(sw, sh)
        self.main_menu   = MainMenuScreen(sw, sh)
        self.char_create = CharCreateScreen(sw, sh)
        self.touch       = TouchControlsOverlay(sw, sh)

        # ── Font chung ────────────────────────────────────────────────────
        self.font = pygame.font.SysFont("Arial", 14, bold=True)

        # ── Game objects (set khi start game) ─────────────────────────────
        self.player:  Player | None     = None
        self.tilemap: TileMap | None    = None
        self.spawner: SpawnManager | None = None
        self._tilemaps: dict[str, TileMap]    = {}
        self._spawners: dict[str, SpawnManager] = {}

        # ── Event subscriptions ───────────────────────────────────────────
        bus.subscribe(EVT_PLAYER_LEVEL_UP, self._on_level_up)
        bus.subscribe(EVT_PLAYER_DIED,     self._on_player_died)
        bus.subscribe(EVT_MONSTER_DIED,    self._on_monster_died)

        # ── Preload tilemaps ───────────────────────────────────────────────
        for key, info in MAP_DATA.items():
            self._tilemaps[key] = TileMap(key, info)

        # ── Trạng thái cổng (cooldown tránh teleport loop) ────────────────
        self._gate_cooldown = 0.0

        # ── Log buffer ───────────────────────────────────────────────────
        self._pending_msg: list[tuple[str, tuple]] = []

    # ═══════════════════════════════════════════════════════════════════════
    # KHỞI TẠO GAME
    # ═══════════════════════════════════════════════════════════════════════
    def _start_new_game(self, name: str, char_class: str):
        self.player = Player(name, char_class, 22.0, 22.0, "lorencia")
        # Thêm vật phẩm starter
        InventorySystem.add_item(self.player, "small_healing_potion", 10)
        InventorySystem.add_item(self.player, "small_mana_potion", 5)
        InventorySystem.add_item(self.player, "zen", 500)
        self._load_map("lorencia")
        self.states.change(State.PLAYING)

    def _load_map(self, map_key: str):
        self.tilemap = self._tilemaps[map_key]
        self.camera.set_map_size(self.tilemap.width, self.tilemap.height)
        if map_key not in self._spawners:
            self._spawners[map_key] = SpawnManager(map_key)
        self.spawner = self._spawners[map_key]
        self.combat.projectiles.clear()
        self._gate_cooldown = 1.5   # tránh ngay lập tức bước qua cổng lại

    def _load_save(self, save_data: dict):
        p = Player(
            save_data["char_name"],
            save_data["char_class"],
            save_data["pos_x"],
            save_data["pos_y"],
            save_data["current_map"],
        )
        p.level      = save_data["level"]
        p.exp        = save_data["exp"]
        p.stat_str   = save_data["str"]
        p.stat_agi   = save_data["agi"]
        p.stat_vit   = save_data["vit"]
        p.stat_ene   = save_data["ene"]
        p.stat_points = save_data["stat_points"]
        p.zen        = save_data["zen"]
        p.kills      = save_data["kills"]
        p.deaths     = save_data["deaths"]
        p.skill_slots = save_data["skill_slots"]
        # Load inventory
        for i, slot in enumerate(save_data.get("inventory", [])):
            if i < len(p.inventory):
                p.inventory[i] = slot
        # Load equipment
        for sl, item in save_data.get("equipment", {}).items():
            if item:
                idata = ITEMS.get(item["item_key"], {})
                p.equipment[sl] = {**idata, **item}
        p._recalc_max()
        p.hp = float(min(save_data["hp"], p.max_hp))
        p.mp = float(min(save_data["mp"], p.max_mp))
        self.player = p
        self._load_map(p.current_map)
        self.states.change(State.PLAYING)

    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
    def _on_level_up(self, player, level, **kw):
        self.hud.notice(f"LEVEL UP!  Lv.{level}", color=(255, 215, 0))
        self.hud.log(f"Lên level {level}! +5 stat points", color=(255, 215, 0))
        self.particles.spawn_level_up(
            player.x * TILE_SIZE + 16,
            player.y * TILE_SIZE + 16)
        self.states.push(State.LEVEL_UP)

    def _on_player_died(self, player, **kw):
        self.hud.log("Bạn đã chết!", color=(255, 50, 50))
        self.gameover.activate()
        self.states.change(State.GAME_OVER)

    def _on_monster_died(self, monster, **kw):
        self.hud.log(f"Tiêu diệt {monster.name}!", color=(200, 200, 100))

    # ═══════════════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════════════════════════════════
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # cap delta time

            self._handle_events()
            self._update(dt)
            self._draw()

        pygame.quit()

    # ── Events ────────────────────────────────────────────────────────────
    def _handle_events(self):
        state = self.states.current

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # ── Main menu ─────────────────────────────────────────────────
            if state == State.MAIN_MENU:
                action = self.main_menu.handle_event(event)
                if action == "new_game":
                    self.states.change(State.CHAR_CREATE)
                elif action == "load_game":
                    saves = list_saves()
                    if saves:
                        try:
                            data = load_game(saves[0]["path"])
                            self._load_save(data)
                            self.hud.log("Game đã được tải!", color=(100, 255, 100))
                        except Exception as e:
                            self.hud.log(f"Lỗi tải: {e}", color=(255, 100, 100))
                    else:
                        self.hud.notice("Chưa có save!", color=(255, 100, 100))
                elif action == "exit":
                    self.running = False

            # ── Char create ───────────────────────────────────────────────
            elif state == State.CHAR_CREATE:
                result = self.char_create.handle_event(event)
                if result:
                    self._start_new_game(result["name"], result["char_class"])
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.states.change(State.MAIN_MENU)

            # ── Game over ─────────────────────────────────────────────────
            elif state == State.GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.player.respawn(22.0, 22.0, "lorencia")
                        self._load_map("lorencia")
                        self.gameover.active = False
                        self.states.change(State.PLAYING)
                    elif event.key == pygame.K_ESCAPE:
                        self.states.change(State.MAIN_MENU)

            # ── Playing ───────────────────────────────────────────────────
            elif state == State.PLAYING:
                # Touch controls
                action = self.touch.handle_event(event)
                if action:
                    self._handle_touch_action(action)
                else:
                    self._handle_playing_event(event)

            # ── Inventory ─────────────────────────────────────────────────
            elif state == State.INVENTORY:
                msg = self.inv_panel.handle_event(event, self.player)
                if msg:
                    self.hud.log(msg)
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_i, pygame.K_ESCAPE):
                    self.states.pop()

            # ── Stats panel (C) ───────────────────────────────────────────
            elif state == State.LEVEL_UP:
                msg = self.stat_panel.handle_event(event, self.player)
                if msg:
                    self.hud.log(msg)
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_c, pygame.K_ESCAPE):
                    self.states.pop()

            # ── Paused ────────────────────────────────────────────────────
            elif state == State.PAUSED:
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE, pygame.K_p):
                    self.states.pop()

    def _handle_touch_action(self, action: str):
        """Xử lý action từ touch controls."""
        p = self.player
        if not p or not p.alive:
            return
        if action == "attack":
            if p.target and p.target.alive:
                self.combat.player_attack(p, p.target)
            else:
                m = self.spawner.nearest_monster(p.x, p.y, max_dist=3.0)
                if m:
                    p.target = m
                    self.combat.player_attack(p, m)
        elif action == "skill_2":
            sk = p.skill_slots.get("2")
            if sk:
                p.active_skill = sk
                tx = p.x + (p.target.x - p.x if p.target else 2)
                ty = p.y + (p.target.y - p.y if p.target else 0)
                self.combat.player_use_skill(p, sk, self.spawner.monsters, tx, ty)
        elif action == "skill_3":
            sk = p.skill_slots.get("3")
            if sk:
                p.active_skill = sk
                tx = p.x + (p.target.x - p.x if p.target else 2)
                ty = p.y + (p.target.y - p.y if p.target else 0)
                self.combat.player_use_skill(p, sk, self.spawner.monsters, tx, ty)
        elif action == "skill_4":
            sk = p.skill_slots.get("4")
            if sk:
                p.active_skill = sk
                tx = p.x + (p.target.x - p.x if p.target else 2)
                ty = p.y + (p.target.y - p.y if p.target else 0)
                self.combat.player_use_skill(p, sk, self.spawner.monsters, tx, ty)
        elif action == "pickup":
            picked = self.spawner.pick_nearby(p, ITEMS)
            for item in picked:
                ok = InventorySystem.add_item(p, item["item_key"], item["qty"])
                idata = ITEMS.get(item["item_key"], {})
                if ok:
                    self.hud.log(f"Nhặt: {idata.get('name', item['item_key'])}", color=(200, 255, 200))
        elif action == "heal":
            self._quick_use_potion(p, "hp")
        elif action == "inventory":
            self.states.push(State.INVENTORY)

    def _handle_playing_event(self, event: pygame.event.Event):
        p = self.player

        if event.type == pygame.KEYDOWN:
            key = event.key

            # Di chuyển WASD
            if key in (pygame.K_i,):
                self.states.push(State.INVENTORY)
            elif key == pygame.K_c:
                self.states.push(State.LEVEL_UP)
            elif key == pygame.K_ESCAPE:
                self.states.push(State.PAUSED)

            # Skill slots 1-5
            elif event.unicode in ("1","2","3","4","5"):
                slot_key = event.unicode
                sk_id    = p.skill_slots.get(slot_key)
                if sk_id:
                    p.active_skill = sk_id

            # Nhặt item Z
            elif key == pygame.K_z:
                picked = self.spawner.pick_nearby(p, ITEMS)
                for item in picked:
                    ok = InventorySystem.add_item(p, item["item_key"], item["qty"])
                    idata = ITEMS.get(item["item_key"], {})
                    if ok:
                        self.hud.log(
                            f"Nhặt: {idata.get('name', item['item_key'])} x{item['qty']}",
                            color=(200, 255, 200))
                    else:
                        self.hud.log("Inventory đầy!", color=(255, 150, 100))

            # Sử dụng potion nhanh: H = heal potion, M = mana potion
            elif key == pygame.K_h:
                self._quick_use_potion(p, "hp")
            elif key == pygame.K_m:
                self._quick_use_potion(p, "mp")

            # Save game
            elif key == pygame.K_F5:
                try:
                    path = save_game(p)
                    self.hud.log(f"Đã lưu game: {os.path.basename(path)}",
                                  color=(100, 255, 100))
                except Exception as e:
                    self.hud.log(f"Lỗi lưu: {e}", color=(255, 100, 100))

        if event.type == pygame.MOUSEBUTTONDOWN:
            mpos = pygame.mouse.get_pos()
            tx, ty = self.camera.screen_to_tile(*mpos)

            if event.button == 1:   # Click trái → di chuyển hoặc tấn công
                # Kiểm tra có quái không
                monster = self.spawner.monster_at(tx, ty, radius=0.8)
                if monster:
                    p.target = monster
                    p._move_target = None
                    # Nếu trong tầm → đánh ngay
                    dist = math.dist((p.x, p.y), (monster.x, monster.y))
                    if dist <= 1.8:
                        dmg = self.combat.player_attack(p, monster)
                    else:
                        # Di chuyển về gần rồi đánh
                        p.set_move_target(monster.x, monster.y)
                else:
                    p.target = None
                    if self.tilemap.is_walkable_f(tx, ty):
                        p.set_move_target(tx, ty)

            elif event.button == 3:  # Click phải → dùng skill active
                monster = self.spawner.monster_at(tx, ty, radius=1.0)
                if monster:
                    p.target = monster
                sk_id = p.active_skill
                if sk_id and sk_id != "melee":
                    self.combat.player_use_skill(
                        p, sk_id, self.spawner.monsters, tx, ty)
                elif sk_id == "melee" and monster:
                    self.combat.player_attack(p, monster)

    def _quick_use_potion(self, player, subtype: str):
        for i, slot in enumerate(player.inventory):
            if slot:
                idata = ITEMS.get(slot["item_key"], {})
                if (idata.get("type") == "potion"
                        and idata.get("subtype") == subtype):
                    ok, msg = InventorySystem.use_item(player, i)
                    if ok:
                        self.hud.log(msg, color=(100, 255, 100))
                        return
        self.hud.log("Không có thuốc!", color=(255, 150, 100))

    # ── Update ────────────────────────────────────────────────────────────
    def _update(self, dt: float):
        state = self.states.current
        self.hud.update(dt)
        self.gameover.update(dt)

        if state not in (State.PLAYING, State.LEVEL_UP, State.PAUSED):
            return
        if state == State.PAUSED:
            return

        p = self.player
        if not p:
            return

        # Player update
        p.update(dt, self.tilemap)

        # Auto-attack target nếu đang nhắm
        if p.target and p.target.alive and p.can_attack():
            dist = math.dist((p.x, p.y), (p.target.x, p.target.y))
            if dist <= 1.8:
                self.combat.player_attack(p, p.target)
            else:
                p.set_move_target(p.target.x, p.target.y)
        elif p.target and not p.target.alive:
            p.target = None

        # WASD movement
        keys = pygame.key.get_pressed()
        spd  = p.move_speed * dt
        nx, ny = p.x, p.y
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            nx -= spd
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            nx += spd
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            ny -= spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            ny += spd

        # Touch joystick movement
        jdx, jdy = self.touch.get_move_vector()
        if abs(jdx) > 0.1 or abs(jdy) > 0.1:
            nx += jdx * p.move_speed * dt
            ny += jdy * p.move_speed * dt
            p._move_target = None

        if (nx, ny) != (p.x, p.y):
            p._move_target = None  # Hủy click target khi WASD
            if self.tilemap.is_walkable_f(nx, ny):
                p.x, p.y = nx, ny
            elif self.tilemap.is_walkable_f(nx, p.y):
                p.x = nx
            elif self.tilemap.is_walkable_f(p.x, ny):
                p.y = ny

        # Spawner update
        self.spawner.update(dt, p, self.tilemap)

        # Combat projectiles
        self.combat.update(dt)

        # Particles
        self.particles.update(dt)

        # Camera
        self.camera.update(p.x, p.y)

        # Gate check
        self._gate_cooldown = max(0.0, self._gate_cooldown - dt)
        if self._gate_cooldown <= 0:
            gate = self.tilemap.get_gate_at(int(p.x), int(p.y))
            if gate:
                p.current_map = gate["to_map"]
                tx, ty = gate["to_pos"]
                p.x, p.y = float(tx), float(ty)
                self._load_map(gate["to_map"])
                self.hud.log(f"Đến {gate['to_map'].title()}",
                              color=(255, 215, 0))
                self.hud.notice(gate.get("label", gate["to_map"].upper()))

    # ── Draw ──────────────────────────────────────────────────────────────
    def _draw(self):
        state = self.states.current
        self.screen.fill(C_BG)

        if state == State.MAIN_MENU:
            self.main_menu.draw(self.screen)

        elif state == State.CHAR_CREATE:
            self.char_create.draw(self.screen)

        elif state in (State.PLAYING, State.INVENTORY,
                       State.LEVEL_UP, State.PAUSED, State.GAME_OVER):
            if self.tilemap and self.player:
                # World
                self.tilemap.draw(self.screen, self.camera)
                self.spawner.draw(self.screen, self.camera, self.font, ITEMS)
                self.combat.draw(self.screen, self.camera)
                self.player.draw(self.screen, self.camera, self.font)
                self._draw_npcs()
                self.particles.draw(self.screen, self.camera)
                # HUD
                self.hud.draw(self.screen, self.player, self.tilemap, self.camera)
                # Touch controls (luôn hiển thị khi PLAYING)
                self.touch.draw(self.screen)

            if state == State.INVENTORY:
                self.inv_panel.draw(self.screen, self.player)
            elif state == State.LEVEL_UP:
                self.stat_panel.draw(self.screen, self.player)
            elif state == State.PAUSED:
                self._draw_pause_overlay()
            elif state == State.GAME_OVER:
                self.gameover.draw(self.screen, self.player)

        pygame.display.flip()

    def _draw_npcs(self):
        for npc in self.tilemap.npcs:
            nx, ny = npc["pos"]
            sx, sy = self.camera.tile_to_screen(nx, ny)
            sx, sy = int(sx), int(sy)
            if -TILE_SIZE < sx < SCREEN_W and -TILE_SIZE < sy < SCREEN_H:
                pygame.draw.rect(self.screen, npc["color"],
                                  (sx + 4, sy + 4, TILE_SIZE - 8, TILE_SIZE - 8))
                pygame.draw.rect(self.screen, (255, 255, 200),
                                  (sx + 4, sy + 4, TILE_SIZE - 8, TILE_SIZE - 8), 1)
                t = self.font.render(npc["char"], True, (0, 0, 0))
                self.screen.blit(t, (sx + TILE_SIZE // 2 - t.get_width() // 2,
                                     sy + TILE_SIZE // 2 - t.get_height() // 2))
                nm = self.font.render(npc["name"], True, (255, 255, 180))
                self.screen.blit(nm, (sx + TILE_SIZE // 2 - nm.get_width() // 2,
                                      sy - 14))

    def _draw_pause_overlay(self):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        self.screen.blit(ov, (0, 0))
        font = pygame.font.SysFont("Arial", 36, bold=True)
        t = font.render("PAUSED  –  ESC tiếp tục", True, (255, 215, 0))
        self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2,
                              SCREEN_H // 2 - 20))
        hint_font = pygame.font.SysFont("Arial", 14)
        hints = [
            "WASD / ← ↑ ↓ → : di chuyển",
            "Click trái : di chuyển / tấn công",
            "Click phải : dùng skill đang chọn",
            "1-5 : chọn skill    Z : nhặt đồ",
            "H : potion HP    M : potion MP",
            "I : inventory    C : stats    F5 : lưu game",
        ]
        sy = SCREEN_H // 2 + 30
        for h in hints:
            ht = hint_font.render(h, True, (180, 180, 200))
            self.screen.blit(ht, (SCREEN_W // 2 - ht.get_width() // 2, sy))
            sy += 20


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
