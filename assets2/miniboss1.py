import os
import sys
import pygame
import random

# Font kustom yang sama dipakai di seluruh game (lihat main.py).
# Dipakai juga di sini (loading bar) supaya benar-benar "semua font"
# konsisten satu jenis, bukan cuma di main.py.
FONT_PATH = "assets2/font/A Friend In Deed.otf"

# Suara roar yang diputar saat animasi "startfight" mencapai frame ke-35
# (index 35, dihitung dari 0) sampai animasi intro-nya selesai.
ROAR_SOUND_PATH = "assets2/miniboss_roar.wav"
ROAR_TRIGGER_FRAME = 35


def _load_font(size):
    """Load FONT_PATH dengan fallback ke font default kalau filenya
    belum ada di folder assets2/font (supaya tidak crash total)."""
    try:
        return pygame.font.Font(FONT_PATH, size)
    except (FileNotFoundError, OSError):
        print(f"[MINIBOSS] Font '{FONT_PATH}' tidak ditemukan — pakai font default sementara")
        return pygame.font.SysFont(None, size)


def _load_roar_sound():
    """Load ROAR_SOUND_PATH dengan fallback aman kalau file belum ada
    atau mixer belum di-init (supaya tidak crash total)."""
    try:
        return pygame.mixer.Sound(ROAR_SOUND_PATH)
    except (FileNotFoundError, OSError, pygame.error):
        print(f"[MINIBOSS] Sound '{ROAR_SOUND_PATH}' tidak ditemukan — roar dinonaktifkan")
        return None


def _draw_loading_bar(screen, progress, label=""):
    """
    Gambar layar loading sederhana (progress bar) sambil asset mini boss
    di-load. `progress` adalah float 0.0–1.0.
    Dipanggil di antara tahap-tahap load supaya tidak terlihat "freeze"
    saat file gambar mini boss dibaca dari disk.
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

    screen.fill((12, 10, 10))

    pygame.draw.rect(screen, (60, 20, 20), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), border_radius=8)
    pygame.draw.rect(screen, (30, 15, 15), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

    fill_w = int(bar_w * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        pygame.draw.rect(screen, (200, 40, 40), (bar_x, bar_y, fill_w, bar_h), border_radius=6)

    pygame.draw.rect(screen, (160, 60, 60), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

    title_surf = _load_font(24).render("Memuat Mini Boss...", True, (255, 220, 220))
    screen.blit(title_surf, title_surf.get_rect(center=(w // 2, bar_y - 28)))

    if label:
        label_surf = _load_font(18).render(label, True, (200, 170, 170))
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


class Miniboss_1(pygame.sprite.Sprite):
    def __init__(self, x, y, assets_folder='assets2/mini_boss', screen=None):
        super().__init__()

        # ── Loading bar — total 5 tahap load asset ───────────────────────
        # `screen` opsional: kalau di-isi (dipanggil dari main.py), progress
        # bar akan tampil di layar selama frame-frame gambar mini boss
        # dibaca dari disk. Kalau None, loading tetap jalan seperti biasa
        # tanpa tampilan apa pun (silent), jadi tetap backward-compatible.
        _TOTAL_STEPS = 5
        _draw_loading_bar(screen, 0 / _TOTAL_STEPS, "Animasi start fight...")

        # ── Coba berbagai nama folder untuk animasi startfight ──────────
        startfight_frames = []
        for folder_name in ("mini-boss-start", "StartFight", "Startfight", "start_fight",
                            "Start", "Intro", "Prepare", "Idle"):
            path = f"{assets_folder}/{folder_name}"
            frames = load_frames(path, 0.15)
            if frames:
                startfight_frames = frames
                print(f"[MINIBOSS] StartFight animation loaded: {path}")
                break

        _draw_loading_bar(screen, 1 / _TOTAL_STEPS, "Animasi jalan...")
        walk_frames = load_frames(f"{assets_folder}/mini-boss-walk", 0.15)

        # Fallback: pakai 4 frame walk pertama sebagai intro jika folder tidak ada
        if not startfight_frames:
            startfight_frames = walk_frames[:min(4, len(walk_frames))] if walk_frames else []
            print("[MINIBOSS] StartFight folder tidak ditemukan — pakai Walk frames sebagai fallback")

        _draw_loading_bar(screen, 2 / _TOTAL_STEPS, "Animasi mati...")
        die_frames = load_frames(f"{assets_folder}/mini-boss-die", 0.1)
        # Kalau asset "mini-boss-die" belum ada, jangan cuma nampilin 1
        # frame diam — pakai efek kematian prosedural (fade + menciut +
        # tenggelam) yang dibangun dari frame terakhir boss sebelum mati,
        # supaya tetap terlihat seperti animasi kematian sungguhan.
        self.has_real_die_anim = bool(die_frames)
        if not self.has_real_die_anim:
            print("[MINIBOSS] Die folder tidak ditemukan — pakai animasi mati prosedural (fade/shrink)")

        _draw_loading_bar(screen, 3 / _TOTAL_STEPS, "Animasi serang...")
        attack_frames = load_frames(f"{assets_folder}/mini-boss-attack", 0.15)

        self.animations = {
            "startfight": startfight_frames,
            "walk":       walk_frames,
            "die":        die_frames,
            "attack":     attack_frames,
        }

        _draw_loading_bar(screen, 4 / _TOTAL_STEPS, "Health bar...")
        # ── Health bar sprite ────────────────────────────────────────────
        self.healthbar_frames = load_spritesheet_row(
            "assets2/healthbar_enemy.png", 5, scale=2
        )

        _draw_loading_bar(screen, 1.0, "Selesai!")

        # ── Roar sound — diputar saat frame startfight mencapai
        #    ROAR_TRIGGER_FRAME sampai animasi intro selesai ──────────────
        self.roar_sound    = _load_roar_sound()
        self._roar_channel = None
        self._roar_played  = False

        self.state       = "startfight"
        self.frame_index = 0.0
        self.anim_speed  = 0.35   # dipercepat (sebelumnya 0.15) sesuai permintaan

        self.image = self.animations["startfight"][0]
        self.rect  = self.image.get_rect(center=(x, y))

        # Posisi float
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        # ── Stats — health tinggi untuk mini boss ────────────────────────
        self.max_health = 80
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

        if self.attacking:
            return

        px, py = player.rect.center
        dx = px - self.x
        dy = py - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        self.facing = 1 if dx > 0 else -1

        # PENTING: pakai jarak total (dist), bukan cuma abs(dx).
        # Sebelumnya hanya mengecek dx, jadi kalau boss & player berada
        # di garis x yang sama (dx ~ 0) tapi jaraknya jauh secara vertikal,
        # boss langsung menganggap dirinya "dalam jangkauan serang" dan
        # diam menyerang di tempat alih-alih berjalan mendekat.
        if dist <= self.attack_range and self.attack_timer == 0:
            self.start_attack()
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
    # ATTACK
    # =================================================================
    def start_attack(self):
        self.state          = "attack"
        self.attacking      = True
        self.frame_index    = 0
        self.attack_timer   = self.attack_cooldown
        self.has_hit_player = False

    def get_attack_hitbox(self):
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

        # Kalau roar masih bunyi (mis. boss dibunuh mid-intro), hentikan
        if getattr(self, "_roar_channel", None) is not None:
            self._roar_channel.stop()
            self._roar_channel = None

        # ── Untuk animasi mati prosedural (dipakai kalau tidak ada
        #    sprite "mini-boss-die" asli) ────────────────────────────
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

        # ── Roar sound: begitu frame startfight menyentuh frame ke-35,
        #    mainkan suara roar dan biarkan looping sampai animasi
        #    startfight-nya benar-benar selesai (di-stop di bawah) ───────
        if (self.state == "startfight" and not self._roar_played
                and self.roar_sound is not None
                and int(self.frame_index) >= ROAR_TRIGGER_FRAME):
            self._roar_channel = self.roar_sound.play(loops=-1)
            self._roar_played  = True

        if self.frame_index >= len(frames):
            if self.state == "startfight":
                # Intro selesai → aktifkan AI
                self.intro_done  = True
                self.state       = "walk"
                self.frame_index = 0

                # Animasi startfight selesai → hentikan roar (kalau masih bunyi)
                if self._roar_channel is not None:
                    self._roar_channel.stop()
                    self._roar_channel = None
            elif self.state == "attack":
                self.attacking   = False
                self.state       = "walk"
                self.frame_index = 0
            else:
                self.frame_index = 0

            # PENTING: setelah state berubah (mis. startfight → walk),
            # `frames` di atas masih menunjuk ke list animasi LAMA.
            # Kalau tidak di-refresh, frame pertama animasi baru akan
            # salah ambil gambar dari animasi sebelumnya selama 1 frame.
            frames = self.animations.get(self.state, [])
            if not frames:
                return

        old_midbottom = self.rect.midbottom
        self.image    = frames[int(self.frame_index)]

        # Kecepatan animasi per-state ("startfight" dipercepat sesuai permintaan)
        _speeds = {"startfight": 0.35, "walk": 0.2, "attack": 0.4}
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
        """Animasi mati berbasis sprite asli (folder mini-boss-die ada)."""
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
        "mini-boss-die". Dibuat dari frame terakhir boss sebelum mati
        (self.death_base_image), lalu: memudar (fade out) + menciut
        (shrink) + tenggelam sedikit ke bawah + memerah (tint merah),
        supaya tetap terasa seperti "animasi kematian" walau tanpa
        gambar sprite khusus.
        """
        DURATION = 75   # ±1.25 detik @60fps
        self.death_anim_timer += 1
        progress = min(1.0, self.death_anim_timer / DURATION)

        base = self.death_base_image
        w, h = base.get_size()

        # Menciut sedikit demi sedikit
        scale = 1.0 - 0.35 * progress
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        frame = pygame.transform.smoothscale(base, (new_w, new_h))

        # Tint memerah (channel hijau & biru dikurangi) supaya terkesan
        # "hangus/kalah", makin pekat seiring waktu
        tint_surf = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
        fade = int(150 * progress)
        tint_surf.fill((0, fade, fade, 0))
        frame.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # Fade out alpha keseluruhan
        frame.set_alpha(int(255 * (1.0 - progress)))

        self.image = frame
        self.rect  = self.image.get_rect()
        sink_offset = int(20 * progress)   # tenggelam turun sedikit
        self.rect.midbottom = (
            self.death_anchor_midbottom[0],
            self.death_anchor_midbottom[1] + sink_offset,
        )

        if progress >= 1.0:
            self.death_done = True   # sinyal ke main bahwa animasi mati usai

    # =================================================================
    # UPDATE
    # =================================================================
    def update(self, player):
        if self.dying:
            self.animate()
            # Safety net: apapun yang terjadi pada animasi mati (asset
            # hilang, list frame kosong, dll), death_done WAJIB menyala
            # dalam waktu wajar supaya fight loop di main.py tidak
            # menunggu selamanya dan player tidak stuck di arena.
            self.death_timer = getattr(self, "death_timer", 0) + 1
            if self.death_timer > 180:   # ±3 detik @60fps
                self.death_done = True
            # Mini boss TIDAK respawn — kematiannya permanen
            return

        if not self.alive:
            return

        if self.attack_timer   > 0: self.attack_timer   -= 1
        if self.hit_cooldown   > 0: self.hit_cooldown   -= 1
        if self.hit_flash_timer > 0: self.hit_flash_timer -= 1

        if self.knockback_x != 0:
            self.x          += self.knockback_x
            self.knockback_x *= 0.85
            if abs(self.knockback_x) < 0.3:
                self.knockback_x = 0
            self.rect.centerx = int(self.x)

        self.ai(player)
        self.animate()

    # =================================================================
    # HEALTH BAR KECIL (di atas sprite — dipakai oleh healthbar sendiri)
    # Health bar besar di tengah atas layar digambar oleh main.py
    # =================================================================
    def draw_healthbar(self, screen):
        ratio       = self.health / self.max_health
        frame_index = int((1 - ratio) * 4)
        frame_index = max(0, min(4, frame_index))
        bar_img     = self.healthbar_frames[frame_index]
        bar_rect    = bar_img.get_rect(
            midbottom=(self.rect.centerx, self.rect.top + 18)
        )
        screen.blit(bar_img, bar_rect)