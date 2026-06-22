import pygame
import random
import sys
from player.mage import Mage
from player.assasin import Assasin
from player.satyr import Satyr
from player.archer import Archer
from player.spear import Spear
from player.arrow import Arrow
from player.hammer import Hammer
from enemy1 import Enemy
from enemy2 import Enemy2
from mobile_controls import MobileControls, PAUSE_BTN_SIZE
from character_registry import broadcast_character
from dialog_system import DialogBox, RESI_DIALOG_TREE
pygame.init() 

# ================= WINDOW =================
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("Pandava: Balance of Dharma")
clock = pygame.time.Clock()

# Virtual joystick + attack/dash buttons for mobile.
# Set mobile_controls.visible = False to hide on desktop builds.
mobile_controls = MobileControls(WIDTH, HEIGHT)
dialog_box = DialogBox(WIDTH, HEIGHT)
FPS = 60

# ================= LOAD ASSETS =================
bg_menu = pygame.image.load("assets2/main_menu2.jpeg").convert()
bg_menu = pygame.transform.scale(bg_menu, (WIDTH, HEIGHT))

card_yudhistira = pygame.image.load("assets2/yudhistira_card.jpeg").convert_alpha()
card_arjuna     = pygame.image.load("assets2/arjuna_card.png").convert_alpha()
card_bima       = pygame.image.load("assets2/bima_card.png").convert_alpha()
card_yudhistira = pygame.transform.scale(card_yudhistira, (300, 400))
card_arjuna     = pygame.transform.scale(card_arjuna,     (300, 400))
card_bima       = pygame.transform.scale(card_bima,       (300, 400))

relic_arjuna    = pygame.image.load("assets2/relic1.png").convert_alpha()
relic_arjuna    = pygame.transform.scale(relic_arjuna, (25, 25))
relic_bima      = pygame.image.load("assets2/relic2.png").convert_alpha()
relic_bima      = pygame.transform.scale(relic_bima, (25, 25))
relic_yudhistira = pygame.image.load("assets2/relic3.png").convert_alpha()
relic_yudhistira = pygame.transform.scale(relic_yudhistira, (25, 25))
relic_sadewa    = pygame.image.load("assets2/relic4.png").convert_alpha()
relic_sadewa    = pygame.transform.scale(relic_sadewa, (25, 25))
relic_nakula    = pygame.image.load("assets2/relic5.png").convert_alpha()
relic_nakula    = pygame.transform.scale(relic_nakula, (25, 25))
portal_resi     = pygame.image.load("assets2/portal_resi.png").convert_alpha()
portal_resi     = pygame.transform.scale(portal_resi, (300, 300))

bg_map1 = pygame.image.load("assets2/background7.jpeg").convert()
bg_map1 = pygame.transform.scale(bg_map1, (WIDTH, HEIGHT))
bg_map2 = pygame.image.load("assets2/background8.jpeg").convert()
bg_map2 = pygame.transform.scale(bg_map2, (WIDTH, HEIGHT))
bg_map3 = pygame.image.load("assets2/background9.jpeg").convert()
bg_map3 = pygame.transform.scale(bg_map3, (WIDTH, HEIGHT))
bg_map4 = pygame.image.load("assets2/background10.png").convert()
bg_map4 = pygame.transform.scale(bg_map4, (WIDTH, HEIGHT))
bg_map5 = pygame.image.load("assets2/background11.png").convert()
bg_map5 = pygame.transform.scale(bg_map5, (WIDTH, HEIGHT))

bg_game    = bg_map1
current_bg = 1

pixel_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 36)
btn_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 80)
hud_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 24)
small_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 20)

arrows = pygame.sprite.Group()

# ================= COLORS =================
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
DARK   = (20,  20,  20)
GREEN  = (80,  220, 140)
RED    = (220, 60,  60)
ORANGE = (255, 160, 40)
GOLD   = (255, 210, 60)
BLUE   = (80,  160, 255)
PURPLE = (180, 80,  255)

# ================= TIMER DURATIONS (seconds) =================
LOBBY_DURATION   = 5
EXPLORE_DURATION = 60

# ================= PHASE STATE =================
phase         = "lobby"
phase_frames  = LOBBY_DURATION * FPS

# ================= STATE =================
state          = "menu"
selected_class = Archer
SPAWN_POS      = (400, 300)

# ================= PLAYER =================
player  = Archer(400, 300)
player.mobile_controls = mobile_controls
players = pygame.sprite.Group(player)
broadcast_character(player)

# ================= ENEMIES =================
enemy               = Enemy(100, 300)
enemies             = pygame.sprite.Group(enemy)
enemy_spawn_pos     = (700, 300)
enemy_respawn_timer = 0
RESPAWN_DELAY       = 120

# ================= INTERACTION ZONES =================
portal_zones_map1 = [
    pygame.Rect(420, 140, 25, 25),
    pygame.Rect(770, 170, 25, 25)
]

BG2_SPAWN_POS = (600, 150)

portal_zones_map2 = [
    pygame.Rect(450, 450, 25, 25)
]

portal_zones_map4_entry = [
    pygame.Rect(152, 296, 25, 25)
]

BG3_SPAWN_POS     = (164, 106)
portal_zones_map3 = [
    pygame.Rect(BG3_SPAWN_POS[0] - 12, BG3_SPAWN_POS[1] - 12, 25, 25)
]

BG4_SPAWN_POS     = (400, 150)
portal_zones_map4 = [
    pygame.Rect(582, 76, 25, 30)
]

BG5_SPAWN_POS           = (546, 56)
portal_zones_map5_entry = [
    pygame.Rect(494, 110, 25, 25)
]
portal_zones_map5 = [
    pygame.Rect(BG5_SPAWN_POS[0] - 12, BG5_SPAWN_POS[1] - 12, 25, 25)
]

# ================= RELIC SYSTEM =================
RELIC_POSITIONS = {
    3: [(200, 200), (350, 300), (150, 400), (480, 250), (300, 150)],
    4: [(200, 200), (500, 300), (300, 400), (420, 180), (150, 300)],
    5: [(300, 200), (450, 350), (200, 300), (500, 200), (350, 400)],
}

# Pasangkan nama dengan image-nya
RELIC_OPTIONS = [
    {"name": "Batu Arjuna",     "img": relic_arjuna},
    {"name": "Batu Bima",       "img": relic_bima},
    {"name": "Batu Yudhistira", "img": relic_yudhistira},
    {"name": "Batu Sadewa",     "img": relic_sadewa},
    {"name": "Batu Nakula",     "img": relic_nakula},
    {"name": "Portal Resi",     "img": portal_resi},
]


def generate_relic():
    relic_map    = random.choice([3, 4, 5])
    relic_pos    = random.choice(RELIC_POSITIONS[relic_map])
    relic_option = random.choice(RELIC_OPTIONS)
    return {
        "map":       relic_map,
        "pos":       relic_pos,
        "name":      relic_option["name"],
        "img":       relic_option["img"],
        "collected": False,
        "rect":      pygame.Rect(relic_pos[0] - 50, relic_pos[1] - 50, 100, 100),
    }


relic       = generate_relic()
relic_pulse = 0
relic_notif_timer = 0
print(f"[RELIC] '{relic['name']}' muncul di Map {relic['map']} posisi {relic['pos']}")

# ================= RELIC DRAW =================
def draw_relic():
    global relic_pulse
    if relic["collected"] or relic["map"] != current_bg:
        return

    relic_pulse = (relic_pulse + 3) % 360

    x, y = relic["pos"]


    # Gambar sprite relic
    screen.blit(relic["img"], relic["img"].get_rect(center=(x, y)))

def draw_relic_prompt():
    """Tampilkan 'Press E' di atas relic jika player dekat."""
    if relic["collected"] or relic["map"] != current_bg:
        return False
    pickup_range = pygame.Rect(relic["pos"][0] - 60, relic["pos"][1] - 60, 120, 120)
    if player.rect.colliderect(pickup_range):
        label = small_font.render(f"Press E — {relic['name']}", True, GOLD)
        screen.blit(label, (
            relic["pos"][0] - label.get_width() // 2,
            relic["pos"][1] - 70
        ))
        return True
    return False

def draw_relic_notif():
    global relic_notif_timer
    if relic_notif_timer <= 0:
        return
    alpha = min(255, relic_notif_timer * 8)
    notif = pixel_font.render(f"✦ {relic['name']} ditemukan! ✦", True, GOLD)
    notif.set_alpha(alpha)
    screen.blit(notif, (WIDTH // 2 - notif.get_width() // 2, HEIGHT // 2 - 40))
    relic_notif_timer -= 1

# ================= HUD HELPERS =================
def lerp_color(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )

def draw_timer_panel():
    panel_w, panel_h = 220, 80
    panel_x = WIDTH - panel_w - 10
    panel_y = 10

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surf.fill((10, 10, 10, 170))
    screen.blit(panel_surf, (panel_x, panel_y))
    pygame.draw.rect(screen, (80, 80, 80), (panel_x, panel_y, panel_w, panel_h), 1)

    secs_left  = phase_frames // FPS
    total_secs = LOBBY_DURATION if phase == "lobby" else EXPLORE_DURATION
    ratio      = phase_frames / (total_secs * FPS)

    if ratio > 0.5:
        bar_color = lerp_color(ORANGE, GREEN, (ratio - 0.5) * 2)
    else:
        bar_color = lerp_color(RED, ORANGE, ratio * 2)

    if phase == "lobby":
        label_text  = "⚔  FIGHT PHASE"
        label_color = RED
    else:
        label_text  = "✦  EXPLORE PHASE"
        label_color = BLUE

    label_surf = hud_font.render(label_text, True, label_color)
    screen.blit(label_surf, (panel_x + 8, panel_y + 6))

    time_text = f"{secs_left // 60:02d}:{secs_left % 60:02d}"
    time_surf = hud_font.render(time_text, True, WHITE)
    screen.blit(time_surf, (panel_x + panel_w - time_surf.get_width() - 8, panel_y + 6))

    bar_x  = panel_x + 8
    bar_y  = panel_y + 38
    bar_w  = panel_w - 16
    bar_h  = 12
    filled = int(bar_w * ratio)

    pygame.draw.rect(screen, (50, 50, 50),    (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    if filled > 0:
        pygame.draw.rect(screen, bar_color,   (bar_x, bar_y, filled, bar_h), border_radius=4)
    pygame.draw.rect(screen, (120, 120, 120), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

    sub_text = "Portal locked — defeat enemies!" if phase == "lobby" else "Portal open — explore!"
    sub_surf = pygame.font.Font("assets2/font/A Friend In Deed.otf", 16).render(sub_text, True, (180, 180, 180))
    screen.blit(sub_surf, (panel_x + 8, panel_y + 56))

    if relic["collected"]:
        relic_surf = small_font.render(f"✦ {relic['name']}", True, GOLD)
        screen.blit(relic_surf, (panel_x + 8, panel_y + panel_h + 6))

# ================= BUTTON =================
def button(text, center, mouse_pos):
    surf = btn_font.render(text, True, DARK)
    rect = surf.get_rect(center=center)
    if rect.collidepoint(mouse_pos):
        surf = btn_font.render(text, True, GREEN)
    screen.blit(surf, rect)
    return rect

# ================= MAIN MENU =================
def main_menu():
    global state
    while state == "menu":
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.collidepoint(mouse_pos):
                    state = "select"
        screen.blit(bg_menu, (0, 0))
        play_btn = button("PLAY", (WIDTH // 2, 270), mouse_pos)
        pygame.display.flip()

# ================= CHARACTER SELECT =================
def character_select():
    global state, selected_class, player, players
    options = [
        {"class": Archer,  "card": card_arjuna},
        {"class": Spear,   "card": card_yudhistira},
        {"class": Hammer,  "card": card_bima},
        {"class": Assasin, "card": card_yudhistira},
    ]
    selected = 0
    while state == "select":
        clock.tick(FPS)
        screen.fill((20, 20, 20))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_RETURN:
                    selected_class = options[selected]["class"]
                    player  = selected_class(400, 300)
                    player.mobile_controls = mobile_controls
                    players = pygame.sprite.Group(player)
                    broadcast_character(player)
                    state   = "game"
        cx, cy = WIDTH // 2, HEIGHT // 2
        for i, char in enumerate(options):
            offset = (i - selected) * 350
            card   = char["card"]
            card   = pygame.transform.scale(card, (340, 450) if i == selected else (280, 380))
            screen.blit(card, card.get_rect(center=(cx + offset, cy)))
        title = btn_font.render("SELECT CHARACTER", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 1))
        pygame.display.flip()

# ================= PAUSE MENU =================
def pause_menu():
    """Blocking loop — the game is fully frozen while this runs because
    no update() calls happen here, only drawing the captured frozen frame.

    Returns one of: 'resume' | 'select' | 'menu'

    To replace placeholder buttons with your own assets later:
    - Replace draw_pause_btn() with a blit of your own button sprite.
    - The rect objects (resume_rect, select_rect, menu_rect) control hit areas
      and stay the same regardless of how you draw the buttons.
    - The frozen_frame capture and overlay fill stay the same.
    """
    # Capture the exact pixel state of the screen at the moment pause was pressed.
    # This is blitted every frame of the pause loop so the game scene shows through.
    frozen_frame = screen.copy()

    # Semi-transparent dark overlay — change the 4th value (0-255) to adjust darkness.
    # 160 ≈ 63% opacity, enough to darken without completely hiding the scene.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))

    # ---- Pause menu layout ----
    btn_w, btn_h = 280, 60
    btn_x  = WIDTH  // 2 - btn_w // 2
    gap    = 80   # vertical distance between button centers
    # Order: Resume (top) → Character Selection (middle) → Main Menu (bottom)
    resume_rect = pygame.Rect(btn_x, HEIGHT // 2 - gap, btn_w, btn_h)
    select_rect = pygame.Rect(btn_x, HEIGHT // 2,       btn_w, btn_h)
    menu_rect   = pygame.Rect(btn_x, HEIGHT // 2 + gap, btn_w, btn_h)

    # Placeholder fonts — replace with your game fonts or loaded assets later.
    pause_title_font = pygame.font.SysFont("arial", 48, bold=True)
    pause_btn_font   = pygame.font.SysFont("arial", 28, bold=True)

    # Placeholder button colors
    BTN_IDLE   = (80,  80,  80)
    BTN_HOVER  = (130, 130, 130)
    BTN_TEXT   = (240, 240, 240)
    BTN_BORDER = (30,  30,  30)

    def draw_pause_btn(rect, text, hovered):
        """Placeholder button renderer.
        To swap in your own asset: blit your button sprite at rect.topleft,
        then blit the text label centered on rect. Remove this function when done."""
        color = BTN_HOVER if hovered else BTN_IDLE
        pygame.draw.rect(screen, BTN_BORDER, rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(screen, color,      rect,               border_radius=7)
        label = pause_btn_font.render(text, True, BTN_TEXT)
        screen.blit(label, (rect.centerx - label.get_width()  // 2,
                             rect.centery - label.get_height() // 2))

    while True:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            # Keep feeding events to mobile_controls so the pause button
            # can be pressed again to resume, and touch_ids stay clean.
            mobile_controls.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
            
            if dialog_box.active:
                dialog_box.handle_event(event)
                continue

            # Mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_rect.collidepoint(mouse_pos):
                    return "resume"
                if select_rect.collidepoint(mouse_pos):
                    return "select"
                if menu_rect.collidepoint(mouse_pos):
                    return "menu"

            # Touch tap directly on pause menu buttons
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if resume_rect.collidepoint(tx, ty):
                    return "resume"
                if select_rect.collidepoint(tx, ty):
                    return "select"
                if menu_rect.collidepoint(tx, ty):
                    return "menu"

        # Pressing the pause button again resumes (one-shot flag consumed here)
        if mobile_controls.pause_just_pressed:
            mobile_controls.pause_just_pressed = False
            return "resume"

        # ---- Draw: frozen game → dark overlay → pause UI ----
        screen.blit(frozen_frame, (0, 0))
        screen.blit(overlay,      (0, 0))

        title = pause_title_font.render("PAUSED", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 160))

        draw_pause_btn(resume_rect, "Resume",              resume_rect.collidepoint(mouse_pos))
        draw_pause_btn(select_rect, "Character Selection", select_rect.collidepoint(mouse_pos))
        draw_pause_btn(menu_rect,   "Main Menu",           menu_rect.collidepoint(mouse_pos))

        # Draw only the pause button itself — joystick/ATK/DASH are hidden
        pause_spr = mobile_controls._btn_pause_active \
                    if mobile_controls.btn_pause_pressed \
                    else mobile_controls._btn_pause_idle
        px, py = mobile_controls.btn_pause_center
        screen.blit(pause_spr, (px - PAUSE_BTN_SIZE // 2, py - PAUSE_BTN_SIZE // 2))

        pygame.display.flip()


# ================= CHARACTER SELECT FROM PAUSE =================
def character_select_from_pause():
    """Like character_select() but returns the chosen class instead of
    switching state directly — so game_loop stays in control of what happens next.
    Returns None if the player presses ESC to go back to the pause menu."""
    options = [
        {"class": Archer,  "card": card_arjuna},
        {"class": Spear,   "card": card_yudhistira},
        {"class": Hammer,  "card": card_bima},
        {"class": Assasin, "card": card_yudhistira},
    ]
    selected = 0
    while True:
        clock.tick(FPS)
        screen.fill((20, 20, 20))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_RETURN:
                    return options[selected]["class"]
                if event.key == pygame.K_ESCAPE:
                    return None  # back to pause menu
        cx, cy = WIDTH // 2, HEIGHT // 2
        for i, char in enumerate(options):
            offset = (i - selected) * 350
            card   = char["card"]
            card   = pygame.transform.scale(card, (340, 450) if i == selected else (280, 380))
            screen.blit(card, card.get_rect(center=(cx + offset, cy)))
        title = btn_font.render("SELECT CHARACTER", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 1))
        hint = pixel_font.render("ESC — back to pause", True, (150, 150, 150))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
        pygame.display.flip()


# ================= RESTART FROM PAUSE =================
def restart_from_pause(new_player_class):
    """Switches the player character without resetting the relic.
    Resets enemies and phase timer, spawns player at the default position."""
    global player, players, phase, phase_frames, bg_game, current_bg, enemy_respawn_timer
    player = new_player_class(*SPAWN_POS)
    player.mobile_controls = mobile_controls
    players = pygame.sprite.Group(player)
    # Reset to fight phase and map 1
    phase        = "lobby"
    phase_frames = LOBBY_DURATION * FPS
    bg_game      = bg_map1
    current_bg   = 1
    # Reset enemies
    enemies.empty()
    enemies.add(Enemy(*enemy_spawn_pos))
    enemy_respawn_timer = 0


# ================= PHASE TRANSITION HELPERS =================
def start_lobby():
    global phase, phase_frames, bg_game, current_bg
    phase        = "lobby"
    phase_frames = LOBBY_DURATION * FPS
    bg_game      = bg_map1
    current_bg   = 1
    player.rect.center = SPAWN_POS
    if len(enemies) == 0:
        enemies.add(Enemy(*enemy_spawn_pos))

def start_explore():
    global phase, phase_frames, bg_game, current_bg
    phase        = "explore"
    phase_frames = EXPLORE_DURATION * FPS
    bg_game      = bg_map2
    current_bg   = 2
    player.rect.center = BG2_SPAWN_POS
    enemies.empty()

# ================= GAME LOOP =================
def game_loop():
    global state, enemy_respawn_timer, player, players
    global arrows, bg_game, current_bg
    global phase, phase_frames
    global relic_notif_timer

    while state == "game":
        clock.tick(FPS)

        # ================= TICK PHASE TIMER =================
        if phase_frames > 0:
            phase_frames -= 1
        else:
            if phase == "lobby":
                start_explore()
            else:
                start_lobby()

        # ================= EVENTS =================
        pressed_e   = False
        should_pause = False
        for event in pygame.event.get():
            mobile_controls.handle_event(event)

            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    should_pause = True
                if event.key == pygame.K_e:
                    pressed_e = True
                if event.key == pygame.K_y:
                    print(f"Player position: x={player.rect.centerx}, y={player.rect.centery}")

        mobile_controls.update()

        if dialog_box.active:
            screen.blit(bg_game, (0, 0))
            enemies.draw(screen)
            for enemy in enemies:
                enemy.draw_healthbar(screen)
            draw_relic()
            player.draw(screen)
            player.draw_healthbar(screen)
            arrows.draw(screen)
            draw_relic_notif()
            draw_timer_panel()
            dialog_box.draw(screen)
            mobile_controls.draw(screen)
            pygame.display.flip()
            continue 

        # Touch pause button check (one-shot flag set by mobile_controls)
        if mobile_controls.pause_just_pressed:
            mobile_controls.pause_just_pressed = False
            should_pause = True

        if should_pause:
            result = pause_menu()
            if result == "select":
                chosen = character_select_from_pause()
                if chosen is not None:
                    restart_from_pause(chosen)
                # chosen is None means player hit ESC — fall back into game_loop
            elif result == "menu":
                state = "menu"
                return  # exits game_loop; outer while True picks up state == "menu"
            # result == "resume": do nothing, game_loop continues normally

        # ================= UPDATE =================
        players.update()

        if player.spawn_arrow:
            arrow = Arrow(player.rect.centerx, player.rect.centery, player.facing)
            arrows.add(arrow)
            player.spawn_arrow = False

        arrows.update()
        enemies.update(player)

        # ================= PLAYER ATTACK =================
        if not isinstance(player, Archer):
            attack_box = player.get_attack_hitbox()
            if attack_box:
                for enemy in enemies:
                    if enemy.rect.colliderect(attack_box):
                        enemy.take_damage(player.facing, player.damage)

        for arrow in list(arrows):
            for enemy in enemies:
                if arrow.rect.colliderect(enemy.rect):
                    enemy.take_damage(player.facing, player.damage)
                    arrow.kill()

        # ================= ENEMY ATTACK =================
        for enemy in enemies:
            atk = enemy.get_attack_hitbox()
            if atk and atk.colliderect(player.rect):
                player.take_damage(1)

        # ================= PORTAL INTERACTION =================
        show_interact = False
        pending_map   = None
        portal_open   = (phase == "explore")

        if current_bg == 1:
            for zone in portal_zones_map1:
                if player.rect.colliderect(zone):
                    show_interact = True
                    pending_map   = 2
                    break

        elif current_bg == 2:
            for zone in portal_zones_map2:
                if player.rect.colliderect(zone):
                    show_interact = True
                    pending_map   = 3
                    break
            if not show_interact:
                for zone in portal_zones_map4_entry:
                    if player.rect.colliderect(zone):
                        show_interact = True
                        pending_map   = 4
                        break
            if not show_interact:
                for zone in portal_zones_map5_entry:
                    if player.rect.colliderect(zone):
                        show_interact = True
                        pending_map   = 5
                        break

        elif current_bg == 3:
            for zone in portal_zones_map3:
                if player.rect.colliderect(zone):
                    show_interact = True
                    pending_map   = 2
                    break

        elif current_bg == 4:
            for zone in portal_zones_map4:
                if player.rect.colliderect(zone):
                    show_interact = True
                    pending_map   = 2
                    break

        elif current_bg == 5:
            for zone in portal_zones_map5:
                if player.rect.colliderect(zone):
                    show_interact = True
                    pending_map   = 2
                    break

        # ================= RELIC PICKUP =================
        near_relic = False
        if not relic["collected"] and relic["map"] == current_bg:
            pickup_range = pygame.Rect(relic["pos"][0] - 60, relic["pos"][1] - 60, 120, 120)
            if player.rect.colliderect(pickup_range):
                near_relic = True
                if pressed_e and not show_interact:
                    if relic["name"] == "Portal Resi":
                        # Portal Resi: setiap tekan E buka dialog box, TIDAK di-collect
                        dialog_box.open(RESI_DIALOG_TREE, start_key="start")
                    else:
                        # Relic biasa: tetap collect seperti semula
                        relic["collected"] = True
                        relic_notif_timer  = 180
                        print(f"[RELIC] '{relic['name']}' berhasil diambil!")
                        
        # Eksekusi pindah map
        if show_interact and pressed_e and portal_open:
            if pending_map == 2:
                bg_game = bg_map2
                if current_bg == 3:
                    player.rect.center = portal_zones_map2[0].center
                elif current_bg == 4:
                    player.rect.center = portal_zones_map4_entry[0].center
                elif current_bg == 5:
                    player.rect.center = portal_zones_map5_entry[0].center
                else:
                    player.rect.center = BG2_SPAWN_POS
                current_bg = 2
            elif pending_map == 3:
                bg_game    = bg_map3
                current_bg = 3
                player.rect.center = BG3_SPAWN_POS
            elif pending_map == 4:
                bg_game    = bg_map4
                current_bg = 4
                player.rect.center = BG4_SPAWN_POS
            elif pending_map == 5:
                bg_game    = bg_map5
                current_bg = 5
                player.rect.center = BG5_SPAWN_POS

        # ================= ENEMY RESPAWN (lobby only) =================
        if phase == "lobby":
            if len(enemies) == 0:
                enemy_respawn_timer += 1
                if enemy_respawn_timer >= RESPAWN_DELAY:
                    enemies.add(Enemy(*enemy_spawn_pos))
                    enemy_respawn_timer = 0
        else:
            enemy_respawn_timer = 0

        # ================= DRAW =================
        screen.blit(bg_game, (0, 0))

        enemies.draw(screen)
        for enemy in enemies:
            enemy.draw_healthbar(screen)

        # ← RELIC DIGAMBAR DI SINI
        draw_relic()

        player.draw(screen)
        player.draw_healthbar(screen)

        arrows.draw(screen)

        # Portal prompt
        if show_interact:
            if portal_open:
                msg = pixel_font.render("Press E", True, WHITE)
            else:
                msg = pixel_font.render("Portal locked!", True, RED)
            screen.blit(msg, (player.rect.centerx - msg.get_width() // 2,
                               player.rect.top - 44))

        # Relic prompt (hanya jika tidak overlap dengan portal)
        if near_relic and not show_interact:
            draw_relic_prompt()

        # Notifikasi pickup
        draw_relic_notif()

        draw_timer_panel()

        # Virtual joystick + attack/dash + pause button (drawn last = on top)
        # show_pause=True makes all controls visible; they are hidden on other screens
        # because draw() is not called at all in main_menu() or character_select().
        mobile_controls.draw(screen, show_pause=True)

        pygame.display.flip()

# ================= RUN =================
while True:
    if state == "menu":
        main_menu()
    elif state == "select":
        character_select()
    elif state == "game":
        game_loop()
