import pygame
import random
import math
import os

# ── Warna ──────────────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GOLD   = (255, 210,  60)
GREEN  = (80,  220, 140)
RED    = (220,  60,  60)
ORANGE = (255, 160,  40)
BLUE   = (80,  160, 255)
TEAL   = (40,  200, 200)

# ── Asset loader ───────────────────────────────────────────────────────
_ASSET_CACHE: dict = {}

def _load(path: str, size: tuple | None = None) -> pygame.Surface:
    key = (path, size)
    if key not in _ASSET_CACHE:
        try:
            img = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            # Fallback: kotak merah kalau file tidak ada
            img = pygame.Surface((64, 64), pygame.SRCALPHA)
            img.fill((180, 40, 40, 200))
        if size:
            img = pygame.transform.scale(img, size)
        _ASSET_CACHE[key] = img
    return _ASSET_CACHE[key]


# ════════════════════════════════════════════════════════════════════════
#  CovenantNPC — harimau + pohon yang selalu spawn berdampingan
# ════════════════════════════════════════════════════════════════════════
class CovenantNPC:
    """
    Harimau roh dan pohon sakral muncul berdampingan di fight phase.
    Pohon selalu di kiri, harimau di kanan (keduanya saling overlap sedikit
    agar terlihat natural).

    Atribut penting:
        visible     : True kalau sedang muncul di map saat ini
        map_id      : map berapa NPC ini ditempatkan (1–5)
        tree_rect   : rect pohon (untuk ritual cek jarak)
        tiger_rect  : rect harimau (untuk dialog cek jarak)
    """

    _TIGER_SIZE = (120, 106)   # scale down dari 467×413
    _TREE_SIZE  = (128, 196)   # diperbesar 2x dari sebelumnya (64×98)

    # Posisi kandidat di map 1 (fight phase selalu di map 1)
    _SPAWN_CANDIDATES = [
        (200, 300), (700, 300), (400, 200), (300, 380), (600, 250),
    ]

    def __init__(self):
        self.tiger_img = _load(
            "assets2/frame_0000.png", self._TIGER_SIZE)   # full body — spawn di map
        self.tree_img  = _load(
            "assets2/covenant_tree.png",  self._TREE_SIZE)

        self.visible      = False
        self.tiger_hidden = False   # True saat Enemy2 punishment aktif di map
        self.map_id    = 1
        self.cx        = 0    # center x titik spawn (antara pohon dan harimau)
        self.cy        = 0

        # Rect untuk collision/proximity check
        self.tree_rect  = pygame.Rect(0, 0, *self._TREE_SIZE)
        self.tiger_rect = pygame.Rect(0, 0, *self._TIGER_SIZE)

        # Efek pulse ringan pada pohon
        self._pulse = 0.0

    def place(self, cx: int, cy: int, map_id: int = 1):
        """Tempatkan NPC di posisi (cx, cy)."""
        self.cx      = cx
        self.cy      = cy
        self.map_id  = map_id
        self.visible = True
        self._update_rects()

    def place_random(self, map_id: int = 1):
        pos = random.choice(self._SPAWN_CANDIDATES)
        self.place(pos[0], pos[1], map_id)

    def hide(self):
        self.visible = False

    def _update_rects(self):
        # Pohon: sedikit di kiri cx
        tree_x = self.cx - self._TREE_SIZE[0] // 2 - 30
        tree_y = self.cy - self._TREE_SIZE[1] + 20
        self.tree_rect  = pygame.Rect(tree_x, tree_y, *self._TREE_SIZE)

        # Harimau: sedikit di kanan cx, lebih bawah agar kakinya sejajar
        tiger_x = self.cx + 10
        tiger_y = self.cy - self._TIGER_SIZE[1] + 20
        self.tiger_rect = pygame.Rect(tiger_x, tiger_y, *self._TIGER_SIZE)

    def near_player(self, player, radius: int = 80) -> bool:
        if not self.visible:
            return False
        center = (self.cx, self.cy)
        dx = player.rect.centerx - center[0]
        dy = player.rect.centery - center[1]
        return (dx * dx + dy * dy) <= radius * radius

    def near_tree(self, player, radius: int = 70) -> bool:
        """True kalau player dekat pohon (untuk ritual siram)."""
        if not self.visible:
            return False
        tx = self.tree_rect.centerx
        ty = self.tree_rect.centery
        dx = player.rect.centerx - tx
        dy = player.rect.centery - ty
        return (dx * dx + dy * dy) <= radius * radius

    def draw(self, screen: pygame.Surface):
        if not self.visible:
            return
        self._pulse = (self._pulse + 2) % 360
        # Pohon selalu digambar
        screen.blit(self.tree_img, self.tree_rect.topleft)
        # Harimau hanya muncul kalau tidak sedang bersembunyi (Enemy2 belum spawn)
        if not self.tiger_hidden:
            screen.blit(self.tiger_img, self.tiger_rect.topleft)

    def draw_timer_above_tree(self, screen: pygame.Surface,
                               title_font: pygame.font.Font,
                               small_font: pygame.font.Font,
                               timer_frames: int, timer_secs: int, fps: int):
        """Gambar countdown timer di atas pohon."""
        if not self.visible:
            return

        secs_left = max(0, timer_frames // fps)
        ratio     = timer_frames / (timer_secs * fps)

        # Warna: hijau → kuning → merah
        if ratio > 0.5:
            r = int(255 * (1 - ratio) * 2)
            col = (r, 220, 60)
        else:
            col = (255, int(200 * ratio * 2), 40)
        if secs_left <= 3:
            col = (220, 60, 60)

        # Posisi di atas pohon
        tx = self.tree_rect.centerx
        ty = self.tree_rect.top - 50

        # Panel kecil di atas pohon
        panel_w, panel_h = 110, 42
        px = tx - panel_w // 2
        py = ty - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 6, 20, 200))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, col, (px, py, panel_w, panel_h), 2, border_radius=6)

        lbl  = small_font.render("Ritual:", True, (200, 200, 200))
        time = title_font.render(f"{secs_left}s", True, col)
        screen.blit(lbl,  (px + 6, py + 4))
        screen.blit(time, (px + panel_w - time.get_width() - 6, py + 4))

        # Bar progress di bawah teks
        bar_x = px + 4
        bar_y = py + panel_h - 10
        bar_w = panel_w - 8
        bar_h = 6
        filled = int(bar_w * ratio)
        pygame.draw.rect(screen, (40, 35, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if filled > 0:
            pygame.draw.rect(screen, col, (bar_x, bar_y, filled, bar_h), border_radius=3)

    def draw_prompt(self, screen: pygame.Surface, player,
                    font: pygame.font.Font,
                    gold_color, white_color,
                    covenant_made: bool = False,
                    near_tree: bool = False):
        """Tampilkan prompt interaksi di atas NPC."""
        if not self.visible:
            return

        if not self.near_player(player):
            return

        if covenant_made and near_tree:
            # Prompt ritual
            label = font.render("Press E — Ritual Air Suci", True, TEAL)
        elif not covenant_made:
            label = font.render("Press E — Perjanjian Harimau", True, gold_color)
        else:
            label = font.render("Press E — Ritual Air Suci", True, TEAL)

        screen.blit(label, (
            self.cx - label.get_width() // 2,
            self.tiger_rect.top - 36,
        ))


# ════════════════════════════════════════════════════════════════════════
#  do_covenant_dialog — blocking loop dialog perjanjian
# ════════════════════════════════════════════════════════════════════════
_COVENANT_LINES = [
    ("Cindaku", "Pendekar... aku telah mengamatimu sejak lama."),
    ("Cindaku", "Aku menawarkan perjanjian: kekuatan dan umur panjang."),
    ("Cindaku", "Imbalannya sederhana — sirami pohon suci ini"),
    ("Cindaku", "dengan air dari jiwa musuh yang kau taklukkan."),
    ("Cindaku", "Setiap 15 detik pohon menuntut persembahanmu."),
    ("Cindaku", "Jika kau ingkar... aku tidak bisa menahan amarahnya."),
]

_COVENANT_REJECT_LINES = [
    ("Cindaku", "Hm. Kau memilih jalan yang lebih sulit."),
    ("Cindaku", "Baiklah. Tapi jika kau berubah pikiran... aku ada di sini."),
]


def do_covenant_dialog(screen: pygame.Surface, clock, fps: int,
                        title_font: pygame.font.Font,
                        body_font: pygame.font.Font,
                        tiger_img: pygame.Surface | None = None) -> str:
    """
    Blocking dialog perjanjian.
    Return "accept" atau "reject".
    """
    W, H = screen.get_size()
    frozen = screen.copy()

    # Load tiger portrait kalau belum
    if tiger_img is None:
        tiger_img = _load("assets2/covenant_tiger.png", (160, 141))

    choice_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 22)
    name_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 26)
    text_font   = pygame.font.Font("assets2/font/A Friend In Deed.otf", 20)

    phase   = "narration"   # "narration" → "choice"
    line_i  = 0
    selected = 0             # 0=accept, 1=reject
    choices  = [
        "✦ Terima perjanjian  (+20 HP, +1 Damage)",
        "✕ Tolak — aku tidak butuh bantuan roh",
    ]

    def draw_frame(lines_done: list[tuple], choice_phase: bool, sel: int):
        screen.blit(frozen, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (0, 0))

        # Panel dialog
        box_w, box_h = W - 80, 230
        box_x, box_y = 40, H - box_h - 20
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((10, 6, 20, 220))
        screen.blit(panel, (box_x, box_y))
        pygame.draw.rect(screen, ORANGE, (box_x, box_y, box_w, box_h), 2, border_radius=8)

        # Portrait harimau
        screen.blit(tiger_img, (box_x + 16, box_y + 16))
        pygame.draw.rect(screen, ORANGE,
                         (box_x + 16, box_y + 16,
                          tiger_img.get_width(), tiger_img.get_height()),
                         2, border_radius=6)

        tx = box_x + tiger_img.get_width() + 32

        if not choice_phase:
            # Tampilkan semua baris yang sudah "terungkap"
            if lines_done:
                spk, txt = lines_done[-1]
                name_s = name_font.render(spk, True, ORANGE)
                screen.blit(name_s, (tx, box_y + 14))
                # Wrap teks sederhana
                words = txt.split()
                line, lines_out = "", []
                for w in words:
                    test = line + (" " if line else "") + w
                    if text_font.size(test)[0] > box_w - tx - 50:
                        lines_out.append(line); line = w
                    else:
                        line = test
                if line:
                    lines_out.append(line)
                for i, l in enumerate(lines_out[:4]):
                    ts = text_font.render(l, True, WHITE)
                    screen.blit(ts, (tx, box_y + 48 + i * 26))

            hint = text_font.render("Tekan E / Enter untuk lanjut", True, (130, 120, 150))
            screen.blit(hint, (box_x + box_w - hint.get_width() - 10,
                               box_y + box_h - 24))
        else:
            # Pilihan
            q = name_font.render("Apa keputusanmu, pendekar?", True, GOLD)
            screen.blit(q, (tx, box_y + 14))
            for i, ch in enumerate(choices):
                color  = GOLD if i == sel else WHITE
                prefix = "➤ " if i == sel else "   "
                cs = choice_font.render(prefix + ch, True, color)
                screen.blit(cs, (tx, box_y + 60 + i * 36))
            hint = text_font.render("↑↓ pilih  |  E/Enter konfirmasi", True, (130, 120, 150))
            screen.blit(hint, (box_x + box_w - hint.get_width() - 10,
                               box_y + box_h - 24))

        pygame.display.flip()

    running = True
    result  = "reject"

    while running:
        clock.tick(fps)
        draw_frame(_COVENANT_LINES[:line_i + 1], phase == "choice", selected)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                import sys; pygame.quit(); sys.exit()

            confirm = False
            nav_dir = 0

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_e, pygame.K_RETURN):
                    confirm = True
                if event.key == pygame.K_DOWN:  nav_dir =  1
                if event.key == pygame.K_UP:    nav_dir = -1
                if event.key == pygame.K_ESCAPE:
                    running = False; break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                confirm = True

            if event.type == pygame.FINGERDOWN:
                confirm = True

            if phase == "narration":
                if confirm:
                    line_i += 1
                    if line_i >= len(_COVENANT_LINES):
                        phase = "choice"
                        line_i = len(_COVENANT_LINES) - 1
            else:
                selected = (selected + nav_dir) % len(choices)
                if confirm:
                    result  = "accept" if selected == 0 else "reject"
                    running = False

    return result


# ════════════════════════════════════════════════════════════════════════
#  do_ritual_minigame — minigame siram pohon (blocking)
# ════════════════════════════════════════════════════════════════════════
def do_ritual_minigame(screen: pygame.Surface, clock, fps: int,
                        title_font: pygame.font.Font,
                        body_font: pygame.font.Font,
                        water_count: int) -> int:
    """
    Minigame ritual — tekan E tepat saat lingkaran shrinking pas di zona target.
    Mirip Guitar Hero / timing circle.

    Return: jumlah air yang dipakai (1 kalau berhasil, 0 kalau gagal/batal).
    """
    W, H = screen.get_size()
    frozen = screen.copy()

    if water_count <= 0:
        # Tidak punya air — tampilkan pesan singkat
        _show_msg(screen, clock, fps, frozen,
                  "Kamu tidak punya Air Suci!",
                  "Bunuh musuh untuk mendapatkan Air Suci.",
                  RED)
        return 0

    choice_font = pygame.font.Font("assets2/font/A Friend In Deed.otf", 22)
    small2      = pygame.font.Font("assets2/font/A Friend In Deed.otf", 18)

    # ── Parameter lingkaran ──
    CENTER    = (W // 2, H // 2 - 30)
    TARGET_R  = 55     # radius zona target (kuning)
    START_R   = 140    # radius awal lingkaran shrinking (biru)
    SPEED     = 1.8    # piksel per frame yang dikurangi dari radius
    HIT_TOL   = 18     # toleransi hit (±18 dari TARGET_R)

    shrink_r = float(START_R)
    state    = "countdown"   # countdown → playing → result
    countdown = fps * 2      # 2 detik countdown
    result_timer = fps * 1   # 1 detik tampil hasil
    hit_result   = None      # None, "hit", "miss"
    water_used   = 0

    while True:
        clock.tick(fps)

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                import sys; pygame.quit(); sys.exit()

            if state == "playing":
                confirm = False
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    confirm = True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    confirm = True
                if event.type == pygame.FINGERDOWN:
                    confirm = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return 0   # batal

                if confirm:
                    diff = abs(shrink_r - TARGET_R)
                    if diff <= HIT_TOL:
                        hit_result   = "hit"
                        water_used   = 1
                    else:
                        hit_result   = "miss"
                    state = "result"

            elif state in ("countdown", "result"):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return 0

        # ── Update ──
        if state == "countdown":
            countdown -= 1
            if countdown <= 0:
                state = "playing"

        elif state == "playing":
            shrink_r -= SPEED
            if shrink_r < TARGET_R - HIT_TOL - 5:
                # Melewati zona → miss
                hit_result = "miss"
                state = "result"

        elif state == "result":
            result_timer -= 1
            if result_timer <= 0:
                return water_used

        # ── Draw ──
        screen.blit(frozen, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        screen.blit(dim, (0, 0))

        # Judul
        t = title_font.render("✦ RITUAL AIR SUCI ✦", True, TEAL)
        screen.blit(t, (W // 2 - t.get_width() // 2, 60))

        # Instruksi
        if state == "countdown":
            secs = countdown // fps + 1
            inst = choice_font.render(f"Bersiap... {secs}", True, GOLD)
        elif state == "playing":
            inst = choice_font.render("Tekan E saat lingkaran masuk zona kuning!", True, WHITE)
        else:
            if hit_result == "hit":
                inst = choice_font.render("✦ Berhasil! Pohon telah disiram.", True, GREEN)
            else:
                inst = choice_font.render("✕ Meleset! Air terbuang sia-sia.", True, RED)
        screen.blit(inst, (W // 2 - inst.get_width() // 2, 110))

        # Lingkaran target (zona kuning)
        pygame.draw.circle(screen, (60, 50, 10), CENTER, TARGET_R + HIT_TOL, 0)
        pygame.draw.circle(screen, GOLD,          CENTER, TARGET_R + HIT_TOL, 3)
        pygame.draw.circle(screen, (40, 160, 40), CENTER, TARGET_R - HIT_TOL, 3)

        # Lingkaran shrinking (biru → putih semakin dekat)
        if state == "playing":
            t_ratio = max(0, min(1, 1 - (shrink_r - TARGET_R) / (START_R - TARGET_R)))
            ring_col = (
                int(80  + t_ratio * 175),
                int(160 + t_ratio * 95),
                int(255 - t_ratio * 120),
            )
            pygame.draw.circle(screen, ring_col, CENTER, int(shrink_r), 4)

        # Ikon air suci di tengah
        water_txt = title_font.render(f"💧 {water_count}", True, BLUE)
        screen.blit(water_txt, (W // 2 - water_txt.get_width() // 2,
                                CENTER[1] - 18))

        hint = small2.render("ESC untuk batal", True, (100, 90, 120))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

        pygame.display.flip()


def _show_msg(screen, clock, fps, frozen, line1, line2, color, duration=120):
    """Tampilkan pesan singkat di tengah layar (blocking, duration frame)."""
    W, H = screen.get_size()
    f1 = pygame.font.Font("assets2/font/A Friend In Deed.otf", 26)
    f2 = pygame.font.Font("assets2/font/A Friend In Deed.otf", 20)
    for _ in range(duration):
        clock.tick(fps)
        screen.blit(frozen, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        screen.blit(dim, (0, 0))
        s1 = f1.render(line1, True, color)
        s2 = f2.render(line2, True, WHITE)
        screen.blit(s1, (W // 2 - s1.get_width() // 2, H // 2 - 30))
        screen.blit(s2, (W // 2 - s2.get_width() // 2, H // 2 + 10))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                import sys; pygame.quit(); sys.exit()
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                return


# ════════════════════════════════════════════════════════════════════════
#  TreeRitualSystem — timer 15 detik + Enemy2 punishment
# ════════════════════════════════════════════════════════════════════════
class TreeRitualSystem:
    """
    Mengatur kewajiban ritual pohon setelah perjanjian dibuat.

    - Timer 15 detik berjalan saat fight phase aktif.
    - Tiap kali timer habis, spawn 1 Enemy2 punishment (HP & damage tinggi).
    - Timer reset saat ritual berhasil (do_ritual_minigame return 1).
    - water_consumed: jumlah air yang harus dikurangi dari water_count
      di main.py setelah ritual (supaya TreeRitualSystem tidak perlu tahu
      variable global main.py).
    """
    TIMER_SECS  = 15    # detik antara kewajiban ritual
    PENALTY_HP  = 40    # HP Enemy2 punishment
    PENALTY_DMG = 3     # damage Enemy2 punishment

    def __init__(self, covenant_npc: CovenantNPC, fps: int = 60):
        self.npc             = covenant_npc
        self.fps             = fps
        self.covenant_made   = False
        self.timer_frames    = self.TIMER_SECS * fps
        self.water_consumed  = 0   # main.py baca ini lalu kurangi water_count
        self._active         = False

    def start_timer(self):
        """Panggil di awal setiap fight phase kalau covenant sudah dibuat."""
        self.timer_frames = self.TIMER_SECS * self.fps
        self._active      = True

    def reset_timer(self):
        """Panggil setelah ritual berhasil."""
        self.timer_frames = self.TIMER_SECS * self.fps

    def stop(self):
        """Panggil saat masuk explore phase."""
        self._active = False

    def update(self, player, enemies: pygame.sprite.Group,
               water_count: int) -> list:
        """
        Panggil tiap frame saat fight phase aktif & covenant_made == True.
        Return list Enemy2 baru yang harus ditambahkan ke enemies group.
        """
        if not self._active or not self.covenant_made:
            return []

        new_enemies = []

        self.timer_frames -= 1
        if self.timer_frames <= 0:
            # Spawn Enemy2 punishment — harimau menghilang
            ex = random.choice([80, WIDTH_FALLBACK - 80])
            ey = random.randint(100, 440)
            e  = _make_punishment_enemy(ex, ey,
                                        self.PENALTY_HP, self.PENALTY_DMG)
            new_enemies.append(e)
            self.npc.tiger_hidden = True   # harimau bersembunyi saat punishment aktif
            self.reset_timer()
            print("[SACRED TREE] Ritual terlewat — Enemy2 punishment muncul!")

        return new_enemies

    def draw_timer(self, screen: pygame.Surface,
                   title_font: pygame.font.Font,
                   small_font: pygame.font.Font):
        """Gambar countdown timer di atas pohon."""
        if not self._active or not self.covenant_made:
            return
        self.npc.draw_timer_above_tree(
            screen, title_font, small_font,
            self.timer_frames, self.TIMER_SECS, self.fps
        )


# ── Helper: buat Enemy2 punishment ──────────────────────────────────────
WIDTH_FALLBACK = 960   # fallback kalau main.py tidak pass WIDTH

def _make_punishment_enemy(x: int, y: int, hp: int, dmg: int):
    """Buat Enemy2 dengan HP dan damage yang dinaikkan."""
    from enemy2 import Enemy2
    e           = Enemy2(x, y)
    e.max_health = hp
    e.health     = hp
    e.speed      = 1.8   # sedikit lebih cepat dari normal
    # Enemy2 tidak punya field "damage" langsung di take_damage caller,
    # jadi kita simpan di atribut custom dan main.py akan baca ini
    # saat menghitung damage ke player.
    e._punishment_damage = dmg
    e._is_punishment     = True
    return e