import pygame
import math


# ===================================================================
# CONFIG — tweak sizes/positions/colors here
# ===================================================================

PIXEL_SCALE = 4   # how chunky each "pixel" block is when upscaled

JOYSTICK_RADIUS_OUTER = 72      # outer ring radius (px, final on-screen size)
JOYSTICK_RADIUS_INNER = 30      # draggable knob radius (px, final on-screen size)
JOYSTICK_MARGIN       = 112     # distance from left/bottom edge
JOYSTICK_DEADZONE     = 0.12    # 0..1, fraction of outer radius to ignore

BUTTON_RADIUS         = 44      # action button radius (px, final on-screen size)
BUTTON_MARGIN_X       = 110     # distance from right edge
BUTTON_MARGIN_Y       = 120     # distance from bottom edge
BUTTON_GAP            = 108     # vertical gap between ATK/DASH buttons

FONT_SIZE = 16

# ---- Pause button (top-center, UI only — not gameplay input) ----
PAUSE_BTN_SIZE   = 48   # width and height of the square button (px)
PAUSE_BTN_MARGIN = 14   # distance from top edge

# ---- Stone / bronze relic palette (matches GOLD/ORANGE/RED in main.py) ----
STONE_DARK    = (46,  38,  30)     # deep basalt shadow
STONE_MID     = (78,  64,  48)     # weathered stone body
STONE_LIGHT   = (120, 100, 74)     # stone highlight
OUTLINE_BLACK = (18,  14,  10)

GOLD_DARK   = (150, 105, 30)
GOLD_MID    = (210, 160, 50)
GOLD_LIGHT  = (255, 210, 110)

EMBER_DARK  = (130, 40,  30)   # attack accent (matches RED/ORANGE)
EMBER_MID   = (200, 70,  45)
EMBER_LIGHT = (255, 140, 90)

SKY_DARK    = (35,  70,  110)  # dash accent (matches BLUE)
SKY_MID     = (60,  120, 190)
SKY_LIGHT   = (140, 200, 255)

TEXT_COLOR  = (245, 230, 195)
TEXT_SHADOW = (30,  22,  16)


def _px_circle(surf, color, cx, cy, r, scale):
    """Draw a circle made of chunky square 'pixels' instead of a smooth
    anti-aliased circle — the core trick for the pixel-art look."""
    r_blocks = max(1, r // scale)
    for by in range(-r_blocks, r_blocks + 1):
        for bx in range(-r_blocks, r_blocks + 1):
            # distance check in block-space approximates a circle while
            # keeping a blocky stepped edge
            if bx * bx + by * by <= r_blocks * r_blocks:
                px = cx + bx * scale - scale // 2
                py = cy + by * scale - scale // 2
                pygame.draw.rect(surf, color, (px, py, scale, scale))


def _px_ring(surf, color, cx, cy, r_outer, r_inner, scale):
    """Chunky pixel ring (annulus) — used for the joystick base and
    button border to give a carved-stone notch look."""
    r_out_blocks = max(1, r_outer // scale)
    r_in_blocks = max(0, r_inner // scale)
    for by in range(-r_out_blocks, r_out_blocks + 1):
        for bx in range(-r_out_blocks, r_out_blocks + 1):
            dist_sq = bx * bx + by * by
            if r_in_blocks * r_in_blocks <= dist_sq <= r_out_blocks * r_out_blocks:
                px = cx + bx * scale - scale // 2
                py = cy + by * scale - scale // 2
                pygame.draw.rect(surf, color, (px, py, scale, scale))


def _build_joystick_base(radius, scale, font):
    """Pre-render the static joystick base (outer ring) once."""
    size = radius * 2 + scale * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    # Outer black outline ring
    _px_ring(surf, OUTLINE_BLACK, cx, cy, radius + scale, radius - scale * 3, scale)
    # Stone body
    _px_ring(surf, STONE_MID, cx, cy, radius, radius - scale * 3, scale)
    # Inner shadow notch (carved look)
    _px_ring(surf, STONE_DARK, cx, cy, radius - scale, radius - scale * 2, scale)
    # Top-left highlight sliver for a beveled feel
    _px_ring(surf, STONE_LIGHT, cx, cy, radius - scale * 2, radius - scale * 3, scale)

    # Four corner "rivets" (small gold pixel dots) — Pandava relic motif
    rivet_r = scale
    offset = radius - scale * 2
    for ang in (45, 135, 225, 315):
        rx = cx + int(offset * math.cos(math.radians(ang)))
        ry = cy + int(offset * math.sin(math.radians(ang)))
        _px_circle(surf, GOLD_MID, rx, ry, rivet_r, scale)

    return surf


def _build_joystick_knob(radius, scale, active):
    size = radius * 2 + scale * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    body = GOLD_LIGHT if active else GOLD_MID
    edge = GOLD_DARK if active else STONE_DARK

    _px_circle(surf, OUTLINE_BLACK, cx, cy, radius + scale, scale)
    _px_circle(surf, edge, cx, cy, radius, scale)
    _px_circle(surf, body, cx, cy, radius - scale, scale)
    # small highlight in upper-left for a faceted-gem look
    _px_circle(surf, GOLD_LIGHT if not active else (255, 240, 200),
               cx - radius // 3, cy - radius // 3, max(scale, radius // 3), scale)

    return surf


def _build_button(radius, scale, label, font, pressed, mid_color, light_color, dark_color):
    size = radius * 2 + scale * 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    body = light_color if pressed else mid_color
    edge = dark_color

    # Outer black pixel outline
    _px_circle(surf, OUTLINE_BLACK, cx, cy, radius + scale, scale)
    # Stone/bronze rim
    _px_ring(surf, edge, cx, cy, radius, radius - scale * 2, scale)
    # Inner face
    _px_circle(surf, body, cx, cy, radius - scale * 2, scale)
    # Top-left bevel highlight
    _px_ring(surf, STONE_LIGHT if not pressed else light_color,
              cx, cy, radius - scale * 2, radius - scale * 3, scale)

    # Label — drawn with a 1px(-block) drop shadow for readability
    text = font.render(label, True, TEXT_COLOR)
    shadow = font.render(label, True, TEXT_SHADOW)
    tw, th = text.get_size()
    surf.blit(shadow, (cx - tw // 2 + scale // 2, cy - th // 2 + scale // 2))
    surf.blit(text, (cx - tw // 2, cy - th // 2))

    return surf


def _build_pause_button(size, pressed):
    """Pre-render the pause button square — placeholder style (grey square, Arial 'P').
    To replace with your own asset later: load your image with
    pygame.image.load(...).convert_alpha(), scale to (size, size), and return it
    instead of building this surface. Make a pressed variant by darkening with
    surf.fill((0,0,0,60), special_flags=pygame.BLEND_RGBA_MULT)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    body   = (180, 180, 180) if pressed else (100, 100, 100)
    border = (40,  40,  40)
    pygame.draw.rect(surf, border, (0, 0, size, size),             border_radius=6)
    pygame.draw.rect(surf, body,   (2, 2, size - 4, size - 4),    border_radius=5)
    font  = pygame.font.SysFont("arial", size // 2, bold=True)
    label = font.render("P", True, (20, 20, 20))
    surf.blit(label, (size // 2 - label.get_width()  // 2,
                      size // 2 - label.get_height() // 2))
    return surf


class MobileControls:
    def __init__(self, width, height, font=None):
        self.width = width
        self.height = height
        self.visible = True
        self.scale = PIXEL_SCALE

        self.font = font or pygame.font.SysFont("monospace", FONT_SIZE, bold=True)

        # ---- Joystick geometry ----
        self.joy_center = (JOYSTICK_MARGIN, height - JOYSTICK_MARGIN)
        self.joy_knob_pos = list(self.joy_center)
        self.joy_touch_id = None
        self.joy_active = False

        # ---- Buttons geometry ----
        self.btn_attack_center = (
            width - BUTTON_MARGIN_X,
            height - BUTTON_MARGIN_Y - BUTTON_GAP
        )
        self.btn_dash_center = (
            width - BUTTON_MARGIN_X,
            height - BUTTON_MARGIN_Y
        )
        self.btn_attack_pressed = False
        self.btn_dash_pressed = False
        self.btn_attack_touch_id = None
        self.btn_dash_touch_id = None

        # ---- PUBLIC STATE — read these directly in base_player.py ----
        self.move_up    = False
        self.move_down  = False
        self.move_left  = False
        self.move_right = False
        self.attack     = False
        self.dash       = False

        self.joy_vec = (0.0, 0.0)

        # ---- Pre-rendered pixel art sprites (cached, rebuilt on state change) ----
        self._joy_base_sprite = _build_joystick_base(JOYSTICK_RADIUS_OUTER, self.scale, self.font)
        self._joy_knob_sprite_idle = _build_joystick_knob(JOYSTICK_RADIUS_INNER, self.scale, False)
        self._joy_knob_sprite_active = _build_joystick_knob(JOYSTICK_RADIUS_INNER, self.scale, True)

        self._btn_attack_sprite_idle = _build_button(
            BUTTON_RADIUS, self.scale, "ATK", self.font, False,
            EMBER_MID, EMBER_LIGHT, EMBER_DARK
        )
        self._btn_attack_sprite_pressed = _build_button(
            BUTTON_RADIUS, self.scale, "ATK", self.font, True,
            EMBER_MID, EMBER_LIGHT, EMBER_DARK
        )
        self._btn_dash_sprite_idle = _build_button(
            BUTTON_RADIUS, self.scale, "DASH", self.font, False,
            SKY_MID, SKY_LIGHT, SKY_DARK
        )
        self._btn_dash_sprite_pressed = _build_button(
            BUTTON_RADIUS, self.scale, "DASH", self.font, True,
            SKY_MID, SKY_LIGHT, SKY_DARK
        )

        # ---- Pause button (UI only — not gameplay input) ----
        # Positioned top-center. Only shown during gameplay via draw(show_pause=True).
        self.btn_pause_center   = (width // 2, PAUSE_BTN_MARGIN + PAUSE_BTN_SIZE // 2)
        self.btn_pause_pressed  = False
        self.btn_pause_touch_id = None
        # One-shot flag: set True when pressed, game_loop reads it then resets to False.
        self.pause_just_pressed = False

        self._btn_pause_idle    = _build_pause_button(PAUSE_BTN_SIZE, False)
        self._btn_pause_active  = _build_pause_button(PAUSE_BTN_SIZE, True)

    # ---------------------------------------------------------------
    # EVENT HANDLING
    # ---------------------------------------------------------------
    def handle_event(self, event):
        """Call this for every event in your pygame.event.get() loop."""
        if not self.visible:
            return

        if event.type == pygame.FINGERDOWN:
            pos = self._finger_to_px(event)
            self._on_press(pos, touch_id=event.finger_id)

        elif event.type == pygame.FINGERMOTION:
            pos = self._finger_to_px(event)
            self._on_drag(pos, touch_id=event.finger_id)

        elif event.type == pygame.FINGERUP:
            self._on_release(touch_id=event.finger_id)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._on_press(event.pos, touch_id="mouse")

        elif event.type == pygame.MOUSEMOTION:
            if self.joy_touch_id == "mouse" or self.btn_attack_touch_id == "mouse" \
               or self.btn_dash_touch_id == "mouse":
                self._on_drag(event.pos, touch_id="mouse")

        elif event.type == pygame.MOUSEBUTTONUP:
            self._on_release(touch_id="mouse")

    def _finger_to_px(self, event):
        return (event.x * self.width, event.y * self.height)

    def _dist(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _on_press(self, pos, touch_id):
        if self._dist(pos, self.joy_center) <= JOYSTICK_RADIUS_OUTER * 1.4 and self.joy_touch_id is None:
            self.joy_touch_id = touch_id
            self.joy_active = True
            self._update_joystick(pos)
            return

        if self._dist(pos, self.btn_attack_center) <= BUTTON_RADIUS * 1.3 and self.btn_attack_touch_id is None:
            self.btn_attack_touch_id = touch_id
            self.btn_attack_pressed = True
            self.attack = True
            return

        if self._dist(pos, self.btn_dash_center) <= BUTTON_RADIUS * 1.3 and self.btn_dash_touch_id is None:
            self.btn_dash_touch_id = touch_id
            self.btn_dash_pressed = True
            self.dash = True
            return

        if self._dist(pos, self.btn_pause_center) <= PAUSE_BTN_SIZE * 0.8 \
                and self.btn_pause_touch_id is None:
            self.btn_pause_touch_id = touch_id
            self.btn_pause_pressed  = True
            self.pause_just_pressed = True
            return

    def _on_drag(self, pos, touch_id):
        if touch_id == self.joy_touch_id:
            self._update_joystick(pos)

    def _on_release(self, touch_id):
        if touch_id == self.joy_touch_id:
            self.joy_touch_id = None
            self.joy_active = False
            self.joy_knob_pos = list(self.joy_center)
            self.joy_vec = (0.0, 0.0)
            self.move_up = self.move_down = self.move_left = self.move_right = False

        if touch_id == self.btn_attack_touch_id:
            self.btn_attack_touch_id = None
            self.btn_attack_pressed = False
            self.attack = False

        if touch_id == self.btn_dash_touch_id:
            self.btn_dash_touch_id = None
            self.btn_dash_pressed = False
            self.dash = False

        if touch_id == self.btn_pause_touch_id:
            self.btn_pause_touch_id = None
            self.btn_pause_pressed  = False

    # ---------------------------------------------------------------
    # JOYSTICK MATH
    # ---------------------------------------------------------------
    def _update_joystick(self, pos):
        cx, cy = self.joy_center
        dx = pos[0] - cx
        dy = pos[1] - cy
        dist = math.hypot(dx, dy)

        max_dist = JOYSTICK_RADIUS_OUTER
        clamped = min(dist, max_dist)

        if dist > 0:
            nx, ny = dx / dist, dy / dist
        else:
            nx, ny = 0, 0

        self.joy_knob_pos = [cx + nx * clamped, cy + ny * clamped]

        norm = clamped / max_dist if max_dist else 0
        self.joy_vec = (nx * norm, ny * norm)

        if norm < JOYSTICK_DEADZONE:
            self.move_up = self.move_down = self.move_left = self.move_right = False
            return

        # Per-axis thresholding instead of angle bands — avoids the
        # "wrong direction until release" glitch caused by small
        # vertical jitter while dragging mostly horizontally (and vice versa).
        ax = nx * norm   # signed normalized x (-1..1)
        ay = ny * norm   # signed normalized y (-1..1)

        axis_dead = JOYSTICK_DEADZONE * 0.6  # smaller per-axis threshold

        self.move_right = ax > axis_dead
        self.move_left  = ax < -axis_dead
        self.move_down  = ay > axis_dead
        self.move_up    = ay < -axis_dead
    # ---------------------------------------------------------------
    # PER-FRAME UPDATE
    # ---------------------------------------------------------------
    def update(self):
        """Placeholder kept for API symmetry. Safe to call every frame."""
        pass

    # ---------------------------------------------------------------
    # DRAWING — blits pre-rendered pixel-art sprites, no per-frame
    # circle math, so this is cheap even on low-end mobile hardware.
    # ---------------------------------------------------------------
    def draw(self, surface, show_pause=False):
        """Draw the mobile controls.

        show_pause=True  → draw joystick + ATK + DASH + pause button (in-game HUD)
        show_pause=False → draw nothing (main menu / character select screens)

        To replace the pause button placeholder later: swap out self._btn_pause_idle
        and self._btn_pause_active with your own pre-loaded/scaled pygame.Surface
        objects in __init__, then _build_pause_button() is no longer called.
        """
        if not self.visible:
            return

        if not show_pause:
            return

        # Joystick base (static)
        base = self._joy_base_sprite
        surface.blit(base, (self.joy_center[0] - base.get_width() // 2,
                             self.joy_center[1] - base.get_height() // 2))

        # Joystick knob (follows finger)
        knob = self._joy_knob_sprite_active if self.joy_active else self._joy_knob_sprite_idle
        kx, ky = self.joy_knob_pos
        surface.blit(knob, (kx - knob.get_width() // 2, ky - knob.get_height() // 2))

        # Attack button
        atk = self._btn_attack_sprite_pressed if self.btn_attack_pressed else self._btn_attack_sprite_idle
        ax, ay = self.btn_attack_center
        surface.blit(atk, (ax - atk.get_width() // 2, ay - atk.get_height() // 2))

        # Dash button
        dash = self._btn_dash_sprite_pressed if self.btn_dash_pressed else self._btn_dash_sprite_idle
        dxp, dyp = self.btn_dash_center
        surface.blit(dash, (dxp - dash.get_width() // 2, dyp - dash.get_height() // 2))

        # Pause button (top-center)
        pause_spr = self._btn_pause_active if self.btn_pause_pressed else self._btn_pause_idle
        px, py = self.btn_pause_center
        surface.blit(pause_spr, (px - PAUSE_BTN_SIZE // 2, py - PAUSE_BTN_SIZE // 2))

    # ---------------------------------------------------------------
    # RESIZE SUPPORT
    # ---------------------------------------------------------------
    def resize(self, width, height):
        self.width = width
        self.height = height
        self.joy_center = (JOYSTICK_MARGIN, height - JOYSTICK_MARGIN)
        self.joy_knob_pos = list(self.joy_center)
        self.btn_attack_center = (width - BUTTON_MARGIN_X, height - BUTTON_MARGIN_Y - BUTTON_GAP)
        self.btn_dash_center   = (width - BUTTON_MARGIN_X, height - BUTTON_MARGIN_Y)
        self.btn_pause_center  = (width // 2, PAUSE_BTN_MARGIN + PAUSE_BTN_SIZE // 2)