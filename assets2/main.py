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
from miniboss1 import Miniboss_1
from mobile_controls import MobileControls, PAUSE_BTN_SIZE
from character_registry import broadcast_character
from dialog_system import DialogBox, RESI_DIALOG_TREE, PRASASTI_BUFFS, PRASASTI_RELIC_REQUIRED, HealingAura, UpgradeAura, HonorSystem
from sacred_tree import CovenantNPC, TreeRitualSystem, do_covenant_dialog, do_ritual_minigame
import sacred_tree as _sacred_tree
from player_hud import PlayerHUD, stamina_ratio_from_dash
pygame.init() 

# ================= WINDOW =================
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("Pandava: Balance of Dharma")
clock = pygame.time.Clock()
_sacred_tree.WIDTH_FALLBACK = WIDTH   # supaya punishment enemy spawn di tepi layar yang benar


# Virtual joystick + attack/dash buttons for mobile.
# Set mobile_controls.visible = False to hide on desktop builds.
mobile_controls = MobileControls(WIDTH, HEIGHT)
dialog_box = DialogBox(WIDTH, HEIGHT)
healing_aura = HealingAura()
upgrade_aura = UpgradeAura()
honor_system = HonorSystem(initial=0)      # mulai seimbang (0)
dialog_box.honor_system = honor_system     # honor bar muncul di dalam dialog
player_hud = PlayerHUD()

# ── Sacred Tree / Covenant NPC ─────────────────────────────────────────
covenant_npc  = CovenantNPC()
ritual_system = TreeRitualSystem(covenant_npc, fps=60)
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

# Background khusus saat dialog Resi aktif
# File: assets2/background_resi.png  (940×768, pixel-art interior candi)
_bg_resi_candidates = [
    "assets2/background_resi.png",   # nama file yang dikirim
    "assets2/bg_resi.png",           # nama alternatif lama
]
bg_resi = None
for _bg_path in _bg_resi_candidates:
    try:
        bg_resi = pygame.image.load(_bg_path).convert()
        bg_resi = pygame.transform.scale(bg_resi, (WIDTH, HEIGHT))
        print(f"[BG RESI] Loaded: {_bg_path}")
        break
    except (pygame.error, FileNotFoundError):
        pass
if bg_resi is None:
    # Fallback: warna ungu gelap kalau file belum ada di folder assets2
    bg_resi = pygame.Surface((WIDTH, HEIGHT))
    bg_resi.fill((30, 20, 45))
    print("[BG RESI] File tidak ditemukan — pakai fallback warna gelap.")

# ── Covenant NPC assets — salin ke assets2 jika file sumber ada ────────
import shutil as _shutil, os as _os
_covenant_asset_map = {
    "assets2/covenant_tiger.png": [
        "assets2/covenant_tiger.png",
        # Sumber: frame_0000.png yang diupload user
    ],
    "assets2/covenant_tree.png": [
        "assets2/covenant_tree.png",
    ],
}
# Kalau asset belum ada, coba copy dari uploads / working dir
for _dst, _srcs in [
    ("assets2/covenant_tiger.png",
     ["assets2/frame_0000.png", "frame_0000.png"]),
    ("assets2/covenant_tree.png",
     ["assets2/big.png", "big.png"]),
]:
    if not _os.path.exists(_dst):
        for _src in _srcs:
            if _os.path.exists(_src):
                _shutil.copy2(_src, _dst)
                print(f"[COVENANT] Copied {_src} → {_dst}")
                break

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
GRAY   = (60,  60,  60)   # background polos saat dialog box aktif

# ================= TIMER DURATIONS (seconds) =================
LOBBY_DURATION   = 3
EXPLORE_DURATION = 60

PORTRAIT_PATHS = {
    "Archer":  "assets2/portraits/archer_portrait.png"
}

# ================= PHASE STATE =================
phase         = "lobby"
phase_frames  = LOBBY_DURATION * FPS

# ================= STATE =================
state          = "menu"
selected_class = Archer
SPAWN_POS      = (400, 300)

# Jumlah "air" yang ditampilkan di HUD kiri atas. Untuk saat ini selalu 0
# sesuai permintaan — nanti tinggal update variabel ini begitu ada sistem
# pickup/currency air yang sebenarnya.
water_count = 0

# ================= PLAYER =================
player  = Archer(400, 300)
player.mobile_controls = mobile_controls
player.honor_system    = honor_system
players = pygame.sprite.Group(player)
broadcast_character(player)
player_hud.set_character(player.__class__.__name__)

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
# NOTE: "Portal Resi" sengaja TIDAK ada di sini lagi — dia sekarang punya
# object & generator sendiri (lihat generate_portal_resi() di bawah) supaya
# posisinya selalu di tengah map dan selalu muncul berbarengan dengan relic ini,
# bukan jadi salah satu pilihan random dari relic biasa.
RELIC_OPTIONS = [
    {"name": "Batu Arjuna",     "img": relic_arjuna},
    {"name": "Batu Bima",       "img": relic_bima},
    {"name": "Batu Yudhistira", "img": relic_yudhistira},
    {"name": "Batu Sadewa",     "img": relic_sadewa},
    {"name": "Batu Nakula",     "img": relic_nakula},
]


def generate_relic():
    """Relic biasa (collectible). Map & posisi random, independen dari Portal Resi."""
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


def generate_portal_resi():
    """
    Portal Resi: selalu muncul berbarengan dengan relic biasa, di map random
    [3, 4, 5], TAPI posisinya selalu di tengah-tengah map (WIDTH//2, HEIGHT//2)
    — tidak ikut RELIC_POSITIONS sama sekali.
    """
    portal_map = random.choice([3, 4, 5])
    portal_pos = (WIDTH // 2, HEIGHT // 2)
    return {
        "map":  portal_map,
        "pos":  portal_pos,
        "name": "Portal Resi",
        "img":  portal_resi,
        "rect": pygame.Rect(portal_pos[0] - 50, portal_pos[1] - 50, 100, 100),
    }


relic       = generate_relic()
portal      = generate_portal_resi()
relic_pulse = 0
relic_notif_timer = 0
print(f"[RELIC] '{relic['name']}' muncul di Map {relic['map']} posisi {relic['pos']}")
print(f"[PORTAL] '{portal['name']}' muncul di Map {portal['map']} posisi {portal['pos']}")

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

# ================= PORTAL RESI DRAW =================
# Terpisah dari relic biasa karena Portal Resi tidak pernah "collected"
# (lihat dialog_box.open() di RELIC PICKUP) dan posisinya selalu di tengah map.
def draw_portal():
    if portal["map"] != current_bg:
        return
    x, y = portal["pos"]
    screen.blit(portal["img"], portal["img"].get_rect(center=(x, y)))

def draw_portal_prompt():
    """Tampilkan 'Press E' di atas Portal Resi jika player dekat."""
    if portal["map"] != current_bg:
        return False
    pickup_range = pygame.Rect(portal["pos"][0] - 60, portal["pos"][1] - 60, 120, 120)
    if player.rect.colliderect(pickup_range):
        label = small_font.render(f"Press E — {portal['name']}", True, GOLD)
        screen.blit(label, (
            portal["pos"][0] - label.get_width() // 2,
            portal["pos"][1] - 70
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


def _draw_menu_btn(surface, font, text, rect, hovered):
    """Tombol menu utama bergaya panel semi-transparan + teks."""
    idle_color  = (20,  16,  30, 180)
    hover_color = (60,  44,  90, 220)
    border_idle = (100, 80, 140)
    border_hov  = (255, 210, 60)

    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    panel.fill(hover_color if hovered else idle_color)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, border_hov if hovered else border_idle,
                     rect, 2, border_radius=8)

    label = font.render(text, True, GOLD if hovered else WHITE)
    surface.blit(label, label.get_rect(center=rect.center))
    return rect


# ================= MAIN MENU =================
def main_menu():
    global state
    menu_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 56)
    sub_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 34)

    btn_w, btn_h = 260, 62
    cx = WIDTH // 2
    play_rect     = pygame.Rect(cx - btn_w // 2, 240, btn_w, btn_h)
    tutorial_rect = pygame.Rect(cx - btn_w // 2, 318, btn_w, btn_h)
    index_rect    = pygame.Rect(cx - btn_w // 2, 396, btn_w, btn_h)

    while state == "menu":
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Mouse ──────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_rect.collidepoint(mouse_pos):
                    state = "select"; return
                if tutorial_rect.collidepoint(mouse_pos):
                    tutorial_screen(); return
                if index_rect.collidepoint(mouse_pos):
                    index_screen(); return

            # ── Touch ──────────────────────────────────────────────
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if play_rect.collidepoint(tx, ty):
                    state = "select"; return
                if tutorial_rect.collidepoint(tx, ty):
                    tutorial_screen(); return
                if index_rect.collidepoint(tx, ty):
                    index_screen(); return

        screen.blit(bg_menu, (0, 0))
        _draw_menu_btn(screen, sub_font, "▶  BERMAIN",  play_rect,
                       play_rect.collidepoint(mouse_pos))
        _draw_menu_btn(screen, sub_font, "?  TUTORIAL", tutorial_rect,
                       tutorial_rect.collidepoint(mouse_pos))
        _draw_menu_btn(screen, sub_font, "✦  INDEX",    index_rect,
                       index_rect.collidepoint(mouse_pos))
        pygame.display.flip()


# ================= TUTORIAL SCREEN =================
def tutorial_screen():
    """Layar tutorial — menjelaskan kontrol dasar dan mekanisme game."""
    tf  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 38)
    sf  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 22)
    hf  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 18)
# hehehe boiii sigma ohio grimace shake sigma yo el teach
    lines = [
        ("PANDAVA — BALANCE OF DHARMA", True),
        ("", False),
        ("KONTROL", True),
        ("  Gerak   :  WASD / Arrow Keys / Joystick kiri", False),
        ("  Serang  :  J / Tombol ATK", False),
        ("  Dash    :  K / Tombol DASH", False),
        ("  Ultimate:  U / Tombol BOOST  (khusus Arjuna)", False),
        ("  Interaksi: E (dekat portal / relic / Resi)", False),
        ("  Jeda    :  ESC / Tombol Pause (atas tengah)", False),
        ("", False),
        ("MEKANIK", True),
        ("  • Fase Bertarung — kalahkan musuh hingga timer habis", False),
        ("  • Fase Jelajah   — portal terbuka, temukan relic & Resi", False),
        ("  • Ambil Relic (Batu) → tukar ke Resi Abimayasa", False),
        ("  • Resi bisa mengupgrade stat atau memulihkan HP", False),
        ("  • HP habis = Game Over", False),
        ("", False),
        ("TIPS", True),
        ("  • Dash untuk menghindari serangan musuh", False),
        ("  • Upgrade damage Bima atau speed Nakula lebih dulu", False),
        ("  • Resi hanya bisa menyembuhkan jika HP tidak penuh", False),
    ]

    back_w, back_h = 180, 50
    back_rect = pygame.Rect(WIDTH // 2 - back_w // 2, HEIGHT - back_h - 14,
                            back_w, back_h)

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mouse_pos):
                    running = False
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH); ty = int(event.y * HEIGHT)
                if back_rect.collidepoint(tx, ty):
                    running = False

        # Background gelap bergaya scroll lontar
        screen.fill((18, 12, 28))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        screen.blit(overlay, (0, 0))

        # Panel konten
        panel_rect = pygame.Rect(40, 20, WIDTH - 80, HEIGHT - 90)
        panel_surf = pygame.Surface((panel_rect.w, panel_rect.h), pygame.SRCALPHA)
        panel_surf.fill((20, 14, 36, 200))
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (100, 80, 140), panel_rect, 2, border_radius=10)

        y = 30
        for text, is_header in lines:
            if is_header:
                surf = tf.render(text, True, GOLD)
            else:
                surf = sf.render(text, True, (210, 200, 230))
            screen.blit(surf, (60, y))
            y += 36 if is_header else 26

        # Tombol back
        hov = back_rect.collidepoint(mouse_pos)
        _draw_menu_btn(screen, sf, "◄  Kembali", back_rect, hov)
        pygame.display.flip()


# ================= INDEX SCREEN =================
# Data cerita Pandava Lima untuk layar Index
_PANDAVA_LORE = [
    {
        "name":  "Arjuna",
        "title": "Sang Pemanah Tanpa Tanding",
        "card":  None,   # diisi dari card_arjuna setelah aset dimuat
        "color": (80, 160, 255),   # biru langit
        "lore":  [
            "Arjuna adalah putra ketiga Pandu dari ibu Kunti,",
            "lahir dari berkah Dewa Indra, raja para dewa.",
            "",
            "Ia dikenal sebagai pemanah terbaik di dunia,",
            "murid kesayangan Resi Drona yang melebihi semua",
            "ksatria semasanya dalam ketepatan dan konsentrasi.",
            "",
            "Dalam Perang Bharatayuddha, Arjuna menjadi",
            "pilar utama pasukan Pandava. Saat goyah melihat",
            "keluarga di pihak musuh, Krishna menurunkan",
            "Bhagavad Gita — ajaran dharma untuk jiwa yang bimbang.",
            "",
            "Senjata andalannya: Gandiva — busur pemberian dewa,",
            "dan panah sakti Pasupati dari Dewa Siwa sendiri.",
        ],
    },
    {
        "name":  "Bima",
        "title": "Angin Kencang Werkudara",
        "card":  None,   # diisi dari card_bima
        "color": (220, 100, 40),   # oranye api
        "lore":  [
            "Bima atau Werkudara adalah putra kedua Pandu,",
            "lahir dari angin Dewa Bayu — sumber kekuatannya",
            "yang luar biasa dan tak tertandingi.",
            "",
            "Tubuhnya besar, tenaganya setara seribu gajah.",
            "Ia mampu membawa senjata Gada (gada besi) yang",
            "tidak sanggup diangkat ksatria lain.",
            "",
            "Bima adalah pejuang terdepan Pandava — tidak kenal",
            "takut, tidak kenal mundur. Dendamnya kepada Duryodana",
            "dan Dursasana berakhir di medan Kurukshetra.",
            "",
            "Anak Bima yang terkenal: Gatotkaca, raksasa sakti",
            "yang gugur demi melindungi ayahnya dan Pandava.",
        ],
    },
    {
        "name":  "Yudhistira",
        "title": "Raja Dharma yang Teguh",
        "card":  None,   # diisi dari card_yudhistira
        "color": (80, 220, 140),   # hijau kebijaksanaan
        "lore":  [
            "Yudhistira adalah putra sulung Pandu dari Kunti,",
            "lahir dari berkah Dewa Yama — dewa keadilan dan dharma.",
            "",
            "Ia dikenal sebagai penjelmaan Dharma: jujur mutlak,",
            "bijaksana, dan tidak pernah berbohong seumur hidupnya",
            "— kecuali satu kali, demi memenangkan perang suci.",
            "",
            "Sebagai raja Hastinapura setelah Bharatayuddha,",
            "pemerintahannya membawa era keemasan dan kedamaian.",
            "",
            "Senjata andalannya: Tombak Kaladanda — senjata",
            "keadilan yang hanya efektif di tangan yang benar.",
            "Kekuatannya bukan fisik, melainkan kebijaksanaan",
            "dan keteguhan hati dalam menghadapi segala cobaan.",
        ],
    },
    {
        "name":  "Nakula",
        "title": "Sang Pendekar Tampan Mahir Senjata",
        "card":  None,   # fallback ke card_yudhistira (belum ada card khusus)
        "color": (180, 80, 255),   # ungu
        "lore":  [
            "Nakula adalah putra pertama dari ibu Madri,",
            "lahir dari berkah kembar Dewa Aswin — dewa tabib.",
            "",
            "Ia dikenal sebagai yang terindah di antara Pandava,",
            "ahli pedang, dan memiliki keahlian luar biasa",
            "dalam merawat kuda — hewan yang sangat berharga",
            "di era Mahabharata.",
            "",
            "Bersama saudara kembarnya Sadewa, Nakula menjadi",
            "penjaga setia Yudhistira dan pelindung kubu Pandava.",
            "",
            "Meski tidak sepopuler Arjuna atau Bima dalam kisah",
            "utama, kegesitan dan kelincahannya dalam pertempuran",
            "menjadi aset tak ternilai bagi pasukan Pandava.",
        ],
    },
    {
        "name":  "Sadewa",
        "title": "Si Kembar Cendekia Ahli Ilmu Bintang",
        "card":  None,   # fallback ke card_yudhistira
        "color": (255, 210, 60),   # emas
        "lore":  [
            "Sadewa adalah putra bungsu dari ibu Madri,",
            "kembar dari Nakula, lahir dari berkah Dewa Aswin.",
            "",
            "Di antara lima Pandava, Sadewa memiliki kecerdasan",
            "tertinggi dan menguasai ilmu astronomi & perbintangan.",
            "Ia mampu meramal masa depan — namun dikutuk untuk",
            "tidak mengungkapkannya tanpa ditanya terlebih dahulu.",
            "",
            "Sadewa mengetahui akan ada Perang Bharatayuddha",
            "jauh sebelum terjadi, namun terpaksa diam karena",
            "kutukan tersebut.",
            "",
            "Kekuatannya memang tidak sebesar Bima, tetapi",
            "kombinasi kecerdasan dan kemampuan tempur Sadewa",
            "menjadikannya pendekar yang sangat berbahaya.",
        ],
    },
]


def index_screen():
    """Layar Index — pilih karakter Pandava untuk baca ceritanya."""
    # Assign card references setelah aset dimuat
    _PANDAVA_LORE[0]["card"] = card_arjuna
    _PANDAVA_LORE[1]["card"] = card_bima
    _PANDAVA_LORE[2]["card"] = card_yudhistira
    _PANDAVA_LORE[3]["card"] = card_yudhistira   # belum ada card Nakula khusus
    _PANDAVA_LORE[4]["card"] = card_yudhistira   # belum ada card Sadewa khusus

    title_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 36)
    name_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 30)
    sub_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 20)
    hint_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 16)

    selected = 0
    arrow_btn_size = 54
    cx, cy   = WIDTH // 2, HEIGHT // 2

    left_rect  = pygame.Rect(cx - 300 - arrow_btn_size // 2,
                             cy - arrow_btn_size // 2,
                             arrow_btn_size, arrow_btn_size)
    right_rect = pygame.Rect(cx + 300 - arrow_btn_size // 2,
                             cy - arrow_btn_size // 2,
                             arrow_btn_size, arrow_btn_size)

    back_w, back_h = 180, 50
    back_rect = pygame.Rect(cx - back_w // 2, HEIGHT - back_h - 14,
                            back_w, back_h)

    def draw_arrow_btn(rect, symbol, hovered):
        color  = (200, 170, 40) if hovered else (60, 50, 30)
        border = (255, 220, 80) if hovered else (100, 80, 40)
        pygame.draw.rect(screen, border, rect.inflate(4, 4), border_radius=10)
        pygame.draw.rect(screen, color,  rect,               border_radius=9)
        a_surf = title_font.render(symbol, True, WHITE)
        screen.blit(a_surf, a_surf.get_rect(center=rect.center))

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        char = _PANDAVA_LORE[selected]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(_PANDAVA_LORE)
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(_PANDAVA_LORE)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if left_rect.collidepoint(mx, my):
                    selected = (selected - 1) % len(_PANDAVA_LORE)
                elif right_rect.collidepoint(mx, my):
                    selected = (selected + 1) % len(_PANDAVA_LORE)
                elif back_rect.collidepoint(mx, my):
                    running = False

            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH); ty = int(event.y * HEIGHT)
                if left_rect.collidepoint(tx, ty):
                    selected = (selected - 1) % len(_PANDAVA_LORE)
                elif right_rect.collidepoint(tx, ty):
                    selected = (selected + 1) % len(_PANDAVA_LORE)
                elif back_rect.collidepoint(tx, ty):
                    running = False

        # ── Draw background ──────────────────────────────────────
        screen.fill((12, 8, 22))
        # Warna aksen tiap karakter sebagai tinted vignette tipis
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        r, g, b = char["color"]
        tint.fill((r, g, b, 20))
        screen.blit(tint, (0, 0))

        # ── Judul ──────────────────────────────────────────────────
        t_surf = title_font.render("✦  INDEX PANDAVA  ✦", True, GOLD)
        screen.blit(t_surf, (cx - t_surf.get_width() // 2, 10))

        # ── Card karakter (kiri) ────────────────────────────────────
        card_scaled = pygame.transform.scale(char["card"], (180, 250))
        card_rect   = card_scaled.get_rect(topleft=(55, 80))
        # Border warna karakter
        pygame.draw.rect(screen, char["color"], card_rect.inflate(6, 6), 3, border_radius=6)
        screen.blit(card_scaled, card_rect)

        # ── Nama & judul karakter ──────────────────────────────────
        name_surf = name_font.render(char["name"], True, char["color"])
        screen.blit(name_surf, (260, 82))
        sub_surf  = sub_font.render(char["title"], True, (200, 190, 210))
        screen.blit(sub_surf, (260, 118))

        # Garis pemisah tipis
        pygame.draw.line(screen, char["color"], (260, 148), (WIDTH - 60, 148), 1)

        # ── Teks cerita ────────────────────────────────────────────
        lore_y = 158
        for line in char["lore"]:
            if line == "":
                lore_y += 10
                continue
            l_surf = sub_font.render(line, True, (215, 205, 225))
            screen.blit(l_surf, (260, lore_y))
            lore_y += 24

        # ── Dots navigator ─────────────────────────────────────────
        dot_y = HEIGHT - 70
        for i, p in enumerate(_PANDAVA_LORE):
            dot_x = cx - (len(_PANDAVA_LORE) // 2 - i) * 22
            col   = p["color"] if i == selected else (60, 55, 70)
            pygame.draw.circle(screen, col, (dot_x, dot_y), 7)
            if i == selected:
                pygame.draw.circle(screen, WHITE, (dot_x, dot_y), 7, 2)

        # ── Panah navigasi ─────────────────────────────────────────
        draw_arrow_btn(left_rect,  "◄", left_rect.collidepoint(mouse_pos))
        draw_arrow_btn(right_rect, "►", right_rect.collidepoint(mouse_pos))

        # ── Tombol kembali ─────────────────────────────────────────
        _draw_menu_btn(screen, sub_font, "◄  Kembali", back_rect,
                       back_rect.collidepoint(mouse_pos))

        hint = hint_font.render("◄ / ► untuk navigasi  |  ESC untuk kembali",
                                True, (110, 100, 130))
        screen.blit(hint, (cx - hint.get_width() // 2, HEIGHT - 18))

        pygame.display.flip()

# ================= MAP OVERLAY =================
# Info per area — nama, warna, dan keterangan singkat
_MAP_AREAS = {
    1: {
        "name":  "Medan Pertempuran",
        "color": (220, 80,  60),
        "desc":  ["Area awal — temukan musuh di sini.",
                  "Fase Bertarung: kalahkan semua musuh",
                  "hingga timer habis untuk buka portal."],
        "icon":  "⚔",
    },
    2: {
        "name":  "Dataran Tengah",
        "color": (80,  160, 255),
        "desc":  ["Hub utama penghubung semua area.",
                  "Portal ke Map 3, 4, dan 5 tersedia di sini.",
                  "Jelajahi tiap sudut untuk masuk area lain."],
        "icon":  "✦",
    },
    3: {
        "name":  "Hutan Sakral",
        "color": (80,  220, 120),
        "desc":  ["Area alam mistis penuh relic tersembunyi.",
                  "Portal Resi Abimayasa bisa muncul di sini.",
                  "Bisa kembali ke Dataran Tengah via portal."],
        "icon":  "🌿",
    },
    4: {
        "name":  "Kuil Kuno",
        "color": (255, 180, 40),
        "desc":  ["Reruntuhan candi penuh misteri dan relic.",
                  "Portal Resi dan Batu Prasasti ada di sini.",
                  "Bisa kembali ke Dataran Tengah via portal."],
        "icon":  "🏛",
    },
    5: {
        "name":  "Puncak Kahyangan",
        "color": (180, 80,  255),
        "desc":  ["Area tertinggi — langit dan awan.",
                  "Relic langka dan Portal Resi ada di sini.",
                  "Bisa kembali ke Dataran Tengah via portal."],
        "icon":  "☁",
    },
}


def show_map_overlay(current_map: int):
    """Tampilkan overlay peta — blocking loop, return saat ditutup."""
    title_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 34)
    area_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 24)
    desc_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 18)
    hint_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 15)

    frozen = screen.copy()

    close_w, close_h = 170, 46
    close_rect = pygame.Rect(WIDTH // 2 - close_w // 2,
                             HEIGHT - close_h - 12, close_w, close_h)

    # Layout 5 node peta dalam formasi: 1 di kiri, 2 di tengah atas,
    # 3 di kanan bawah, 4 di tengah bawah, 5 di kanan atas
    # Gunakan koordinat relatif di panel peta (panel 420×280 di tengah layar)
    PANEL_X = WIDTH  // 2 - 210
    PANEL_Y = HEIGHT // 2 - 155
    NODE_POS = {
        1: (PANEL_X + 42,  PANEL_Y + 130),   # kiri tengah
        2: (PANEL_X + 210, PANEL_Y + 130),   # tengah
        3: (PANEL_X + 80,  PANEL_Y + 50),    # kiri atas
        4: (PANEL_X + 210, PANEL_Y + 220),   # bawah tengah
        5: (PANEL_X + 340, PANEL_Y + 50),    # kanan atas
    }
    # Koneksi antar area (edge peta)
    EDGES = [(1, 2), (2, 3), (2, 4), (2, 5)]
    NODE_R = 28

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(mouse_pos):
                    running = False
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH); ty = int(event.y * HEIGHT)
                if close_rect.collidepoint(tx, ty):
                    running = False

        # ── Background: frozen gameplay + gelap
        screen.blit(frozen, (0, 0))
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 175))
        screen.blit(dim, (0, 0))

        # ── Panel latar peta
        panel_surf = pygame.Surface((440, 300), pygame.SRCALPHA)
        panel_surf.fill((15, 10, 30, 220))
        screen.blit(panel_surf, (PANEL_X - 10, PANEL_Y - 20))
        pygame.draw.rect(screen, (90, 70, 130),
                         (PANEL_X - 10, PANEL_Y - 20, 440, 300), 2, border_radius=10)

        # ── Judul
        t_surf = title_font.render("✦  PETA AREA  ✦", True, GOLD)
        screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, PANEL_Y - 52))

        # ── Gambar edge / koneksi
        for a, b in EDGES:
            pygame.draw.line(screen, (70, 60, 90),
                             NODE_POS[a], NODE_POS[b], 3)

        # ── Gambar node
        for area_id, pos in NODE_POS.items():
            area = _MAP_AREAS[area_id]
            is_current = (area_id == current_map)
            col = area["color"]

            # Glow kalau area saat ini
            if is_current:
                glow_surf = pygame.Surface((NODE_R * 4, NODE_R * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*col, 60),
                                   (NODE_R * 2, NODE_R * 2), NODE_R * 2)
                screen.blit(glow_surf, (pos[0] - NODE_R * 2, pos[1] - NODE_R * 2))

            pygame.draw.circle(screen, (20, 15, 35), pos, NODE_R)
            pygame.draw.circle(screen, col, pos, NODE_R, 3 if not is_current else 0)
            if is_current:
                pygame.draw.circle(screen, col, pos, NODE_R)

            # Icon area
            icon_surf = area_font.render(area["icon"], True,
                                         BLACK if is_current else col)
            screen.blit(icon_surf, icon_surf.get_rect(center=pos))

            # Nomor kecil di bawah node
            num_surf = hint_font.render(str(area_id), True, WHITE)
            screen.blit(num_surf, (pos[0] - num_surf.get_width() // 2,
                                   pos[1] + NODE_R + 2))

        # ── Panel info area saat ini (kanan layar)
        info_x = PANEL_X + 460
        info_y = PANEL_Y - 20
        info_panel = pygame.Surface((220, 300), pygame.SRCALPHA)
        info_panel.fill((15, 10, 30, 210))
        screen.blit(info_panel, (info_x, info_y))
        pygame.draw.rect(screen, _MAP_AREAS[current_map]["color"],
                         (info_x, info_y, 220, 300), 2, border_radius=10)

        cur = _MAP_AREAS[current_map]
        now_surf = desc_font.render("LOKASI SEKARANG", True, (140, 130, 160))
        screen.blit(now_surf, (info_x + 10, info_y + 10))

        name_surf = area_font.render(cur["name"], True, cur["color"])
        screen.blit(name_surf, (info_x + 10, info_y + 34))
        pygame.draw.line(screen, cur["color"],
                         (info_x + 10, info_y + 62),
                         (info_x + 210, info_y + 62), 1)

        dy = info_y + 72
        for line in cur["desc"]:
            d_surf = hint_font.render(line, True, (200, 195, 215))
            screen.blit(d_surf, (info_x + 10, dy))
            dy += 22

        # Legenda "Kamu di sini"
        pygame.draw.circle(screen, cur["color"],
                           (info_x + 16, dy + 20), 8)
        here_surf = hint_font.render("= Posisi kamu", True, (180, 175, 200))
        screen.blit(here_surf, (info_x + 30, dy + 12))

        # ── Tombol tutup
        hov = close_rect.collidepoint(mouse_pos)
        _draw_menu_btn(screen, desc_font, "✕  Tutup", close_rect, hov)

        hint = hint_font.render("M / ESC untuk menutup", True, (90, 80, 110))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 14))

        pygame.display.flip()
def _draw_character_select_ui(surface, options, selected, title_font, hint_font):
    """Render character select screen: cards + arrow buttons + checkmark button."""
    surface.fill((15, 12, 28))

    cx, cy = WIDTH // 2, HEIGHT // 2

    # ── Cards ────────────────────────────────────────────────────
    for i, char in enumerate(options):
        offset = (i - selected) * 340
        card   = char["card"]
        if i == selected:
            card = pygame.transform.scale(card, (300, 420))
            # Golden border on selected card
            card_rect = card.get_rect(center=(cx + offset, cy))
            pygame.draw.rect(surface, GOLD, card_rect.inflate(6, 6), 3, border_radius=6)
        else:
            card = pygame.transform.scale(card, (240, 340))
            card_rect = card.get_rect(center=(cx + offset, cy))
        surface.blit(card, card_rect)

    # ── Title ────────────────────────────────────────────────────
    title_surf = title_font.render("SELECT CHARACTER", True, GOLD)
    surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))

    # ── Arrow LEFT button ────────────────────────────────────────
    arrow_btn_size = 54
    left_rect  = pygame.Rect(cx - 280 - arrow_btn_size // 2, cy - arrow_btn_size // 2,
                             arrow_btn_size, arrow_btn_size)
    right_rect = pygame.Rect(cx + 280 - arrow_btn_size // 2, cy - arrow_btn_size // 2,
                             arrow_btn_size, arrow_btn_size)

    mouse_pos = pygame.mouse.get_pos()

    def draw_arrow_btn(rect, symbol, hovered):
        color  = (200, 170, 40) if hovered else (80, 70, 40)
        border = (255, 220, 80) if hovered else (120, 100, 50)
        pygame.draw.rect(surface, border, rect.inflate(4, 4), border_radius=10)
        pygame.draw.rect(surface, color,  rect,               border_radius=9)
        arrow_surf = title_font.render(symbol, True, WHITE)
        surface.blit(arrow_surf, arrow_surf.get_rect(center=rect.center))

    draw_arrow_btn(left_rect,  "◄", left_rect.collidepoint(mouse_pos))
    draw_arrow_btn(right_rect, "►", right_rect.collidepoint(mouse_pos))

    # ── Checkmark CONFIRM button ──────────────────────────────────
    check_w, check_h = 180, 56
    check_rect = pygame.Rect(cx - check_w // 2, HEIGHT - check_h - 24, check_w, check_h)
    check_hover = check_rect.collidepoint(mouse_pos)
    check_color  = (40, 180, 80)  if check_hover else (30, 120, 55)
    check_border = (80, 255, 120) if check_hover else (50, 160, 80)
    pygame.draw.rect(surface, check_border, check_rect.inflate(4, 4), border_radius=12)
    pygame.draw.rect(surface, check_color,  check_rect,               border_radius=11)
    check_surf = title_font.render("✓  Pilih", True, WHITE)
    surface.blit(check_surf, check_surf.get_rect(center=check_rect.center))

    # ── Keyboard hint ─────────────────────────────────────────────
    hint_surf = hint_font.render("◄ / ► untuk memilih   |   Enter / ✓ untuk konfirmasi", True, (160, 160, 160))
    surface.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT - 22))

    return left_rect, right_rect, check_rect


def character_select():
    global state, selected_class, player, players
    options = [
        {"class": Archer,  "card": card_arjuna,     "name": "Arjuna"},
        {"class": Spear,   "card": card_yudhistira,  "name": "Yudhistira"},
        {"class": Hammer,  "card": card_bima,        "name": "Bima"},
        {"class": Assasin, "card": card_yudhistira,  "name": "Assasin"},
    ]
    selected  = 0
    sel_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 36)
    hint_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 16)

    # Inisialisasi dummy supaya event handler tidak error sebelum frame pertama digambar
    left_rect  = pygame.Rect(0, 0, 1, 1)
    right_rect = pygame.Rect(0, 0, 1, 1)
    check_rect = pygame.Rect(0, 0, 1, 1)

    def confirm_selection():
        nonlocal selected
        global state, selected_class, player, players
        selected_class = options[selected]["class"]
        player  = selected_class(400, 300)
        player.mobile_controls = mobile_controls
        player.honor_system    = honor_system
        players = pygame.sprite.Group(player)
        broadcast_character(player)
        player_hud.set_character(player.__class__.__name__)
        state = "game"

    while state == "select":
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard ─────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    selected = (selected + 1) % len(options)
                if event.key == pygame.K_LEFT:
                    selected = (selected - 1) % len(options)
                if event.key == pygame.K_RETURN:
                    confirm_selection()
                    return

            # ── Mouse click ───────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if left_rect.collidepoint(mx, my):
                    selected = (selected - 1) % len(options)
                elif right_rect.collidepoint(mx, my):
                    selected = (selected + 1) % len(options)
                elif check_rect.collidepoint(mx, my):
                    confirm_selection()
                    return

            # ── Touch ─────────────────────────────────────────────
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if left_rect.collidepoint(tx, ty):
                    selected = (selected - 1) % len(options)
                elif right_rect.collidepoint(tx, ty):
                    selected = (selected + 1) % len(options)
                elif check_rect.collidepoint(tx, ty):
                    confirm_selection()
                    return

        left_rect, right_rect, check_rect = _draw_character_select_ui(
            screen, options, selected, sel_font, hint_font
        )
        pygame.display.flip()

# ================= PAUSE MENU =================
def pause_menu(frozen_frame=None):
    """Blocking loop — the game is fully frozen while this runs because
    no update() calls happen here, only drawing the captured frozen frame.

    Returns a tuple: (result, frozen_frame)
      result        — one of: 'resume' | 'select' | 'settings' | 'menu'
      frozen_frame  — the captured gameplay snapshot used as this pause
                       menu's background. Pass it back into the NEXT
                       pause_menu() call (e.g. after Settings/Character
                       Select returns) so the background stays the
                       original gameplay frame instead of being re-captured
                       from whatever screen is currently drawn.

    To replace placeholder buttons with your own assets later:
    - Replace draw_pause_btn() with a blit of your own button sprite.
    - The rect objects (resume_rect, select_rect, settings_rect, menu_rect)
      control hit areas and stay the same regardless of how you draw the buttons.
    - The frozen_frame capture and overlay fill stay the same.

    frozen_frame param: optional pre-captured snapshot of the game scene.
    If omitted, the current screen contents are captured (used for the very
    first open, when the screen still shows live gameplay).
    """
    # Capture the exact pixel state of the screen at the moment pause was pressed.
    # This is blitted every frame of the pause loop so the game scene shows through.
    if frozen_frame is None:
        frozen_frame = screen.copy()

    # Semi-transparent dark overlay — change the 4th value (0-255) to adjust darkness.
    # 160 ≈ 63% opacity, enough to darken without completely hiding the scene.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))

    # ---- Pause menu layout ----
    btn_w, btn_h = 280, 60
    btn_x  = WIDTH  // 2 - btn_w // 2
    gap    = 76   # vertical distance between button centers
    # Order: Resume → Character Selection → Settings → Main Menu
    resume_rect   = pygame.Rect(btn_x, HEIGHT // 2 - gap * 1.5, btn_w, btn_h)
    select_rect   = pygame.Rect(btn_x, HEIGHT // 2 - gap * 0.5, btn_w, btn_h)
    settings_rect = pygame.Rect(btn_x, HEIGHT // 2 + gap * 0.5, btn_w, btn_h)
    menu_rect     = pygame.Rect(btn_x, HEIGHT // 2 + gap * 1.5, btn_w, btn_h)

    # Pause menu now uses the game's custom pixel font instead of system Arial,
    # so it matches the rest of the UI (HUD, timer panel, dialog box, etc).
    pause_title_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 48)
    pause_btn_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 26)

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
                    return "resume", frozen_frame

            # Mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_rect.collidepoint(mouse_pos):
                    return "resume", frozen_frame
                if select_rect.collidepoint(mouse_pos):
                    return "select", frozen_frame
                if settings_rect.collidepoint(mouse_pos):
                    return "settings", frozen_frame
                if menu_rect.collidepoint(mouse_pos):
                    return "menu", frozen_frame

            # Touch tap directly on pause menu buttons
            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if resume_rect.collidepoint(tx, ty):
                    return "resume", frozen_frame
                if select_rect.collidepoint(tx, ty):
                    return "select", frozen_frame
                if settings_rect.collidepoint(tx, ty):
                    return "settings", frozen_frame
                if menu_rect.collidepoint(tx, ty):
                    return "menu", frozen_frame

        # Pressing the pause button again resumes (one-shot flag consumed here)
        if mobile_controls.pause_just_pressed:
            mobile_controls.pause_just_pressed = False
            return "resume", frozen_frame

        # ---- Draw: frozen game → dark overlay → pause UI ----
        screen.blit(frozen_frame, (0, 0))
        screen.blit(overlay,      (0, 0))

        title = pause_title_font.render("PAUSED", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 160))

        draw_pause_btn(resume_rect,   "Resume",              resume_rect.collidepoint(mouse_pos))
        draw_pause_btn(select_rect,   "Character Selection", select_rect.collidepoint(mouse_pos))
        draw_pause_btn(settings_rect, "Settings",             settings_rect.collidepoint(mouse_pos))
        draw_pause_btn(menu_rect,     "Main Menu",           menu_rect.collidepoint(mouse_pos))

        # Draw only the pause button itself — joystick/ATK/DASH are hidden
        pause_spr = mobile_controls._btn_pause_active \
                    if mobile_controls.btn_pause_pressed \
                    else mobile_controls._btn_pause_idle
        px, py = mobile_controls.btn_pause_center
        screen.blit(pause_spr, (px - PAUSE_BTN_SIZE // 2, py - PAUSE_BTN_SIZE // 2))

        pygame.display.flip()


# ================= SETTINGS MENU (from pause) =================
def settings_menu():
    """
    Lets the player drag the joystick / ATK / DASH buttons anywhere they like.
    The pause button is intentionally NOT repositionable here — it always
    stays fixed top-center.

    Layout changes take effect IMMEDIATELY (live, in-memory) the moment the
    player drags a control — there's no need to Save or restart the game to
    see the new position. "Save" only persists the layout to disk
    (assets2/controls_layout.json) so it's remembered the NEXT time the game
    is launched; "Reset Default" snaps back to the built-in default
    positions (also live, immediately).

    Returns to the pause menu when the player presses Back/ESC. Whatever
    layout is active at that moment keeps being used in-game right away.
    """
    # Settings menu also uses the custom pixel font now, to match the rest of the UI.
    title_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 40)
    btn_font    = pygame.font.Font("assets2/font/A Friend In Deed.otf", 24)
    hint_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 18)

    btn_w, btn_h = 170, 50
    gap = 16
    total_w = btn_w * 3 + gap * 2
    start_x = WIDTH // 2 - total_w // 2
    btn_y   = 20

    save_rect  = pygame.Rect(start_x,                      btn_y, btn_w, btn_h)
    reset_rect = pygame.Rect(start_x + (btn_w + gap),       btn_y, btn_w, btn_h)
    back_rect  = pygame.Rect(start_x + (btn_w + gap) * 2,   btn_y, btn_w, btn_h)

    BTN_IDLE   = (80,  80,  80)
    BTN_HOVER  = (130, 130, 130)
    BTN_TEXT   = (240, 240, 240)
    BTN_BORDER = (30,  30,  30)

    def draw_btn(rect, text, hovered):
        color = BTN_HOVER if hovered else BTN_IDLE
        pygame.draw.rect(screen, BTN_BORDER, rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(screen, color,      rect,               border_radius=7)
        label = btn_font.render(text, True, BTN_TEXT)
        screen.blit(label, (rect.centerx - label.get_width()  // 2,
                             rect.centery - label.get_height() // 2))

    mobile_controls.start_edit_mode()

    save_flash_timer = 0  # frames remaining to show "Saved!" feedback text

    while True:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Back without saving to disk — but the in-memory layout the
                # player just dragged into place stays active immediately,
                # it is NOT reverted. Only "Reset Default" or relaunching the
                # game without ever pressing Save will lose it.
                mobile_controls.stop_edit_mode()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if save_rect.collidepoint(mouse_pos):
                    mobile_controls.save_layout()
                    save_flash_timer = FPS * 2  # show "Saved!" for ~2 seconds
                    continue
                if reset_rect.collidepoint(mouse_pos):
                    mobile_controls.reset_layout()
                    continue
                if back_rect.collidepoint(mouse_pos):
                    # Keep the dragged-into-place layout active immediately;
                    # only stop edit mode and return to the pause menu.
                    mobile_controls.stop_edit_mode()
                    return

            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if save_rect.collidepoint(tx, ty):
                    mobile_controls.save_layout()
                    save_flash_timer = FPS * 2
                    continue
                if reset_rect.collidepoint(tx, ty):
                    mobile_controls.reset_layout()
                    continue
                if back_rect.collidepoint(tx, ty):
                    # Keep the dragged-into-place layout active immediately;
                    # only stop edit mode and return to the pause menu.
                    mobile_controls.stop_edit_mode()
                    return

            # Everything else (drags on the joystick/ATK/DASH halos) goes to
            # mobile_controls' edit-mode handler.
            mobile_controls.handle_event(event)

        # ---- Draw ----
        screen.fill((25, 25, 30))

        title = title_font.render("Controls Settings", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 78))

        hint = hint_font.render(
            "Drag the joystick / ATK / DASH to reposition them.",
            True, (190, 190, 190)
        )
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 118))

        draw_btn(save_rect,  "Save",            save_rect.collidepoint(mouse_pos))
        draw_btn(reset_rect, "Reset Default",   reset_rect.collidepoint(mouse_pos))
        draw_btn(back_rect,  "Back",            back_rect.collidepoint(mouse_pos))

        # Draw the controls themselves (with edit-mode halos/labels)
        mobile_controls.draw(screen, show_pause=True)

        if save_flash_timer > 0:
            saved_label = btn_font.render("Saved!", True, GREEN)
            screen.blit(saved_label, (save_rect.centerx - saved_label.get_width() // 2,
                                       save_rect.bottom + 6))
            save_flash_timer -= 1

        pygame.display.flip()


# ================= CHARACTER SELECT FROM PAUSE =================
def character_select_from_pause():
    """Like character_select() but returns the chosen class instead of
    switching state directly — so game_loop stays in control of what happens next.
    Returns None if the player presses ESC to go back to the pause menu."""
    options = [
        {"class": Archer,  "card": card_arjuna,    "name": "Arjuna"},
        {"class": Spear,   "card": card_yudhistira, "name": "Yudhistira"},
        {"class": Hammer,  "card": card_bima,       "name": "Bima"},
        {"class": Assasin, "card": card_yudhistira, "name": "Assasin"},
    ]
    selected  = 0
    sel_font  = pygame.font.Font("assets2/font/A Friend In Deed.otf", 36)
    hint_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 16)

    left_rect  = pygame.Rect(0, 0, 1, 1)
    right_rect = pygame.Rect(0, 0, 1, 1)
    check_rect = pygame.Rect(0, 0, 1, 1)

    while True:
        clock.tick(FPS)
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
                    return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if left_rect.collidepoint(mx, my):
                    selected = (selected - 1) % len(options)
                elif right_rect.collidepoint(mx, my):
                    selected = (selected + 1) % len(options)
                elif check_rect.collidepoint(mx, my):
                    return options[selected]["class"]

            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if left_rect.collidepoint(tx, ty):
                    selected = (selected - 1) % len(options)
                elif right_rect.collidepoint(tx, ty):
                    selected = (selected + 1) % len(options)
                elif check_rect.collidepoint(tx, ty):
                    return options[selected]["class"]

        left_rect, right_rect, check_rect = _draw_character_select_ui(
            screen, options, selected, sel_font, hint_font
        )
        # ESC hint (khusus from-pause)
        esc_surf = pygame.font.Font("assets2/font/A Friend In Deed.otf", 15).render(
            "ESC — kembali ke pause", True, (120, 120, 120)
        )
        screen.blit(esc_surf, (8, HEIGHT - 18))
        pygame.display.flip()


# ================= RESTART FROM PAUSE =================
def restart_from_pause(new_player_class):
    """Switches the player character without resetting the relic.
    Resets enemies and phase timer, spawns player at the default position."""
    global player, players, phase, phase_frames, bg_game, current_bg, enemy_respawn_timer
    player = new_player_class(*SPAWN_POS)
    player.mobile_controls = mobile_controls
    player.honor_system    = honor_system
    players = pygame.sprite.Group(player)
    broadcast_character(player)
    player_hud.set_character(player.__class__.__name__)
    # Reset to fight phase and map 1
    phase        = "lobby"
    phase_frames = LOBBY_DURATION * FPS
    bg_game      = bg_map1
    current_bg   = 1
    # Reset enemies
    enemies.empty()
    enemies.add(Enemy(*enemy_spawn_pos))
    enemy_respawn_timer = 0


# ================= FULL RESET (setelah mati) =================
def full_reset():
    """
    Reset SEMUA state permainan ke kondisi awal — dipanggil setelah player
    mati dan memilih 'Play Again', sebelum masuk ke character select.

    Yang di-reset:
    - Phase → lobby (fight), timer diulang dari awal
    - Map → kembali ke map 1
    - Enemies → semua mati, satu musuh baru di spawn pos
    - Relic & Portal → generate ulang (baru & random)
    - Relic notif timer → 0
    - Water count → 0
    - Arrows → kosong
    - Dialog box → ditutup paksa
    - Enemy respawn timer → 0
    """
    global phase, phase_frames, bg_game, current_bg
    global enemies, enemy_respawn_timer
    global relic, portal, relic_notif_timer
    global water_count, arrows

    # Phase & map
    phase        = "lobby"
    phase_frames = LOBBY_DURATION * FPS
    bg_game      = bg_map1
    current_bg   = 1

    # Enemies — hapus semua, spawn satu musuh baru dengan HP penuh
    enemies.empty()
    enemies.add(Enemy(*enemy_spawn_pos))
    enemy_respawn_timer = 0

    # Relic & Portal — generate ulang supaya fresh
    relic  = generate_relic()
    portal = generate_portal_resi()
    relic_notif_timer = 0
    print(f"[FULL RESET] Relic baru: '{relic['name']}' di Map {relic['map']}")
    print(f"[FULL RESET] Portal Resi baru di Map {portal['map']}")

    # Bersihkan panah & dialog
    arrows.empty()
    dialog_box.close()
    dialog_box.player_relics.clear()   # reset koleksi prasasti player
    honor_system.reset()               # reset honor ke titik seimbang (0)
    covenant_npc.hide()                # sembunyikan NPC
    ritual_system.covenant_made = False
    ritual_system.stop()

    # Currency
    water_count = 0


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
    # Covenant NPC — muncul saat fight phase jika perjanjian sudah dibuat
    if ritual_system.covenant_made:
        covenant_npc.place_random(map_id=1)
        ritual_system.start_timer()

def start_explore():
    global phase, phase_frames, bg_game, current_bg
    phase        = "explore"
    phase_frames = EXPLORE_DURATION * FPS
    bg_game      = bg_map2
    current_bg   = 2
    player.rect.center = BG2_SPAWN_POS
    enemies.empty()
    # NPC muncul di explore phase hanya sebelum perjanjian dibuat
    if not ritual_system.covenant_made:
        covenant_npc.place_random(map_id=2)
        covenant_npc.tiger_hidden = False
    else:
        covenant_npc.hide()
    ritual_system.stop()


# ================= APPLY DIALOG ACTION =================
def apply_dialog_action(action_key):
    """
    Dipanggil dari game_loop setiap kali dialog box ditutup dan node
    terakhir yang ditampilkan memiliki field "action".
    Membaca PRASASTI_BUFFS dari dialog_system untuk menentukan buff-nya.
    """
    global player
    if not action_key or action_key not in PRASASTI_BUFFS:
        return

    buff = PRASASTI_BUFFS[action_key]

    # Healing — pulihkan HP penuh
    if buff.get("heal_full"):
        player.health = player.max_health
        healing_aura.trigger(player.rect.centerx, player.rect.top)
        print(f"[DIALOG ACTION] Healing: HP dipulihkan ke {player.max_health}")
        return

    # Stat upgrade
    dmg_up   = buff.get("damage", 0)
    speed_up = buff.get("speed",  0)

    if dmg_up:
        player.damage += dmg_up
        print(f"[DIALOG ACTION] {action_key}: damage +{dmg_up} → {player.damage}")

    if speed_up:
        player.speed += speed_up
        print(f"[DIALOG ACTION] {action_key}: speed +{speed_up:.1f} → {player.speed:.1f}")

    # Trigger VFX aura sesuai prasasti yang digunakan
    _aura_theme = {
        "upgrade_strength_bima":    "gold",
        "upgrade_arjuna":           "green",
        "upgrade_speed_nakula":     "purple",
        "upgrade_speed_yudhistira": "cyan",
        "upgrade_strength_sadewa":  "teal",
    }
    theme = _aura_theme.get(action_key)
    if theme:
        upgrade_aura.trigger(player.rect.centerx, player.rect.centery, theme=theme)

# ================= DEATH SCREEN =================
def death_screen():
    death_title_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 100)
    death_sub_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 32)
    death_btn_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 28)

    btn_w, btn_h = 240, 60
    cx = WIDTH  // 2
    cy = HEIGHT // 2

    play_again_rect = pygame.Rect(cx - btn_w - 20, cy + 80, btn_w, btn_h)
    quit_rect       = pygame.Rect(cx + 20,          cy + 80, btn_w, btn_h)

    # Fade-in timer
    fade_alpha = 0

    # Overlay gelap
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))

    # Ambil snapshot gameplay sebagai latar
    snapshot = screen.copy()

    clock_ds = pygame.time.Clock()

    while True:
        clock_ds.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_again_rect.collidepoint(mouse_pos):
                    return "restart"
                if quit_rect.collidepoint(mouse_pos):
                    return "quit"

            if event.type == pygame.FINGERDOWN:
                tx = int(event.x * WIDTH)
                ty = int(event.y * HEIGHT)
                if play_again_rect.collidepoint(tx, ty):
                    return "restart"
                if quit_rect.collidepoint(tx, ty):
                    return "quit"

        # Fade in overlay
        if fade_alpha < 210:
            fade_alpha = min(210, fade_alpha + 4)

        # ── Draw ──────────────────────────────────────────────────
        screen.blit(snapshot, (0, 0))

        overlay.set_alpha(fade_alpha)
        screen.blit(overlay, (0, 0))

        # "YOU ARE DEAD" — merah tebal dengan shadow
        dead_shadow = death_title_font.render("YOU ARE DEAD", True, (80, 0, 0))
        dead_text   = death_title_font.render("YOU ARE DEAD", True, (220, 30, 30))
        dead_rect   = dead_text.get_rect(center=(cx, cy - 60))
        screen.blit(dead_shadow, (dead_rect.x + 4, dead_rect.y + 4))
        screen.blit(dead_text,   dead_rect)

        # Sub-text
        sub_surf = death_sub_font.render("Perjalananmu berakhir di sini, pendekar...", True, (200, 150, 150))
        screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 20)))

        # ── Tombol Play Again ─────────────────────────────────────
        pa_hover  = play_again_rect.collidepoint(mouse_pos)
        pa_color  = (40, 160, 80)  if pa_hover else (25, 100, 50)
        pa_border = (80, 255, 120) if pa_hover else (50, 150, 75)
        pygame.draw.rect(screen, pa_border, play_again_rect.inflate(4, 4), border_radius=10)
        pygame.draw.rect(screen, pa_color,  play_again_rect,               border_radius=9)
        pa_surf = death_btn_font.render("▶  Play Again", True, WHITE)
        screen.blit(pa_surf, pa_surf.get_rect(center=play_again_rect.center))

        # ── Tombol Quit ───────────────────────────────────────────
        q_hover  = quit_rect.collidepoint(mouse_pos)
        q_color  = (160, 40, 40) if q_hover else (100, 25, 25)
        q_border = (255, 80, 80) if q_hover else (150, 50, 50)
        pygame.draw.rect(screen, q_border, quit_rect.inflate(4, 4), border_radius=10)
        pygame.draw.rect(screen, q_color,  quit_rect,               border_radius=9)
        q_surf = death_btn_font.render("✕  Quit", True, WHITE)
        screen.blit(q_surf, q_surf.get_rect(center=quit_rect.center))

        pygame.display.flip()


# ================= GAME LOOP =================
def game_loop():
    global state, enemy_respawn_timer, player, players
    global arrows, bg_game, current_bg
    global phase, phase_frames
    global relic_notif_timer
    global water_count
    global relic, portal

    # Track action dari node dialog terakhir yang punya "action" field
    last_dialog_action = None
    prev_dialog_active = False

    while state == "game":
        clock.tick(FPS)

        # ================= DETEKSI KEMATIAN PLAYER =================
        if player.health <= 0:
            result = death_screen()
            if result == "quit":
                pygame.quit(); sys.exit()
            else:  # "restart" → reset semua lalu ke character select
                full_reset()
                state = "select"
                return

        # ================= APPLY DIALOG ACTION (saat dialog baru saja ditutup) =====
        # Cek apakah dialog baru saja ditutup frame ini
        if prev_dialog_active and not dialog_box.active:
            if last_dialog_action:
                apply_dialog_action(last_dialog_action)
                last_dialog_action = None
        prev_dialog_active = dialog_box.active

        # Rekam action dari node aktif saat dialog sedang berjalan
        if dialog_box.active:
            node = dialog_box._current_node()
            if node and "action" in node:
                last_dialog_action = node["action"]

        # ================= TICK PHASE TIMER =================
        # Dialog yang aktif membekukan timer fase juga, supaya waktu lobby/explore
        # tidak terus berkurang selama player sedang baca dialog.
        if not dialog_box.active:
            if phase_frames > 0:
                phase_frames -= 1
            else:
                if phase == "lobby":
                    # ── Fight phase selesai → generate relic & portal baru ──
                    relic  = generate_relic()
                    portal = generate_portal_resi()
                    print(f"[PHASE] Fight selesai! Relic baru: '{relic['name']}' di Map {relic['map']}")
                    print(f"[PHASE] Portal Resi baru di Map {portal['map']}")
                    start_explore()
                else:
                    start_lobby()

        # ================= EVENTS =================
        pressed_e     = False
        pressed_m     = False
        should_pause  = False
        boost_pressed = False
        # Posisi tombol BOOST/ULT (khusus Archer/Arjuna) — tengah bawah layar.
        # Dihitung di sini supaya bisa dipakai untuk deteksi klik/touch di
        # loop event di bawah.
        boost_btn_w, boost_btn_h = 100, 36
        boost_btn_rect = pygame.Rect(
            WIDTH // 2 - boost_btn_w // 2,
            HEIGHT - boost_btn_h - 16,
            boost_btn_w,
            boost_btn_h,
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # PRIORITAS UTAMA: kalau dialog box aktif, dia yang menyerap
            # event ini duluan (UP/DOWN navigasi opsi, E/Enter konfirmasi, ESC tutup).
            # Tanpa blok ini, dialog_box.handle_event() TIDAK PERNAH terpanggil
            # di dalam game_loop, makanya dialog kelihatan "tidak bisa diapa-apain".
            if dialog_box.active:
                dialog_box.handle_event(event)
                continue

            mobile_controls.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    should_pause = True
                if event.key == pygame.K_e:
                    pressed_e = True
                if event.key == pygame.K_m:
                    pressed_m = True
                if event.key == pygame.K_y:
                    print(f"Player position: x={player.rect.centerx}, y={player.rect.centery}")

            # Tombol BOOST/ULT — diecek di SINI (langsung di event loop utama),
            # bukan lewat pygame.event.get(TYPE) lagi belakangan, karena loop
            # ini sudah "mengambil semua" event dari queue duluan. Kalau dicek
            # ulang nanti, queue-nya sudah kosong dan tombolnya tidak akan
            # merespons klik/sentuhan sama sekali (tombol MAP kena masalah ini).
            if hasattr(player, "activate_ultimate"):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if boost_btn_rect.collidepoint(event.pos):
                        boost_pressed = True
                elif event.type == pygame.FINGERDOWN:
                    tbx = int(event.x * WIDTH); tby = int(event.y * HEIGHT)
                    if boost_btn_rect.collidepoint(tbx, tby):
                        boost_pressed = True


        mobile_controls.update()

        if dialog_box.active:
            # Saat dialog Resi aktif, gunakan bg_resi sebagai latar
            # (bukan abu-abu polos) supaya suasana lebih atmosferik.
            screen.blit(bg_resi, (0, 0))
            dialog_box.draw(screen)
            # NOTE: mobile_controls.draw() intentionally NOT called here —
            # joystick/ATK/DASH/pause are hidden while a dialog is open so
            # they don't visually clutter or get accidentally pressed
            # underneath the dialog box.
            pygame.display.flip()
            continue 

        # Touch pause button check (one-shot flag set by mobile_controls)
        if mobile_controls.pause_just_pressed:
            mobile_controls.pause_just_pressed = False
            should_pause = True

        if should_pause:
            result, frozen_frame = pause_menu()
            # Loop here so "Back" from Settings returns to the SAME pause
            # menu screen (same frozen background) instead of capturing a
            # new frozen_frame from the settings UI that's currently drawn.
            while result == "settings":
                settings_menu()
                result, frozen_frame = pause_menu(frozen_frame)
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

        player.rect.clamp_ip(screen.get_rect())

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

        # ================= REWARD: +1 WATER SAAT MUSUH MATI =================
        for enemy in enemies:
            if getattr(enemy, "just_died", False):
                water_count += 1
                enemy.just_died = False

        # ================= COVENANT NPC INTERACTION ==========
        if covenant_npc.visible and covenant_npc.map_id == current_bg:
            # Update ritual timer → mungkin spawn Enemy2 punishment
            new_punish = ritual_system.update(player, enemies, water_count)
            for pe in new_punish:
                enemies.add(pe)

            # Cek interaksi player dengan NPC
            if covenant_npc.near_player(player) and pressed_e and not show_interact:
                if not ritual_system.covenant_made:
                    # Belum ada perjanjian — tampilkan dialog perjanjian
                    result = do_covenant_dialog(
                        screen, clock, FPS, pixel_font, small_font)
                    if result == "accept":
                        ritual_system.covenant_made = True
                        # Buff player: +20 max HP, +1 damage
                        player.max_health += 20
                        player.health     = min(player.health + 20, player.max_health)
                        player.damage     += 1
                        # Mulai timer ritual
                        covenant_npc.place_random(map_id=1)
                        ritual_system.start_timer()
                        print("[COVENANT] Perjanjian diterima! HP+20, Damage+1")
                else:
                    # Perjanjian sudah ada — cek ritual siram pohon
                    if covenant_npc.near_tree(player):
                        used = do_ritual_minigame(
                            screen, clock, FPS, pixel_font, small_font, water_count)
                        if used > 0:
                            water_count -= used
                            ritual_system.reset_timer()
                            print(f"[RITUAL] Berhasil! Timer direset. Air sisa: {water_count}")

        # ================= ENEMY ATTACK =================
        for enemy in enemies:
            atk = enemy.get_attack_hitbox()
            if atk and atk.colliderect(player.rect):
                # Punishment enemy punya damage lebih tinggi
                dmg = getattr(enemy, "_punishment_damage", 1)
                player.take_damage(dmg)

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
                    # Catat kepemilikan relic ke dialog_box supaya Resi bisa
                    # memvalidasi sebelum menerima penukaran prasasti.
                    dialog_box.player_relics.add(relic["name"])
                    print(f"[RELIC] '{relic['name']}' berhasil diambil! Koleksi: {dialog_box.player_relics}")

        # ================= PORTAL RESI INTERACTION =================
        # Terpisah dari relic biasa: tidak pernah "collected", jadi bisa
        # ditekan E berkali-kali untuk membuka dialog box lagi.
        near_portal = False
        if portal["map"] == current_bg:
            portal_pickup_range = pygame.Rect(portal["pos"][0] - 60, portal["pos"][1] - 60, 120, 120)
            if player.rect.colliderect(portal_pickup_range):
                near_portal = True
                if pressed_e and not show_interact:
                    dialog_box.open(
                        RESI_DIALOG_TREE,
                        start_key="start",
                        npc_portrait="assets2/resi_abimayasa.png",
                    )

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
            # Spawn NPC di map baru saat explore phase (hanya sebelum perjanjian)
            if phase == "explore" and not ritual_system.covenant_made:
                covenant_npc.place_random(map_id=current_bg)
                covenant_npc.tiger_hidden = False

        # ================= ENEMY RESPAWN (lobby only) =================
        if phase == "lobby":
            if len(enemies) == 0:
                enemy_respawn_timer += 1
                if enemy_respawn_timer >= RESPAWN_DELAY:
                    enemies.add(Enemy(*enemy_spawn_pos))
                    enemy_respawn_timer = 0
        else:
            enemy_respawn_timer = 0

        # ═══ DRAW ═══════════════════════════════════════════════════════
        screen.blit(bg_game, (0, 0))

        enemies.draw(screen)
        for enemy in enemies:
            enemy.draw_healthbar(screen)

        # Covenant NPC (pohon + harimau) — fight phase & explore phase
        if covenant_npc.visible and covenant_npc.map_id == current_bg:
            covenant_npc.draw(screen)
            near_tree_for_ritual = (ritual_system.covenant_made and
                                    covenant_npc.near_tree(player))
            covenant_npc.draw_prompt(
                screen, player, small_font, GOLD, WHITE,
                covenant_made=ritual_system.covenant_made,
                near_tree=near_tree_for_ritual,
            )

        # ← RELIC & PORTAL RESI DIGAMBAR DI SINI
        draw_relic()
        draw_portal()

        player.draw(screen)

        # Aura hijau healing — update posisi ke player, lalu update & gambar
        healing_aura.update_origin(player.rect.centerx, player.rect.top)
        healing_aura.update()
        healing_aura.draw(screen)

        upgrade_aura.update_origin(player.rect.centerx, player.rect.centery)
        upgrade_aura.update()
        upgrade_aura.draw(screen)

        arrows.draw(screen)

        # Portal map-transition prompt (gerbang pindah map, BUKAN Portal Resi)
        if show_interact:
            if portal_open:
                msg = pixel_font.render("Press E", True, WHITE)
            else:
                msg = pixel_font.render("Portal locked!", True, RED)
            screen.blit(msg, (player.rect.centerx - msg.get_width() // 2,
                               player.rect.top - 44))

        # Relic prompt (hanya jika tidak overlap dengan gerbang pindah map)
        if near_relic and not show_interact:
            draw_relic_prompt()

        # Portal Resi prompt (hanya jika tidak overlap dengan gerbang pindah map)
        if near_portal and not show_interact:
            draw_portal_prompt()

        # Notifikasi pickup
        draw_relic_notif()

        draw_timer_panel()

        # Honor bar — di bawah timer panel, pojok kanan atas
        honor_system.draw_hud(screen, WIDTH - 240, 100, width=230)

        # Ritual timer — pojok kiri bawah (hanya saat fight phase & covenant aktif)
        if phase == "lobby":
            ritual_system.draw_timer(screen, pixel_font, small_font)

        player_hud.draw(screen, player.health, player.max_health,
                         stamina_ratio_from_dash(player), water_count)

        # ── Tombol MAP (hanya saat fase explore) ──────────────────────
        # Tombol kecil di pojok kanan bawah, di atas mobile controls.
        if phase == "explore":
            map_btn_rect = pygame.Rect(WIDTH - 110, HEIGHT - 48, 100, 36)
            map_mouse_hov = map_btn_rect.collidepoint(pygame.mouse.get_pos())
            _draw_menu_btn(screen, small_font, "🗺  MAP", map_btn_rect, map_mouse_hov)

            # Cek klik mouse pada tombol MAP
            for _ev in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                if _ev.button == 1 and map_btn_rect.collidepoint(_ev.pos):
                    pressed_m = True
            # Cek touch pada tombol MAP
            for _ev in pygame.event.get(pygame.FINGERDOWN):
                tx2 = int(_ev.x * WIDTH); ty2 = int(_ev.y * HEIGHT)
                if map_btn_rect.collidepoint(tx2, ty2):
                    pressed_m = True

            if pressed_m:
                show_map_overlay(current_bg)

        # ── Tombol BOOST / ULTIMATE / RAGE (khusus Archer/Arjuna) ──────
        # Tengah bawah layar — tetap kelihatan di kedua fase (lobby & explore).
        # Tombol yang SAMA berubah fungsi tergantung state:
        #   1. "🔥 AKTIF!"  — ultimate biasa sedang berjalan
        #   2. "⏳ Xs"      — masih cooldown
        #   3. "💢 RAGE!"   — window RAGE terbuka (5 detik setelah cooldown
        #                     ultimate biasa habis) — kalau dipencet di sini,
        #                     boost LEBIH BESAR tapi honor turun (adharma naik)
        #   4. "⚡ ULT"     — siap pakai (ultimate biasa)
        if hasattr(player, "activate_ultimate"):
            boost_hover = boost_btn_rect.collidepoint(pygame.mouse.get_pos())

            in_rage_window = getattr(player, "rage_window_active", False)
            in_rage_active = getattr(player, "rage_active", False)

            if player.ultimate_active or in_rage_active:
                boost_label = "🔥 AKTIF!"
            elif in_rage_window:
                boost_label = "💢 RAGE!"
            elif player.ultimate_cooldown_timer > 0:
                cd_left     = player.ultimate_cooldown_timer // FPS + 1
                boost_label = f"⏳ {cd_left}s"
            else:
                boost_label = "⚡ ULT"

            _draw_menu_btn(screen, small_font, boost_label, boost_btn_rect, boost_hover)

            if boost_pressed:
                if in_rage_window and hasattr(player, "activate_rage"):
                    player.activate_rage()
                else:
                    player.activate_ultimate()

        # Virtual joystick + attack/dash + pause button (drawn last = on top)
        # show_pause=True makes all controls visible; they are hidden on other screens
        # because draw() is not called at all in main_menu() or character_select().
        mobile_controls.draw(screen, show_pause=True)

        # Banner "Boost!" ultimate Arjuna / "RAGE!" — digambar paling akhir
        # supaya muncul di atas semua elemen lain (HUD, mobile controls, dll).
        if hasattr(player, "draw_ultimate_banner"):
            player.draw_ultimate_banner(screen)
        if hasattr(player, "draw_rage_banner"):
            player.draw_rage_banner(screen)

        pygame.display.flip()

# ================= RUN =================
while True:
    if state == "menu":
        main_menu()
    elif state == "select":
        character_select()
    elif state == "game":
        game_loop()