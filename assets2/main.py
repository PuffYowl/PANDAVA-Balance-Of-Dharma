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

pygame.init() 

# ================= WINDOW =================
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("Pandava: Balance of Dharma")
clock = pygame.time.Clock()
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
relic_arjuna    = pygame.transform.scale(relic_arjuna, (15, 15))
relic_bima      = pygame.image.load("assets2/relic2.png").convert_alpha()
relic_bima      = pygame.transform.scale(relic_bima, (15, 15))
relic_yudhistira = pygame.image.load("assets2/relic3.png").convert_alpha()
relic_yudhistira = pygame.transform.scale(relic_yudhistira, (30, 30))
relic_sadewa    = pygame.image.load("assets2/relic4.png").convert_alpha()
relic_sadewa    = pygame.transform.scale(relic_sadewa, (15, 15))
relic_nakula    = pygame.image.load("assets2/relic5.png").convert_alpha()
relic_nakula    = pygame.transform.scale(relic_nakula, (15, 15))

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
EXPLORE_DURATION = 60
LOBBY_DURATION   = 0.25*EXPLORE_DURATION

# ================= PHASE STATE =================
phase         = "lobby"
phase_frames  = LOBBY_DURATION * FPS

# ================= STATE =================
state          = "menu"
selected_class = Assasin
SPAWN_POS      = (400, 300)

# ================= PLAYER =================
player  = Assasin(400, 300)
players = pygame.sprite.Group(player)

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
                    players = pygame.sprite.Group(player)
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
        pressed_e = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
                if event.key == pygame.K_e:
                    pressed_e = True
                if event.key == pygame.K_y:
                    print(f"Player position: x={player.rect.centerx}, y={player.rect.centery}")

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

        pygame.display.flip()

# ================= RUN =================
while True:
    if state == "menu":
        main_menu()
    elif state == "select":
        character_select()
    elif state == "game":
        game_loop()