"""
player_hud.py
=================
Top-left pixel-art status HUD: character portrait (carved wood frame
with peacock-crown motif), health bar (red), stamina/dash bar (blue),
and a bottom counter row (icon + number) — modeled after the
Pandava: Balance of Dharma reference mockup.

USAGE
-----
    from player_hud import PlayerHUD

    hud = PlayerHUD()

    # Once, after picking/loading a character (and again any time the
    # player switches character):
    hud.set_character(player_class_name)   # e.g. "Archer", "Assasin", ...

    # Every frame, in your draw section:
    hud.draw(screen, player.health, player.max_health,
              stamina_ratio, water_count)

PORTRAITS
---------
Fill in PORTRAIT_PATHS below with your own asset paths per character.
Until a path is set (or the file is missing), a pixel-art placeholder
silhouette is drawn instead so the HUD never crashes or shows blank.

STAMINA
-------
This HUD does not assume your BasePlayer tracks "stamina" as a single
0..1 value yet — dash in base_player.py currently uses dash_timer /
dash_cooldown instead. Pass whatever ratio (0.0 = empty, 1.0 = full)
makes sense for your dash-readiness; a ready-made helper
`stamina_ratio_from_dash(player)` is included below that derives one
from the existing dash_timer/dash_cooldown fields without needing any
changes to base_player.py.
"""

import pygame
import os


# ===================================================================
# CONFIG
# ===================================================================

HUD_X = 14          # top-left corner X
HUD_Y = 14          # top-left corner Y

PORTRAIT_SIZE   = 96    # portrait square size (px)
FRAME_BORDER    = 8     # wood frame border thickness (px)
BAR_WIDTH       = 230   # width of health/stamina bars
BAR_HEIGHT      = 15
BAR_GAP         = 6     # vertical gap between health bar and stamina bar
ROW_HEIGHT      = 46    # bottom counter row height
ICON_SIZE       = 50    # diperkecil dari 34, dan sekarang ditaruh di bawah stamina bar

# Fill these in with your own portrait file paths per character class
# name (player.__class__.__name__). Leave a value as None to use the
# pixel-art placeholder for that character until you have art ready.
PORTRAIT_PATHS = {
    "Archer":  "assets2/portraits/archer_portrait.png",
    "Spear":   "assets2/portraits/spear_portrait.png"
}

# Fill this in with your own pixelated water-drop icon path. Leave as
# None to use the built-in pixel-art placeholder.
WATER_ICON_PATH = "assets2/water_drop.png"



# ---- Palette (matches the wood/bronze/parchment look in the mockup) ----
WOOD_DARK     = (58,  38,  24)
WOOD_MID      = (92,  60,  36)
WOOD_LIGHT    = (140, 96,  56)
PANEL_BG      = (40,  28,  20)

HEALTH_BG     = (40,  20,  18)
HEALTH_FILL   = (176, 60,  46)
HEALTH_FILL_HI= (210, 90,  70)

STAMINA_BG    = (18,  28,  34)
STAMINA_FILL  = (96,  158, 176)
STAMINA_FILL_HI = (140, 196, 214)

TEXT_COLOR    = (245, 235, 205)
TEXT_SHADOW   = (24,  16,  10)

GOLD_MID      = (210, 160, 50)
GOLD_LIGHT    = (255, 215, 120)

SKIN_MID      = (200, 150, 110)
SKIN_DARK     = (150, 105, 75)
HAIR_DARK     = (35,  30,  45)


def _px_rect(surf, color, x, y, w, h, block):
    """Draw a rectangle snapped to a pixel-block grid for a chunky,
    non-antialiased look, matching the rest of the game's pixel-art style."""
    bx = (x // block) * block
    by = (y // block) * block
    bw = ((x + w - bx) // block + 1) * block
    bh = ((y + h - by) // block + 1) * block
    pygame.draw.rect(surf, color, (bx, by, bw, bh))


def _build_wood_frame(size, border, block=4):
    """Builds the carved-wood portrait frame with small corner finials,
    similar to the reference mockup's frame."""
    total = size + border * 2
    surf = pygame.Surface((total, total), pygame.SRCALPHA)

    # Outer dark wood
    pygame.draw.rect(surf, WOOD_DARK, (0, 0, total, total))
    # Mid wood border
    pygame.draw.rect(surf, WOOD_MID, (block, block, total - block * 2, total - block * 2))
    # Inner highlight sliver (top-left bevel)
    pygame.draw.rect(surf, WOOD_LIGHT, (block, block, total - block * 2, block))
    pygame.draw.rect(surf, WOOD_LIGHT, (block, block, block, total - block * 2))
    # Inner dark socket where the portrait image sits
    pygame.draw.rect(surf, PANEL_BG, (border, border, size, size))

    # Corner finials (small notches sticking out at the four corners,
    # echoing the carved wood posts in the reference image)
    fin = border
    pygame.draw.rect(surf, WOOD_DARK, (-fin // 2, -fin // 2, fin, fin))
    pygame.draw.rect(surf, WOOD_DARK, (total - fin // 2, -fin // 2, fin, fin))
    pygame.draw.rect(surf, WOOD_DARK, (-fin // 2, total - fin // 2, fin, fin))
    pygame.draw.rect(surf, WOOD_DARK, (total - fin // 2, total - fin // 2, fin, fin))

    return surf


def _build_placeholder_portrait(size):
    """Simple pixel-art silhouette bust used until real portrait art is
    wired up via PORTRAIT_PATHS. Avoids the HUD ever looking broken."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill(PANEL_BG)

    cx = size // 2
    # Hair/head silhouette
    pygame.draw.circle(surf, HAIR_DARK, (cx, size // 3), size // 3)
    # Face
    pygame.draw.circle(surf, SKIN_MID, (cx, int(size * 0.42)), int(size * 0.26))
    # Shoulders/body
    pygame.draw.rect(surf, HAIR_DARK, (size // 6, int(size * 0.62), size - size // 3, size - int(size * 0.62)))
    # Simple gold crown band as a nod to the reference art's headdress
    pygame.draw.rect(surf, GOLD_MID, (size // 4, int(size * 0.14), size // 2, size // 10))
    for i in range(3):
        gx = size // 4 + i * (size // 6)
        pygame.draw.circle(surf, GOLD_LIGHT, (gx + size // 12, int(size * 0.14)), max(2, size // 24))

    return surf


def _build_water_icon_placeholder(size, block=4):
    """Chunky pixel-art water droplet, used until a real icon path is
    supplied via WATER_ICON_PATH."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    drop_dark = (40, 110, 160)
    drop_mid  = (70, 150, 210)
    drop_hi   = (150, 210, 240)

    cx = size // 2
    # Build the droplet out of blocky pixel rows (wide at bottom, point at top)
    rows = [
        (0.30, 0.06), (0.36, 0.14), (0.42, 0.24), (0.46, 0.34),
        (0.48, 0.44), (0.48, 0.54), (0.46, 0.64), (0.40, 0.74),
        (0.30, 0.82),
    ]
    for half_w_frac, y_frac in rows:
        half_w = max(block, int(size * half_w_frac))
        y = int(size * y_frac)
        _px_rect(surf, drop_mid, cx - half_w, y, half_w * 2, block, block)

    # Outline (cheap approximation: redraw edges darker)
    pygame.draw.polygon(surf, drop_dark, [
        (cx, int(size * 0.04)),
        (int(size * 0.86), int(size * 0.58)),
        (cx, int(size * 0.92)),
        (int(size * 0.14), int(size * 0.58)),
    ], width=block)

    # Highlight
    pygame.draw.circle(surf, drop_hi, (int(size * 0.38), int(size * 0.5)), max(2, size // 10))

    return surf


def stamina_ratio_from_dash(player):
    """Derives a 0..1 'stamina' ratio from BasePlayer's existing
    dash_timer / dash_cooldown fields, without requiring any changes
    to base_player.py.

    - While dashing: ratio counts DOWN from 1.0 to 0.0 over dash_duration.
    - While on cooldown (dash_timer holds a negative value counting up
      to 0 in BasePlayer.input()): ratio counts back UP from 0.0 to 1.0.
    - Otherwise (fully ready): 1.0.
    """
    if getattr(player, "dashing", False):
        duration = max(1, getattr(player, "dash_duration", 1))
        timer = getattr(player, "dash_timer", 0)
        return max(0.0, min(1.0, timer / duration))

    timer = getattr(player, "dash_timer", 0)
    if timer < 0:
        cooldown = max(1, getattr(player, "dash_cooldown", 1))
        return max(0.0, min(1.0, 1.0 - (abs(timer) / cooldown)))

    return 1.0


class PlayerHUD:
    def __init__(self, font_path=None, font_size=18):
        self.x = HUD_X
        self.y = HUD_Y

        self.font = (pygame.font.Font(font_path, font_size)
                     if font_path else pygame.font.SysFont("monospace", font_size, bold=True))

        # ---- Pre-rendered static pieces (built once, cached) ----
        self._frame_sprite = _build_wood_frame(PORTRAIT_SIZE, FRAME_BORDER)
        self._placeholder_portrait = _build_placeholder_portrait(PORTRAIT_SIZE)

        self._portrait_cache = {}   # character_name -> loaded/scaled Surface
        self.current_character = None
        self._current_portrait = self._placeholder_portrait

        self._water_icon = self._load_water_icon()

    # -----------------------------------------------------------------
    def _load_water_icon(self):
        if WATER_ICON_PATH and os.path.isfile(WATER_ICON_PATH):
            try:
                img = pygame.image.load(WATER_ICON_PATH).convert_alpha()
                return pygame.transform.scale(img, (ICON_SIZE, ICON_SIZE))
            except pygame.error:
                pass
        return _build_water_icon_placeholder(ICON_SIZE)

    def _load_portrait(self, character_name):
        if character_name in self._portrait_cache:
            return self._portrait_cache[character_name]

        path = PORTRAIT_PATHS.get(character_name)

        # DEBUG — hapus print ini setelah masalah ketemu
        print(f"[HUD DEBUG] character_name={character_name!r}, path={path!r}, "
              f"exists={os.path.isfile(path) if path else 'N/A'}")

        surf = None
        if path and os.path.isfile(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                surf = pygame.transform.scale(img, (PORTRAIT_SIZE, PORTRAIT_SIZE))
                print(f"[HUD DEBUG] berhasil load gambar: {path}")
            except pygame.error as e:
                print(f"[HUD DEBUG] GAGAL load gambar: {e}")
                surf = None

        if surf is None:
            print(f"[HUD DEBUG] fallback ke placeholder untuk {character_name!r}")
            surf = self._placeholder_portrait

        self._portrait_cache[character_name] = surf
        return surf

    def set_character(self, character_name):
        """Call this once after the player object is created/changed
        (e.g. right after `broadcast_character(player)` in main.py) so
        the HUD shows the correct portrait."""
        self.current_character = character_name
        self._current_portrait = self._load_portrait(character_name)

    # -----------------------------------------------------------------
    def draw(self, surface, health, max_health, stamina_ratio, water_count):
        """
        health, max_health : current/max HP (health bar fill = health/max_health)
        stamina_ratio       : 0.0..1.0, fill amount for the blue bar
        water_count         : integer shown in the bottom counter row
        """
        x, y = self.x, self.y

        # ---- Portrait frame + image ----
        surface.blit(self._frame_sprite, (x, y))
        surface.blit(self._current_portrait, (x + FRAME_BORDER, y + FRAME_BORDER))

        frame_total = PORTRAIT_SIZE + FRAME_BORDER * 2
        bars_x = x + frame_total + 6
        bars_w = BAR_WIDTH

        # ---- Health bar (red) ----
        health_y = y
        self._draw_bar(surface, bars_x, health_y, bars_w, BAR_HEIGHT,
                        ratio=max(0.0, min(1.0, health / max_health if max_health else 0)),
                        bg_color=HEALTH_BG, fill_color=HEALTH_FILL, fill_hi=HEALTH_FILL_HI)

        # ---- Stamina bar (blue) ----
        stamina_y = health_y + BAR_HEIGHT + BAR_GAP
        self._draw_bar(surface, bars_x, stamina_y, bars_w, BAR_HEIGHT,
                        ratio=max(0.0, min(1.0, stamina_ratio)),
                        bg_color=STAMINA_BG, fill_color=STAMINA_FILL, fill_hi=STAMINA_FILL_HI)

        # ---- Water counter (icon + number), kecil, langsung di bawah stamina bar ----
        water_row_y = stamina_y + BAR_HEIGHT + BAR_GAP
        icon_x = bars_x
        icon_y = water_row_y
        surface.blit(self._water_icon, (icon_x, icon_y))

        count_text = str(water_count)
        text_surf = self.font.render(count_text, True, TEXT_COLOR)
        shadow_surf = self.font.render(count_text, True, TEXT_SHADOW)
        text_x = icon_x + ICON_SIZE + 8
        text_y = icon_y + (ICON_SIZE - text_surf.get_height()) // 2
        surface.blit(shadow_surf, (text_x + 2, text_y + 2))
        surface.blit(text_surf, (text_x, text_y))

    def _draw_bar(self, surface, x, y, w, h, ratio, bg_color, fill_color, fill_hi):
        # Background track
        pygame.draw.rect(surface, bg_color, (x, y, w, h))
        # Fill
        fill_w = int(w * ratio)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, (x, y, fill_w, h))
            # Thin brighter highlight line along the top of the fill
            pygame.draw.rect(surface, fill_hi, (x, y, fill_w, max(2, h // 6)))
        # Border
        pygame.draw.rect(surface, WOOD_DARK, (x, y, w, h), 3)