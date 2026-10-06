"""
touch_controls.py - Virtual joystick và nút cảm ứng cho Android/màn hình touch
"""
import pygame
import math


class VirtualJoystick:
    """
    Joystick ảo góc trái dưới màn hình.
    Trả về (dx, dy) normalized [-1, 1].
    """
    def __init__(self, x, y, radius=60):
        self.cx      = x        # tâm joystick
        self.cy      = y
        self.radius  = radius   # bán kính vùng kéo
        self.knob_r  = radius // 3
        self.knob_x  = float(x)
        self.knob_y  = float(y)
        self.active  = False
        self.touch_id = None
        self.dx      = 0.0
        self.dy      = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.FINGERDOWN:
            # Kiểm tra chạm vào vùng joystick
            fx = event.x * pygame.display.get_surface().get_width()
            fy = event.y * pygame.display.get_surface().get_height()
            if math.dist((fx, fy), (self.cx, self.cy)) <= self.radius * 1.5:
                self.active   = True
                self.touch_id = event.finger_id
                self._update_knob(fx, fy)

        elif event.type == pygame.FINGERMOTION:
            if event.finger_id == self.touch_id:
                fx = event.x * pygame.display.get_surface().get_width()
                fy = event.y * pygame.display.get_surface().get_height()
                self._update_knob(fx, fy)

        elif event.type == pygame.FINGERUP:
            if event.finger_id == self.touch_id:
                self.active   = False
                self.touch_id = None
                self.knob_x   = float(self.cx)
                self.knob_y   = float(self.cy)
                self.dx = 0.0
                self.dy = 0.0

        # Cũng hỗ trợ mouse (test trên PC)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if math.dist((mx, my), (self.cx, self.cy)) <= self.radius * 1.5:
                self.active = True
                self._update_knob(mx, my)
        elif event.type == pygame.MOUSEMOTION:
            if self.active and pygame.mouse.get_pressed()[0]:
                self._update_knob(*event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active:
                self.active = False
                self.knob_x = float(self.cx)
                self.knob_y = float(self.cy)
                self.dx = 0.0
                self.dy = 0.0

    def _update_knob(self, fx, fy):
        dx = fx - self.cx
        dy = fy - self.cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > self.radius:
            dx = dx / dist * self.radius
            dy = dy / dist * self.radius
        self.knob_x = self.cx + dx
        self.knob_y = self.cy + dy
        self.dx = dx / self.radius
        self.dy = dy / self.radius

    def get_direction(self):
        """Trả về (dx, dy) normalized."""
        return self.dx, self.dy

    def draw(self, screen: pygame.Surface):
        # Vùng ngoài
        pygame.draw.circle(screen, (80, 80, 100, 120),
                           (self.cx, self.cy), self.radius, 2)
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (50, 50, 70, 100),
                           (self.radius, self.radius), self.radius)
        screen.blit(s, (self.cx - self.radius, self.cy - self.radius))
        # Knob
        knob_color = (150, 150, 200, 180) if not self.active else (200, 200, 255, 220)
        ks = pygame.Surface((self.knob_r * 2, self.knob_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ks, (*knob_color[:3], knob_color[3] if len(knob_color) > 3 else 180),
                           (self.knob_r, self.knob_r), self.knob_r)
        screen.blit(ks, (int(self.knob_x) - self.knob_r,
                         int(self.knob_y) - self.knob_r))
        pygame.draw.circle(screen, (180, 180, 220),
                           (int(self.knob_x), int(self.knob_y)),
                           self.knob_r, 2)


class TouchButton:
    """
    Nút cảm ứng tròn.
    """
    def __init__(self, x, y, radius, label, color=(80, 80, 160), action=None):
        self.cx      = x
        self.cy      = y
        self.radius  = radius
        self.label   = label
        self.color   = color
        self.action  = action
        self.pressed = False
        self._font   = None

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", max(10, self.radius // 2), bold=True)
        return self._font

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Trả về True nếu vừa được nhấn."""
        hit = False
        if event.type == pygame.FINGERDOWN:
            fx = event.x * pygame.display.get_surface().get_width()
            fy = event.y * pygame.display.get_surface().get_height()
            if math.dist((fx, fy), (self.cx, self.cy)) <= self.radius:
                self.pressed = True
                hit = True
        elif event.type == pygame.FINGERUP:
            self.pressed = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if math.dist(event.pos, (self.cx, self.cy)) <= self.radius:
                self.pressed = True
                hit = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False

        return hit

    def draw(self, screen: pygame.Surface):
        alpha = 220 if self.pressed else 160
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        c = (*self.color, alpha)
        pygame.draw.circle(s, c, (self.radius, self.radius), self.radius)
        screen.blit(s, (self.cx - self.radius, self.cy - self.radius))
        pygame.draw.circle(screen, (200, 200, 255),
                           (self.cx, self.cy), self.radius,
                           3 if self.pressed else 1)
        font = self._get_font()
        t = font.render(self.label, True, (255, 255, 255))
        screen.blit(t, (self.cx - t.get_width() // 2,
                        self.cy - t.get_height() // 2))


class TouchControlsOverlay:
    """
    Bộ controls đầy đủ cho màn hình cảm ứng:
    - Joystick trái: di chuyển
    - Nút A: tấn công / tương tác
    - Nút S1-S3: skill 2,3,4
    - Nút I: inventory
    - Nút Z: nhặt đồ
    - Nút H: potion HP
    """

    def __init__(self, screen_w: int, screen_h: int):
        self.sw = screen_w
        self.sh = screen_h
        self.visible = True

        # Joystick góc trái dưới
        self.joystick = VirtualJoystick(
            x=screen_w * 0.12,
            y=screen_h * 0.80,
            radius=int(screen_h * 0.10)
        )

        r  = int(screen_h * 0.065)   # bán kính nút
        r2 = int(screen_h * 0.050)   # nút nhỏ hơn

        # Nút tấn công (góc phải dưới)
        self.btn_attack = TouchButton(
            int(screen_w * 0.88), int(screen_h * 0.80),
            r, "ATK", color=(180, 50, 50), action="attack"
        )

        # Skill 2, 3, 4 — hàng trên nút ATK
        self.btn_sk2 = TouchButton(
            int(screen_w * 0.76), int(screen_h * 0.72),
            r2, "SK2", color=(80, 80, 180), action="skill_2"
        )
        self.btn_sk3 = TouchButton(
            int(screen_w * 0.88), int(screen_h * 0.65),
            r2, "SK3", color=(80, 150, 80), action="skill_3"
        )
        self.btn_sk4 = TouchButton(
            int(screen_w * 0.76), int(screen_h * 0.58),
            r2, "SK4", color=(150, 80, 150), action="skill_4"
        )

        # Nút phụ (hàng trên)
        self.btn_pickup = TouchButton(
            int(screen_w * 0.88), int(screen_h * 0.52),
            r2, "Z", color=(80, 130, 80), action="pickup"
        )
        self.btn_hp = TouchButton(
            int(screen_w * 0.78), int(screen_h * 0.42),
            r2, "HP", color=(180, 50, 50), action="heal"
        )
        self.btn_inv = TouchButton(
            int(screen_w * 0.93), int(screen_h * 0.42),
            r2, "INV", color=(100, 100, 50), action="inventory"
        )

        self._all_buttons = [
            self.btn_attack,
            self.btn_sk2, self.btn_sk3, self.btn_sk4,
            self.btn_pickup, self.btn_hp, self.btn_inv,
        ]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Xử lý touch event.
        Trả về action string nếu nút được nhấn, None nếu không.
        """
        self.joystick.handle_event(event)
        for btn in self._all_buttons:
            if btn.handle_event(event):
                return btn.action
        return None

    def get_move_vector(self):
        """Trả về (dx, dy) từ joystick."""
        return self.joystick.get_direction()

    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return
        self.joystick.draw(screen)
        for btn in self._all_buttons:
            btn.draw(screen)
