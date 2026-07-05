import pygame
import os
import random

def load_frames(folder, scale=1):

    frames = []

    for file in sorted(os.listdir(folder)):

        if file.lower().endswith(".png"):

            img = pygame.image.load(os.path.join(folder, file)).convert_alpha()

            w, h = img.get_size()

            img = pygame.transform.scale(
                img,
                (int(w * scale), int(h * scale))
            )

            frames.append(img)

    return normalize_frame_sizes(frames)


def normalize_frame_sizes(frames):
    """
    Menyamakan ukuran kanvas semua frame dalam list ke ukuran terbesar
    (lebar & tinggi maksimum di antara semua frame), supaya animasi
    tidak kelihatan "ganti-ganti ukuran" saat pindah frame.

    Setiap frame ditempatkan di tengah-bawah (midbottom) kanvas baru,
    jadi kaki karakter tetap menempel di posisi yang sama, tidak
    melar/distort, hanya ditambah ruang transparan di sekitarnya.
    """

    if not frames:
        return frames

    max_w = max(f.get_width() for f in frames)
    max_h = max(f.get_height() for f in frames)

    normalized = []

    for f in frames:

        canvas = pygame.Surface((max_w, max_h), pygame.SRCALPHA)

        fw, fh = f.get_size()

        # Tempel di tengah secara horizontal, rapat ke bawah secara
        # vertikal (anggap "kaki" karakter ada di bagian bawah frame).
        pos_x = (max_w - fw) // 2
        pos_y = max_h - fh

        canvas.blit(f, (pos_x, pos_y))

        normalized.append(canvas)

    return normalized

# ================= SPRITESHEET LOADER =================
def load_spritesheet_row(path, frame_count, scale=1):

    sheet = pygame.image.load(path).convert_alpha()

    sheet_width = sheet.get_width()
    sheet_height = sheet.get_height()

    frame_width = sheet_width // frame_count
    frame_height = sheet_height

    frames = []

    for i in range(frame_count):

        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)

        frame.blit(
            sheet,
            (0, 0),
            (i * frame_width, 0, frame_width, frame_height)
        )

        if scale != 1:

            frame = pygame.transform.scale(
                frame,
                (int(frame_width * scale), int(frame_height * scale))
            )

        frames.append(frame)

    return frames

class BasePlayer(pygame.sprite.Sprite):

    def __init__(self, x, y, assets_folder="assets2/player1", scale=1,
             use_spritesheet=False):

        super().__init__()
        self.mobile_controls = None 
        self.scale = scale
        self.assets_folder = assets_folder 

        if not use_spritesheet:

            self.animations = {

                "idle": load_frames(f"{assets_folder}/Idle", scale),
                "walk": load_frames(f"{assets_folder}/Walk", scale),
                "dash": load_frames(f"{assets_folder}/Dash", scale),
                "attack": load_frames(f"{assets_folder}/Attack", scale),

            }

            if assets_folder == 'assets2/player_hammer':

                self.animations = {
                    "idle": load_frames(f"{assets_folder}/Idle", scale),
                    "walk": load_frames(f"{assets_folder}/Walk", 0.255),
                    "dash": load_frames(f"{assets_folder}/Dash", scale),
                    "attack": load_frames(f"{assets_folder}/Attack", scale),
                }

        else:

            if assets_folder == 'assets2/player_satyr':

                self.animations = {
                    "idle": load_spritesheet_row(f"{assets_folder}/Idle.png", 6, scale),
                    "walk": load_spritesheet_row(f"{assets_folder}/Walk.png", 7, scale),
                    "dash": load_spritesheet_row(f"{assets_folder}/Dash.png", 6, scale),
                    "attack": load_spritesheet_row(f"{assets_folder}/Attack.png", 10, scale),

            }

            elif assets_folder == 'assets2/player_archer':

                self.animations = {

                    "idle": load_frames(f"{assets_folder}/Idle", 0.23),
                    "walk": load_frames(f"{assets_folder}/Walk", 0.09),
                    "dash": load_spritesheet_row(f"{assets_folder}/Dash.png", 1, 0.23),
                    "attack": load_frames(f"{assets_folder}/Attack", 0.25),

            } 

            elif assets_folder == 'assets2/player_spear':

                self.animations = {

                    "idle": load_spritesheet_row(f"{assets_folder}/Idle.png", 1, 0.2),
                    "walk": load_frames(f"{assets_folder}/Walk", 0.056),
                    "dash": load_spritesheet_row(f"{assets_folder}/Dash.png", 1, 0.2),
                    "attack": load_frames(f"{assets_folder}/Attack", 0.2),

                }

            elif assets_folder == 'assets2/player_nakula':

                self.animations = {
                    
                    "idle": load_frames(f"{assets_folder}/Idle", 0.18),
                    "walk": load_frames(f"{assets_folder}/Walk", 0.06),
                    "dash": load_frames(f"{assets_folder}/Dash", 0.18),
                    "attack": load_frames(f"{assets_folder}/Attack", 0.4),
                }

            elif assets_folder == 'assets2/player_sadewa':

                self.animations = {
                    
                    "idle": load_frames(f"{assets_folder}/Idle", 0.18),
                    "walk": load_frames(f"{assets_folder}/Walk", 0.09),
                    "dash": load_frames(f"{assets_folder}/Dash", 0.18),
                    "attack": load_frames(f"{assets_folder}/Attack", 0.4),
                }

        self.state = "idle"
        self.frame_index = 0
        self.anim_speed = 0.05
        self.attack_anim_speed = 0.3
        self.hit_cooldown = 0

        self.image = self.animations[self.state][0]
        self.rect = self.image.get_rect(center=(x, y))

        # MOVEMENT
        self.speed = 5
        self.speed_diagonal = 1
        self.dash_speed = 25
        self.facing = 1

        # DASH
        self.dashing = False
        self.dash_timer = 0
        self.dash_duration = 10
        self.dash_cooldown = 40
        
        self.dash_dir_x = 1
        self.dash_dir_y = 0

        # ATTACK
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 25
        self._attack_key_prev = False

        # HEALTH
        self.max_health = 5
        self.health = self.max_health

        # DAMAGE
        self.damage = 1

        # ================= ULTIMATE / BOOST (semua karakter) =================
        self.ultimate_damage_mult    = 1.8     # pengali damage selama boost aktif
        self.ultimate_speed_mult     = 1.5     # pengali speed selama boost aktif
        self.ultimate_duration       = 300     # lama boost aktif (frame, ±5 detik @60fps)
        self.ultimate_cooldown_time  = 600     # cooldown sebelum bisa dipakai lagi (±10 detik)
        self.ultimate_banner_time    = 120     # lama banner tampil di layar (±2 detik)
        self.ultimate_fade_frames    = 20      # durasi fade-out di akhir tampilnya banner
        self.ultimate_banner_margin  = 16      # jarak banner dari tepi kiri layar
        self.ultimate_shake_amount   = 3       # besar goyangan banner (px)
        self.ultimate_banner_max_w   = 260     # lebar maksimum banner setelah di-scale

        self.ultimate_active         = False
        self.ultimate_timer          = 0
        self.ultimate_cooldown_timer = 0
        self.ultimate_banner_timer   = 0

        # Stat sebelum boost disimpan SAAT diaktifkan (bukan dari __init__),
        # supaya upgrade permanen dari Resi tidak ke-reset waktu boost habis.
        self._pre_ultimate_damage = self.damage
        self._pre_ultimate_speed  = self.speed
        self._ultimate_key_prev   = False

        # Banner di-load LAZY (baru di-load pertama kali benar-benar mau
        # digambar) supaya kalau asetnya belum ada, game tidak langsung
        # crash saat karakter dibuat — baru error saat ultimate/RAGE
        # pertama kali dipakai, dengan pesan yang lebih jelas.
        self.ultimate_banner_img = None
        self.rage_banner_img     = None

        # ================= RAGE (window bonus setelah cooldown ULT habis) =====
        # Setiap kali cooldown ultimate BIASA habis, ada window RAGE selama
        # rage_window_duration (±5 detik). Selama window ini, tombol ULT yang
        # sama (lihat main.py) berubah jadi tombol "RAGE!" — kalau dipencet,
        # boost yang didapat LEBIH BESAR daripada ultimate biasa, tapi honor
        # (dharma/adharma) player TURUN sebesar rage_honor_penalty setiap
        # pemakaian (lihat self.honor_system, di-attach dari main.py seperti
        # mobile_controls).
        self.rage_damage_mult     = 2.5    # pengali damage selama RAGE aktif (> ultimate biasa)
        self.rage_speed_mult      = 2.0    # pengali speed selama RAGE aktif (> ultimate biasa)
        self.rage_window_duration = 300    # lama window RAGE tersedia (frame, ±5 detik @60fps)
        self.rage_honor_penalty   = 15     # adharma yang ditambah (honor TURUN) per pemakaian RAGE

        self.rage_window_active  = False   # True selama window 5 detik tersedia
        self.rage_window_timer   = 0
        self.rage_active         = False   # True selama efek RAGE sedang berjalan (boost aktif)
        self.rage_timer          = 0
        self.rage_banner_timer   = 0

        # honor_system di-attach dari main.py (pola sama seperti
        # self.mobile_controls) — boleh None kalau belum di-attach, supaya
        # activate_rage() tidak crash kalau dipanggil sebelum di-set.
        self.honor_system = None

    def input(self):
        keys = pygame.key.get_pressed()
        mc = self.mobile_controls   
 
        dx = 0
        dy = 0
 
        moving = False
 
        # ATTACK
        attack_pressed = keys[pygame.K_p] or (mc and mc.attack)

        attack_just_pressed = attack_pressed and not self._attack_key_prev
        self._attack_key_prev = attack_pressed

        if attack_just_pressed and not self.attacking and self.attack_timer == 0:
 
            self.attacking = True
            self.state = "attack"
            self.frame_index = 0
 
 
        if self.attacking:
 
            self.anim_speed = 0.05
            return
 
        else:
 
            self.anim_speed = 5
 
 
        move_left  = keys[pygame.K_a] or (mc and mc.move_left)
        move_right = keys[pygame.K_d] or (mc and mc.move_right)
        move_up    = keys[pygame.K_w] or (mc and mc.move_up)
        move_down  = keys[pygame.K_s] or (mc and mc.move_down)

        # DASH
        dash_pressed = keys[pygame.K_LSHIFT] or (mc and mc.dash)

        if dash_pressed and not self.dashing and self.dash_timer == 0:

            self.dashing = True
            self.dash_timer = self.dash_duration
            self.state = "dash"

            
            dir_x = 0
            dir_y = 0
            if move_left:
                dir_x = -1
            if move_right:
                dir_x = 1
            if move_up:
                dir_y = -1
            if move_down:
                dir_y = 1

            if dir_x == 0 and dir_y == 0:
                # Tidak ada tombol arah ditahan — dash horizontal sesuai facing
                dir_x = self.facing

            # Normalisasi diagonal supaya kecepatan dash diagonal tidak
            # lebih cepat dari dash lurus (panjang vektor tetap 1).
            if dir_x != 0 and dir_y != 0:
                norm = (dir_x ** 2 + dir_y ** 2) ** 0.5
                dir_x /= norm
                dir_y /= norm

            self.dash_dir_x = dir_x
            self.dash_dir_y = dir_y


        if self.dashing:

            dx = self.dash_dir_x * self.dash_speed
            dy = self.dash_dir_y * self.dash_speed

            self.dash_timer -= 1

            if self.dash_timer <= 0:

                self.dashing = False
                self.dash_timer = -self.dash_cooldown


        # MOVE
        if not self.dashing:

            if move_left:
 
                dx = -self.speed
                self.facing = -1
                moving = True
 
 
            if move_right:
 
                dx = self.speed
                self.facing = 1
                moving = True
 
 
            if move_up:
 
                dy = -self.speed
                moving = True
 
 
            if move_down:
 
                dy = self.speed
                moving = True

            if move_up and move_right:
                dx = self.speed
                dy = -self.speed_diagonal
                moving = True

            if move_up and move_left:
                dx = -self.speed
                dy = -self.speed_diagonal
                moving = True

            if move_down and move_right:
                dx = self.speed
                dy = self.speed_diagonal
                moving = True

            if move_down and move_left:
                dx = -self.speed
                dy = self.speed_diagonal
                moving = True

            self.anim_speed = 0.3 if moving else 0.05
 
 
        self.rect.x += dx
        self.rect.y += dy
 
 
        if not self.dashing:
 
            self.state = "walk" if moving else "idle"
 
 
        if self.dash_timer < 0:
 
            self.dash_timer += 1
 
 
        if self.attack_timer > 0:
 
            self.attack_timer -= 1


    def animate(self):

        frames = self.animations[self.state]

        if self.state == "attack":
            self.frame_index += self.attack_anim_speed
        else:
            self.frame_index += self.anim_speed

        if self.state == "attack" and self.frame_index >= len(frames):

            self.attacking = False
            self.attack_timer = self.attack_cooldown
            self.state = "idle"
            self.frame_index = 0

        if self.frame_index >= len(frames):
            self.frame_index = 0

        center = self.rect.center
        self.image = frames[int(self.frame_index)]
        self.rect = self.image.get_rect(center=center)

        if self.facing == -1:
            self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, surface):

        # jika class punya afterimage
        if hasattr(self, "afterimages"):

            for img, pos, alpha in self.afterimages:

                temp = img.copy()
                temp.set_alpha(alpha)

                surface.blit(temp, pos)

        # gambar player utama
        surface.blit(self.image, self.rect)

    def get_attack_hitbox(self):

        if self.state != "attack":

            return None


        offset = 40 if self.facing == 1 else -40


        return pygame.Rect(

            self.rect.centerx + offset,

            self.rect.centery - 20,

            40,

            40

        )

    def take_damage(self, amount):
        if self.hit_cooldown == 0:
            self.health -= amount
            self.hit_cooldown = 20

    # ================= ULTIMATE / BOOST (semua karakter) =================
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
        terbuka (rage_window_active, beberapa detik setelah cooldown
        ultimate biasa habis). Boost yang didapat lebih besar dari ultimate
        biasa (rage_damage_mult, rage_speed_mult), TAPI honor player turun
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

    def update_ultimate(self):
        """Tracking timer ultimate/RAGE + deteksi tombol U. Dipanggil
        otomatis tiap frame dari BasePlayer.update(), jadi SEMUA karakter
        anak BasePlayer otomatis dapat fitur ini tanpa perlu menulis ulang
        kode yang sama di tiap file karakter."""

        keys = pygame.key.get_pressed()
        mc = self.mobile_controls
        ultimate_key_down = keys[pygame.K_u] or bool(mc and getattr(mc, "ultimate", False))

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
                # RAGE. Tidak terjadi kalau RAGE sendiri sedang aktif
                # (activate_rage juga menyetel ultimate_cooldown_timer,
                # jadi window tidak akan langsung dibuka lagi sebelum
                # efek RAGE selesai).
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
                # sebelum RAGE diaktifkan, lalu masuk cooldown.
                self.damage = self._pre_ultimate_damage
                self.speed  = self._pre_ultimate_speed
                self.rage_active            = False
                self.ultimate_cooldown_timer = self.ultimate_cooldown_time

        if self.ultimate_banner_timer > 0:
            self.ultimate_banner_timer -= 1

        if self.rage_banner_timer > 0:
            self.rage_banner_timer -= 1

    def _load_banner_image(self, candidates, max_w):
        """Coba load gambar banner dari beberapa kemungkinan path (jaga-jaga
        kalau ekstensi file beda, mis. .png vs .jpeg/.jpg). Pakai yang
        pertama ketemu, lalu di-scale supaya lebarnya tidak melebihi max_w."""

        img = None
        last_err = None
        for path in candidates:
            try:
                img = pygame.image.load(path).convert()
                break
            except (pygame.error, FileNotFoundError) as e:
                last_err = e
                continue

        if img is None:
            raise FileNotFoundError(
                f"Banner tidak ditemukan di salah satu path berikut: {candidates}. "
                f"Error terakhir: {last_err}"
            )

        if img.get_width() > max_w:
            ratio = max_w / img.get_width()
            new_size = (int(img.get_width() * ratio), int(img.get_height() * ratio))
            img = pygame.transform.smoothscale(img, new_size)

        return img

    def _draw_shaking_banner(self, surface, img, timer):
        """Gambar satu banner di samping kiri layar dengan sedikit efek
        shake + fade-out di akhir. Dipakai bareng oleh draw_ultimate_banner
        dan draw_rage_banner supaya logikanya tidak diduplikasi."""

        shake_x = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)
        shake_y = random.randint(-self.ultimate_shake_amount, self.ultimate_shake_amount)

        img_rect = img.get_rect(
            midleft=(self.ultimate_banner_margin, surface.get_height() // 2)
        )
        img_rect.x += shake_x
        img_rect.y += shake_y

        if timer <= self.ultimate_fade_frames:
            alpha   = int(255 * (timer / self.ultimate_fade_frames))
            banner  = img.copy()
            banner.set_alpha(alpha)
            surface.blit(banner, img_rect)
        else:
            surface.blit(img, img_rect)

    def draw_ultimate_banner(self, surface):
        """Gambar banner 'Boost!' di samping kiri layar selagi ultimate
        baru aktif, dengan efek shake. Panggil dari main.py, idealnya
        sebelum pygame.display.flip() supaya tampil di atas elemen lain."""

        if self.ultimate_banner_timer <= 0:
            return

        if self.ultimate_banner_img is None:
            self.ultimate_banner_img = self._load_banner_image(
                ["assets2/boost_banner.png", "assets2/boost_banner.jpeg", "assets2/boost_banner.jpg"],
                self.ultimate_banner_max_w,
            )

        self._draw_shaking_banner(surface, self.ultimate_banner_img, self.ultimate_banner_timer)

    def draw_rage_banner(self, surface):
        """Gambar banner 'RAGE!' di samping kiri layar selagi RAGE baru
        aktif. Posisi, ukuran, dan efek shake sama seperti
        draw_ultimate_banner, hanya gambar & timer-nya yang beda."""

        if self.rage_banner_timer <= 0:
            return

        if self.rage_banner_img is None:
            self.rage_banner_img = self._load_banner_image(
                ["assets2/rage_banner.png", "assets2/rage_banner.jpeg", "assets2/rage_banner.jpg"],
                self.ultimate_banner_max_w,
            )

        self._draw_shaking_banner(surface, self.rage_banner_img, self.rage_banner_timer)

    def update(self):

        if self.hit_cooldown > 0:
         self.hit_cooldown -= 1

        self.update_ultimate()

        self.input()

        self.animate()