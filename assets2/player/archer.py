import pygame
import random
from .base_player import load_spritesheet_row 
from .base_player import BasePlayer, load_frames  


class Archer(BasePlayer):

    def __init__(self, x, y, assets_folder='assets2/player_archer', scale=4):

        super().__init__(
            x,
            y,
            assets_folder,
            scale,
            use_spritesheet=True
        )

        # ================= HEALTHBAR =================
        self.healthbar_frames = load_spritesheet_row(
            "assets2/healthbar_satyr.png",
            5,
            scale=2
        )

        # ================= STATS =================
        self.speed = 1.7
        self.dash_speed = 18
        self.attack_cooldown = 35

        self.attack_anim_speed = 0.5

        self.damage = 2
        self.max_health = 10
        self.health = self.max_health

        self.spawn_arrow = False

        # ================= AFTERIMAGE =================
        self.afterimages = []
        self.afterimage_delay = 2
        self.afterimage_timer = 0
        self.afterimage_fade_speed = 25

        # ================= ULTIMATE / BOOST =================
        self.ultimate_damage_mult    = 1.8     # pengali damage selama boost aktif
        self.ultimate_speed_mult     = 1.5     # pengali speed selama boost aktif
        self.ultimate_duration       = 300     # lama boost aktif (frame, ±5 detik @60fps)
        self.ultimate_cooldown_time  = 600     # cooldown sebelum bisa dipakai lagi (±10 detik)
        self.ultimate_banner_time    = 120     # lama gambar "Boost!" tampil di tengah (±2 detik)
        self.ultimate_fade_frames    = 20      # durasi fade-out di akhir tampilnya banner

        self.ultimate_active         = False
        self.ultimate_timer          = 0
        self.ultimate_cooldown_timer = 0
        self.ultimate_banner_timer   = 0

        # Stat sebelum boost disimpan SAAT diaktifkan (bukan dari __init__),
        # supaya upgrade permanen dari Resi tidak ke-reset waktu boost habis.
        self._pre_ultimate_damage = self.damage
        self._pre_ultimate_speed  = self.speed
        self._ultimate_key_prev   = False

        # ================= RAGE (window bonus setelah cooldown ULT habis) =====
        # Setiap kali cooldown ultimate BIASA habis (ultimate_cooldown_timer
        # turun ke 0), ada window RAGE selama rage_window_duration (5 detik).
        # Selama window ini, tombol ULT yang sama (lihat main.py) berubah
        # jadi tombol "RAGE!" — kalau dipencet, boost yang didapat LEBIH
        # BESAR daripada ultimate biasa, tapi honor (dharma/adharma) si
        # player TURUN sebesar rage_honor_penalty setiap pemakaian (lihat
        # self.honor_system, di-attach dari main.py seperti mobile_controls).
        self.rage_damage_mult    = 2.5     # pengali damage selama RAGE aktif (> ultimate biasa)
        self.rage_speed_mult     = 2.0     # pengali speed selama RAGE aktif (> ultimate biasa)
        self.rage_window_duration = 300    # lama window RAGE tersedia (frame, ±5 detik @60fps)
        self.rage_honor_penalty  = 15      # adharma yang ditambah (honor TURUN) per pemakaian RAGE

        self.rage_window_active  = False   # True selama window 5 detik tersedia
        self.rage_window_timer   = 0
        self.rage_active         = False   # True selama efek RAGE sedang berjalan (boost aktif)
        self.rage_timer          = 0
        self.rage_banner_timer   = 0

        # honor_system di-attach dari main.py (pola sama seperti
        # self.mobile_controls) — boleh None kalau belum di-attach, supaya
        # activate_rage() tidak crash kalau dipanggil sebelum di-set.
        self.honor_system = None

        # Gambar "Boost!" yang muncul di samping kiri screen saat ultimate aktif
        self.ultimate_banner_img = pygame.image.load(
            "assets2/boost_banner.jpeg"
        ).convert()

        banner_max_w = 260                  # diperkecil — sebelumnya 700 (di tengah)
        if self.ultimate_banner_img.get_width() > banner_max_w:
            ratio = banner_max_w / self.ultimate_banner_img.get_width()
            new_size = (
                int(self.ultimate_banner_img.get_width()  * ratio),
                int(self.ultimate_banner_img.get_height() * ratio),
            )
            self.ultimate_banner_img = pygame.transform.smoothscale(
                self.ultimate_banner_img, new_size
            )

        # Gambar "RAGE!" — posisi, ukuran, dan efek shake SAMA seperti
        # banner "Boost!" (lihat draw_rage_banner di bawah, isinya identik
        # dengan draw_ultimate_banner kecuali gambar & timer yang dipakai).
        self.rage_banner_img = pygame.image.load(
            "assets2/rage_banner.png"
        ).convert()
        if self.rage_banner_img.get_width() > banner_max_w:
            ratio = banner_max_w / self.rage_banner_img.get_width()
            new_size = (
                int(self.rage_banner_img.get_width()  * ratio),
                int(self.rage_banner_img.get_height() * ratio),
            )
            self.rage_banner_img = pygame.transform.smoothscale(
                self.rage_banner_img, new_size
            )

        self.ultimate_banner_margin = 16    # jarak dari tepi kiri layar
        self.ultimate_shake_amount  = 3     # besar goyangan (px) — "shake sedikit"


    # ================= UPDATE =================
    def update(self):

        super().update()

        # ================= ULTIMATE / BOOST =================
        # Tombol U untuk aktifkan ultimate (edge-detect → tidak ke-trigger
        # berulang kali kalau tombolnya ditahan). Kalau window RAGE sedang
        # terbuka (5 detik setelah cooldown ultimate biasa habis), tombol U
        # yang SAMA otomatis trigger RAGE — sama seperti tombol UI di
        # main.py yang berubah label jadi "RAGE!" selama window ini.
        keys = pygame.key.get_pressed()
        ultimate_key_down = keys[pygame.K_u]
        if ultimate_key_down and not self._ultimate_key_prev:
            if self.rage_window_active:
                self.activate_rage()
            else:
                self.activate_ultimate()
        self._ultimate_key_prev = ultimate_key_down

        if self.ultimate_active:
            self.ultimate_timer -= 1
            if self.ultimate_timer <= 0:
                # Boost selesai → kembalikan damage/speed ke nilai sebelum boost
                self.damage = self._pre_ultimate_damage
                self.speed  = self._pre_ultimate_speed
                self.ultimate_active        = False
                self.ultimate_cooldown_timer = self.ultimate_cooldown_time

        if self.ultimate_cooldown_timer > 0:
            self.ultimate_cooldown_timer -= 1
            if self.ultimate_cooldown_timer <= 0:
                # Cooldown ultimate biasa baru SAJA habis -> buka window
                # RAGE selama rage_window_duration. Tidak terjadi kalau
                # RAGE sendiri sedang aktif (lihat activate_rage: itu juga
                # menyetel ultimate_cooldown_timer, jadi window tidak akan
                # langsung dibuka lagi sebelum efek RAGE selesai).
                if not self.rage_active:
                    self.rage_window_active = True
                    self.rage_window_timer  = self.rage_window_duration

        if self.rage_window_active:
            self.rage_window_timer -= 1
            if self.rage_window_timer <= 0:
                self.rage_window_active = False

        if self.rage_active:
            self.rage_timer -= 1
            if self.rage_timer <= 0:
                # Efek RAGE selesai → kembalikan damage/speed ke nilai
                # sebelum RAGE diaktifkan, lalu masuk cooldown (sama timer
                # cooldown dengan ultimate biasa, supaya tombol balik ke
                # "⏳ Xs" dulu sebelum siap dipakai lagi).
                self.damage = self._pre_ultimate_damage
                self.speed  = self._pre_ultimate_speed
                self.rage_active            = False
                self.ultimate_cooldown_timer = self.ultimate_cooldown_time

        if self.ultimate_banner_timer > 0:
            self.ultimate_banner_timer -= 1

        if self.rage_banner_timer > 0:
            self.rage_banner_timer -= 1

        # AFTERIMAGE
        if self.dashing:

            self.afterimage_timer += 1

            if self.afterimage_timer >= self.afterimage_delay:

                self.afterimage_timer = 0

                self.afterimages.append([
                    self.image.copy(),
                    self.rect.topleft,
                    180
                ])

        # fade
        for img in self.afterimages:
            img[2] -= self.afterimage_fade_speed

        self.afterimages = [img for img in self.afterimages if img[2] > 0]


    # ================= ULTIMATE / BOOST =================
    def activate_ultimate(self):
        """Aktifkan boost ultimate. Return True kalau berhasil aktif,
        False kalau masih cooldown atau sedang aktif."""

        if self.ultimate_active or self.ultimate_cooldown_timer > 0:
            return False

        self.ultimate_active       = True
        self.ultimate_timer        = self.ultimate_duration
        self.ultimate_banner_timer = self.ultimate_banner_time

        self._pre_ultimate_damage = self.damage
        self._pre_ultimate_speed  = self.speed

        self.damage = self._pre_ultimate_damage * self.ultimate_damage_mult
        self.speed  = self._pre_ultimate_speed  * self.ultimate_speed_mult

        return True

    # ================= RAGE =================
    def activate_rage(self):
        """Aktifkan boost RAGE — hanya bisa dipakai SELAMA window RAGE
        terbuka (rage_window_active, 5 detik setelah cooldown ultimate
        biasa habis). Boost yang didapat lebih besar dari ultimate biasa
        (rage_damage_mult, rage_speed_mult), TAPI honor player turun
        (adharma naik) sebesar rage_honor_penalty setiap pemakaian.

        Return True kalau berhasil aktif, False kalau window RAGE sedang
        tidak terbuka atau ultimate/RAGE lain sedang aktif."""

        if not self.rage_window_active:
            return False
        if self.ultimate_active or self.rage_active:
            return False

        self.rage_window_active = False   # window dipakai, tutup sekarang
        self.rage_window_timer  = 0

        self.rage_active       = True
        self.rage_timer        = self.ultimate_duration   # durasi sama seperti ultimate biasa
        self.rage_banner_timer = self.ultimate_banner_time

        self._pre_ultimate_damage = self.damage
        self._pre_ultimate_speed  = self.speed

        self.damage = self._pre_ultimate_damage * self.rage_damage_mult
        self.speed  = self._pre_ultimate_speed  * self.rage_speed_mult

        # Konsekuensi: adharma naik (honor turun). honor_system di-attach
        # dari main.py — kalau belum di-attach (None), efek boost tetap
        # jalan tapi penalti honor di-skip saja (tidak crash).
        if self.honor_system is not None:
            self.honor_system.change(-self.rage_honor_penalty)

        return True


    def draw_ultimate_banner(self, surface):
        """Gambar 'Boost!' di samping kiri screen selagi ultimate baru aktif,
        dengan sedikit efek shake. Panggil ini di main.py, idealnya paling
        akhir (sebelum pygame.display.flip()) supaya tampil di atas elemen lain."""

        if self.ultimate_banner_timer <= 0:
            return

        # Efek shake ringan — goyangan acak kecil tiap frame selagi banner tampil
        shake_x = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)
        shake_y = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)

        img_rect = self.ultimate_banner_img.get_rect(
            midleft=(self.ultimate_banner_margin, surface.get_height() // 2)
        )
        img_rect.x += shake_x
        img_rect.y += shake_y

        if self.ultimate_banner_timer <= self.ultimate_fade_frames:
            alpha  = int(255 * (self.ultimate_banner_timer / self.ultimate_fade_frames))
            banner = self.ultimate_banner_img.copy()
            banner.set_alpha(alpha)
            surface.blit(banner, img_rect)
        else:
            surface.blit(self.ultimate_banner_img, img_rect)


    def draw_rage_banner(self, surface):
        """Gambar 'RAGE!' di samping kiri screen selagi RAGE baru aktif.
        Posisi, ukuran, dan efek shake SAMA seperti draw_ultimate_banner —
        cuma gambar dan timer-nya yang beda (rage_banner_img / rage_banner_timer)."""

        if self.rage_banner_timer <= 0:
            return

        shake_x = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)
        shake_y = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)

        img_rect = self.rage_banner_img.get_rect(
            midleft=(self.ultimate_banner_margin, surface.get_height() // 2)
        )
        img_rect.x += shake_x
        img_rect.y += shake_y

        if self.rage_banner_timer <= self.ultimate_fade_frames:
            alpha  = int(255 * (self.rage_banner_timer / self.ultimate_fade_frames))
            banner = self.rage_banner_img.copy()
            banner.set_alpha(alpha)
            surface.blit(banner, img_rect)
        else:
            surface.blit(self.rage_banner_img, img_rect)


    # ================= DRAW =================
    def draw(self, surface):

        for img, pos, alpha in self.afterimages:

            temp = img.copy()
            temp.set_alpha(alpha)

            if self.facing == -1:
                temp = pygame.transform.flip(temp, True, False)

            surface.blit(temp, pos)

        surface.blit(self.image, self.rect)


    def draw_healthbar(self, surface):

        ratio = self.health / self.max_health

        frame_count = len(self.healthbar_frames)
        frame_index = int((1 - ratio) * (frame_count - 1))

        frame_index = max(0, min(frame_count - 1, frame_index))

        bar_img = self.healthbar_frames[frame_index]

        bar_rect = bar_img.get_rect(
            midbottom=(self.rect.centerx, self.rect.top - 5)
        )

        surface.blit(bar_img, bar_rect)


    # ================= ANIMATE =================
    def animate(self):

        frames = self.animations[self.state]

        # ================= SPEED =================
        if self.state == "attack":
            self.frame_index += self.attack_anim_speed
        else:
            self.frame_index += self.anim_speed

        # ================= END ATTACK =================
        if self.state == "attack" and self.frame_index >= len(frames):

            self.attacking = False
            self.attack_timer = self.attack_cooldown
            self.state = "idle"
            self.frame_index = 0

            # 🎯 spawn arrow DI SINI (bener)
            self.spawn_arrow = True

        # ================= LOOP FRAME =================
        if self.frame_index >= len(frames):
            self.frame_index = 0

        # ================= APPLY FRAME (INI YANG TADI SALAH POSISI) =================
        old_anchor = self.rect.midbottom

        frame = frames[int(self.frame_index)]

        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)

        self.image = frame

        # ❗ jangan buat rect baru tanpa anchor
        self.rect.size = self.image.get_size()
        self.rect.midbottom = old_anchor

    # ================= HITBOX =================
    def get_attack_hitbox(self):

        if self.state != "attack":
            return None

        offset = 60 if self.facing == 1 else -60

        return pygame.Rect(
            self.rect.centerx + offset,
            self.rect.centery - 30,
            70,
            60
        )