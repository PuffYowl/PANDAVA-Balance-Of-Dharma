import os
import sys
import pygame
import random

# Boss utama — Dursasana. Struktur file ini SENGAJA dibuat mirip banget
# sama miniboss1.py (Miniboss_1) sesuai permintaan: "buat agar boss fight
# nya mirip seperti mini boss fight". Bedanya cuma di HP (jauh lebih
# banyak), nama, dan cara dia dipanggil dari main.py (fixed di Round 4,
# sekali saja, tidak random & tidak berulang).
FONT_PATH = "assets2/font/A Friend In Deed.otf"


def _load_font(size):
    """Load FONT_PATH dengan fallback ke font default kalau filenya
    belum ada di folder assets2/font (supaya tidak crash total)."""
    try:
        return pygame.font.Font(FONT_PATH, size)
    except (FileNotFoundError, OSError):
        print(f"[DURSASANA] Font '{FONT_PATH}' tidak ditemukan — pakai font default sementara")
        return pygame.font.SysFont(None, size)


def _draw_loading_bar(screen, progress, label=""):
    """
    Gambar layar loading sederhana (progress bar) sambil asset Dursasana
    di-load. `progress` adalah float 0.0–1.0.
    Dipanggil di antara tahap-tahap load supaya tidak terlihat "freeze"
    saat file gambar boss dibaca dari disk.
    """
    if screen is None:
        return

    # Tetap proses event supaya window tidak dianggap "Not Responding"
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    w, h = screen.get_size()
    bar_w, bar_h = 420, 26
    bar_x = w // 2 - bar_w // 2
    bar_y = h // 2 - bar_h // 2

    screen.fill((10, 8, 8))

    pygame.draw.rect(screen, (70, 20, 10), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), border_radius=8)
    pygame.draw.rect(screen, (35, 12, 8), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

    fill_w = int(bar_w * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        pygame.draw.rect(screen, (220, 60, 20), (bar_x, bar_y, fill_w, bar_h), border_radius=6)

    pygame.draw.rect(screen, (180, 90, 40), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

    title_surf = _load_font(24).render("Memuat Boss Dursasana...", True, (255, 225, 200))
    screen.blit(title_surf, title_surf.get_rect(center=(w // 2, bar_y - 28)))

    if label:
        label_surf = _load_font(18).render(label, True, (210, 180, 160))
        screen.blit(label_surf, label_surf.get_rect(center=(w // 2, bar_y + bar_h + 24)))

    pygame.display.flip()


def load_frames(folder, scale=4):
    frames = []
    if not os.path.exists(folder):
        return frames
    for file in sorted(os.listdir(folder)):
        if file.lower().endswith(".png"):
            img = pygame.image.load(os.path.join(folder, file)).convert_alpha()
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            frames.append(img)
    return frames


def load_spritesheet_row(path, frame_count, scale=1):
    """Sama seperti versi di miniboss1.py, tapi dengan fallback: kalau
    file spritesheet health bar belum ada, generate frame placeholder
    warna solid supaya game tidak crash sebelum asset dursasana
    disiapkan."""
    if not os.path.exists(path):
        print(f"[DURSASANA] Healthbar '{path}' tidak ditemukan — pakai placeholder sementara")
        frames = []
        for i in range(frame_count):
            ratio = 1 - (i / max(1, frame_count - 1))
            surf = pygame.Surface((220, 24), pygame.SRCALPHA)
            color = (int(90 + 130 * ratio), int(20 + 20 * ratio), 20, 255)
            surf.fill(color)
            frames.append(surf)
        return frames

    sheet = pygame.image.load(path).convert_alpha()
    frame_width  = sheet.get_width() // frame_count
    frame_height = sheet.get_height()
    frames = []
    for i in range(frame_count):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
        if scale != 1:
            frame = pygame.transform.scale(
                frame, (int(frame_width * scale), int(frame_height * scale))
            )
        frames.append(frame)
    return frames


class Dursasana(pygame.sprite.Sprite):
    def __init__(self, x, y, assets_folder='assets2/boss', screen=None):
        super().__init__()

        # ── Loading bar — total 5 tahap load asset ───────────────────────
        _TOTAL_STEPS = 5
        _draw_loading_bar(screen, 0 / _TOTAL_STEPS, "Animasi start fight...")

        # ── Coba berbagai nama folder untuk animasi startfight ──────────
        startfight_frames = []
        for folder_name in ("boss-start-fight", "StartFight", "Startfight", "start_fight",
                             "Start", "Intro", "Prepare", "Idle"):
            path = f"{assets_folder}/{folder_name}"
            frames = load_frames(path, 0.15)
            if frames:
                startfight_frames = frames
                print(f"[DURSASANA] StartFight animation loaded: {path}")
                break

        _draw_loading_bar(screen, 1 / _TOTAL_STEPS, "Animasi jalan...")
        walk_frames = load_frames(f"{assets_folder}/boss-walk", 0.15)

        # Fallback: pakai 4 frame walk pertama sebagai intro jika folder tidak ada
        if not startfight_frames:
            startfight_frames = walk_frames[:min(4, len(walk_frames))] if walk_frames else []
            print("[DURSASANA] StartFight folder tidak ditemukan — pakai Walk frames sebagai fallback")

        _draw_loading_bar(screen, 2 / _TOTAL_STEPS, "Animasi mati...")
        die_frames = load_frames(f"{assets_folder}/boss-death", 0.15)
        # Sama seperti mini boss: kalau asset "dursasana-die" belum ada,
        # dipakai animasi mati prosedural (fade + menciut + tenggelam).
        self.has_real_die_anim = bool(die_frames)
        if not self.has_real_die_anim:
            print("[DURSASANA] Die folder tidak ditemukan — pakai animasi mati prosedural (fade/shrink)")

        _draw_loading_bar(screen, 3 / _TOTAL_STEPS, "Animasi serang...")
        attack_frames = load_frames(f"{assets_folder}/boss-attack", 0.15)

        # ── Animasi dash — kalau folder belum ada, pakai walk frames
        #    sebagai fallback biar tetap ada gambar saat nge-dash ──────
        dash_frames = load_frames(f"{assets_folder}/boss-dash", 0.15)
        if not dash_frames:
            dash_frames = walk_frames
            print("[DURSASANA] Dash folder tidak ditemukan — pakai Walk frames sebagai fallback")

        self.animations = {
            "startfight": startfight_frames,
            "walk":       walk_frames,
            "die":        die_frames,
            "attack":     attack_frames,
            "dash":       dash_frames,
        }

        _draw_loading_bar(screen, 4 / _TOTAL_STEPS, "Health bar...")
        # ── Health bar sprite — boss punya health bar sendiri (lebih
        #    "penuh" segmennya dibanding mini boss karena HP jauh lebih
        #    banyak) ─────────────────────────────────────────────────
        self.healthbar_frames = load_spritesheet_row(
            "assets2/healthbar_dursasana.png", 8, scale=2
        )

        _draw_loading_bar(screen, 1.0, "Selesai!")

        self.state       = "startfight"
        self.frame_index = 0.0
        self.anim_speed  = 0.35

        self.image = self.animations["startfight"][0] if self.animations["startfight"] else pygame.Surface((64, 64), pygame.SRCALPHA)
        self.rect  = self.image.get_rect(center=(x, y))

        # Posisi float
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        # ── Stats — HP jauh lebih banyak, ini boss utama, bukan mini boss ─
        self.max_health = 100
        self.health     = self.max_health
        self.speed      = 1.5
        self.alive      = True
        self.dying      = False
        self.death_done = False   # True saat animasi mati selesai penuh

        # ── Intro state — boss diam & tidak bisa diserang selama animasi ─
        self.intro_done = False

        # ── Attack ──────────────────────────────────────────────────────
        self.attack_range    = 90
        self.attack_cooldown = 60
        self.attack_timer    = 0
        self.attacking       = False
        self.has_hit_player  = False

        # ── Dash — dipakai buat nutup jarak cepat waktu player jauh ──────
        self.dash_speed        = 11        # jauh lebih cepat dari self.speed
        self.dash_min_distance = 220       # cuma dash kalau player sejauh ini
        self.dash_cooldown     = 100       # jeda sebelum bisa dash lagi
        self.dash_timer        = 0
        self.dash_duration     = 22        # lama dash berlangsung (frame)
        self.dash_duration_timer = 0
        self.dashing           = False
        self.dash_dir_x        = 0.0
        self.dash_dir_y        = 0.0
        self.has_hit_player_dash = False

        # ── Hit & knockback ──────────────────────────────────────────────
        self.hit_cooldown    = 0
        self.hit_flash_timer = 0
        self.knockback_x     = 0

        # Flag satu-frame saat boss mati — dibaca main.py
        self.just_died = False

        self.facing = 1

    # =================================================================
    # AI
    # =================================================================
    def ai(self, player):
        if not self.alive or self.dying:
            return
        if not self.intro_done:
            return          # Diam total selama animasi intro

        # Kalau lagi dash, jalankan pergerakan dash & berhenti di sini —
        # tidak boleh mikir attack/walk lain sampai dash-nya kelar.
        if self.dashing:
            self._update_dash(player)
            return

        if self.attacking:
            return

        px, py = player.rect.center
        dx = px - self.x
        dy = py - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        self.facing = 1 if dx > 0 else -1

        # Pakai jarak total (dist), bukan cuma abs(dx), sama seperti
        # perbaikan yang sudah ada di mini boss.
        if dist <= self.attack_range and self.attack_timer == 0:
            self.start_attack()
            return

        # DASH — kalau player cukup jauh & cooldown dash sudah habis,
        # Dursasana nge-dash cepat ke arah player buat nutup jarak.
        if dist >= self.dash_min_distance and self.dash_timer == 0:
            self.start_dash(dx, dy, dist)
            return

        self.state = "walk"

        # Normalisasi supaya kecepatan diagonal sama dengan lurus
        if dist > 3:
            nx = dx / dist
            ny = dy / dist
            self.x += nx * self.speed
            self.y += ny * self.speed

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    # =================================================================
    # DASH
    # =================================================================
    def start_dash(self, dx, dy, dist):
        """Mulai dash: arah dikunci sekali di awal (tidak re-aim tiap
        frame) supaya terasa seperti dash sungguhan, bukan cuma jalan
        cepat yang selalu mengejar posisi player."""
        self.state               = "dash"
        self.dashing             = True
        self.frame_index         = 0
        self.dash_duration_timer = self.dash_duration
        self.dash_timer          = self.dash_cooldown
        self.has_hit_player_dash = False

        if dist > 0:
            self.dash_dir_x = dx / dist
            self.dash_dir_y = dy / dist
        else:
            self.dash_dir_x = 1 if self.facing == 1 else -1
            self.dash_dir_y = 0

    def _update_dash(self, player):
        if self.dash_duration_timer <= 0:
            self.dashing = False
            self.state   = "walk"
            self.frame_index = 0
            return

        self.dash_duration_timer -= 1
        self.x += self.dash_dir_x * self.dash_speed
        self.y += self.dash_dir_y * self.dash_speed
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    # =================================================================
    # ATTACK
    # =================================================================
    def start_attack(self):
        self.state          = "attack"
        self.attacking      = True
        self.frame_index    = 0
        self.attack_timer   = self.attack_cooldown
        self.has_hit_player = False

    def get_attack_hitbox(self):
        # ── Dash contact damage ───────────────────────────────────────
        # Dash tidak punya frame serang presisi (animasinya bisa cuma
        # fallback walk), jadi dipakai window waktu: begitu dash sudah
        # jalan sedikit (biar tidak nge-hit di frame pertama sebelum
        # posisi kebaca layar), hitbox aktif SEKALI per dash — dipakai
        # rect Dursasana sendiri yang sedikit di-inflate.
        if self.dashing:
            if self.has_hit_player_dash:
                return None
            if self.dash_duration_timer <= self.dash_duration - 4:
                self.has_hit_player_dash = True
                return self.rect.inflate(20, 10)
            return None

        if not self.attacking:
            return None
        current_frame = int(self.frame_index)
        if current_frame != 8 or self.has_hit_player:
            return None
        self.has_hit_player = True
        offset = 35 if self.facing == 1 else -35
        return pygame.Rect(
            self.rect.centerx + offset,
            self.rect.centery - 30,
            45, 60
        )

    # =================================================================
    # DAMAGE
    # =================================================================
    def take_damage(self, direction, damage):
        if not self.intro_done:
            return          # Invincible selama intro
        if self.hit_cooldown == 0 and self.alive:
            self.health     -= damage
            self.hit_cooldown    = 20
            self.knockback_x     = direction * 8
            self.hit_flash_timer = 6
            if self.health <= 0:
                self.start_death()

    # =================================================================
    # DEATH
    # =================================================================
    def start_death(self):
        self.alive           = False
        self.dying           = True
        self.state           = "die"
        self.frame_index     = 0
        self.hit_flash_timer = 0
        self.just_died       = True   # main.py baca lalu reset
        self.death_timer     = 0      # safety net — lihat update()

        # ── Untuk animasi mati prosedural (dipakai kalau tidak ada
        #    sprite "dursasana-die" asli) ────────────────────────────
        self.death_anim_timer       = 0
        self.death_anchor_midbottom = self.rect.midbottom
        self.death_base_image       = self.image.copy()

    # =================================================================
    # ANIMATION
    # =================================================================
    def animate(self):
        if self.dying:
            if self.has_real_die_anim:
                self._animate_die_frames()
            else:
                self._animate_procedural_death()
            return

        frames = self.animations.get(self.state, [])
        if not frames:
            return

        self.frame_index += self.anim_speed

        if self.frame_index >= len(frames):
            if self.state == "startfight":
                # Intro selesai → aktifkan AI
                self.intro_done  = True
                self.state       = "walk"
                self.frame_index = 0
            elif self.state == "attack":
                self.attacking   = False
                self.state       = "walk"
                self.frame_index = 0
            else:
                self.frame_index = 0

            # Refresh `frames` setelah state berubah supaya tidak sempat
            # menampilkan 1 frame dari animasi lama.
            frames = self.animations.get(self.state, [])
            if not frames:
                return

        old_midbottom = self.rect.midbottom
        self.image    = frames[int(self.frame_index)]

        _speeds = {"startfight": 0.35, "walk": 0.2, "attack": 0.4, "dash": 0.5}
        self.anim_speed = _speeds.get(self.state, 0.2)

        if self.facing == -1:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect          = self.image.get_rect()
        self.rect.midbottom = old_midbottom

        if self.hit_flash_timer > 0:
            flash = self.image.copy()
            flash.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash

    def _animate_die_frames(self):
        """Animasi mati berbasis sprite asli (folder dursasana-die ada)."""
        frames = self.animations.get("die", [])
        if not frames:
            self.death_done = True   # safety — seharusnya tidak pernah kejadian
            return

        self.frame_index += 0.25

        if self.frame_index >= len(frames):
            self.frame_index = float(len(frames) - 1)
            self.death_done  = True  # sinyal ke main bahwa animasi mati usai

        old_midbottom = self.rect.midbottom
        self.image    = frames[int(self.frame_index)]
        if self.facing == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect           = self.image.get_rect()
        self.rect.midbottom = old_midbottom

    def _animate_procedural_death(self):
        """
        Animasi mati prosedural — dipakai kalau tidak ada sprite
        "dursasana-die". Sama seperti mini boss: fade out + shrink +
        tenggelam + tint merah, dari frame terakhir sebelum mati.
        """
        DURATION = 75   # ±1.25 detik @60fps
        self.death_anim_timer += 1
        progress = min(1.0, self.death_anim_timer / DURATION)

        base = self.death_base_image
        w, h = base.get_size()

        scale = 1.0 - 0.35 * progress
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        frame = pygame.transform.smoothscale(base, (new_w, new_h))

        tint_surf = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
        fade = int(150 * progress)
        tint_surf.fill((0, fade, fade, 0))
        frame.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        frame.set_alpha(int(255 * (1.0 - progress)))

        self.image = frame
        self.rect  = self.image.get_rect()
        sink_offset = int(20 * progress)
        self.rect.midbottom = (
            self.death_anchor_midbottom[0],
            self.death_anchor_midbottom[1] + sink_offset,
        )

        if progress >= 1.0:
            self.death_done = True

    # =================================================================
    # UPDATE
    # =================================================================
    def update(self, player):
        if self.dying:
            self.animate()
            self.death_timer = getattr(self, "death_timer", 0) + 1
            if self.death_timer > 180:   # ±3 detik @60fps — safety net
                self.death_done = True
            # Boss TIDAK respawn — kematiannya permanen
            return

        if not self.alive:
            return

        if self.attack_timer   > 0: self.attack_timer   -= 1
        if self.hit_cooldown   > 0: self.hit_cooldown   -= 1
        if self.hit_flash_timer > 0: self.hit_flash_timer -= 1
        if self.dash_timer     > 0: self.dash_timer     -= 1

        if self.knockback_x != 0:
            self.x          += self.knockback_x
            self.knockback_x *= 0.85
            if abs(self.knockback_x) < 0.3:
                self.knockback_x = 0
            self.rect.centerx = int(self.x)

        self.ai(player)
        self.animate()

    # =================================================================
    # HEALTH BAR KECIL (di atas sprite) — health bar besar di tengah
    # atas layar tetap digambar oleh main.py, sama seperti mini boss.
    # =================================================================
    def draw_healthbar(self, screen):
        ratio       = self.health / self.max_health
        max_index   = len(self.healthbar_frames) - 1
        frame_index = int((1 - ratio) * max_index)
        frame_index = max(0, min(max_index, frame_index))
        bar_img     = self.healthbar_frames[frame_index]
        bar_rect    = bar_img.get_rect(
            midbottom=(self.rect.centerx, self.rect.top + 18)
        )
        screen.blit(bar_img, bar_rect)