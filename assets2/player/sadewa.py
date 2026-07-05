import pygame
from .base_player import load_spritesheet_row 
from .base_player import BasePlayer, load_frames  


class Sadewa(BasePlayer):

    def __init__(self, x, y, assets_folder='assets2/player_sadewa', scale=4):

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
        self.speed = 2.3
        self.dash_speed = 18
        self.attack_cooldown = 35

        self.attack_anim_speed = 0.2  

        self.damage = 2
        self.max_health = 10
        self.health = self.max_health

        # ================= FACING (ATTACK) =================
        # Spritesheet attack orientasinya beda sama idle/walk, jadi
        # butuh aturan flip sendiri (lihat animate()). Kalau abis
        # dites arah nyerangnya masih kebalik, tinggal ganti
        # True -> False di bawah ini.
        self.attack_flip_inverted = True

        # ================= AFTERIMAGE =================
        self.afterimages = []
        self.afterimage_delay = 1
        self.afterimage_timer = 0
        self.afterimage_fade_speed = 25

        self.spawn_arrow = False
        self.nearest_enemy = None   # diisi dari game_loop via broadcast atau langsung

    # ================= UPDATE =================
    def update(self):
        keys = pygame.key.get_pressed()
        mc = self.mobile_controls

        if keys[pygame.K_d] or (mc and mc.move_right):
            self.facing = 1
        elif keys[pygame.K_a] or (mc and mc.move_left):
            self.facing = -1

        super().update()

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


    # ================= DRAW =================
    def draw(self, surface):

        for img, pos, alpha in self.afterimages:

            temp = img.copy()
            temp.set_alpha(alpha)
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

        # ANIM SPEED
        if self.state == "attack":
            self.frame_index += self.attack_anim_speed
        else:
            self.frame_index += self.anim_speed

        if self.state == 'walk':
            self.anim_speed = 0.8
        else:
            self.anim_speed = 0.05

        # END ATTACK
        if self.state == "attack" and self.frame_index >= len(frames):
            self.state = "idle"
            self.attacking = False
            self.attack_timer = self.attack_cooldown
            self.frame_index = 0
            frames = self.animations[self.state]  # refresh biar gak sempat nampilin frame attack yang lama

        if self.frame_index >= len(frames):
            self.frame_index = 0

        frame = frames[int(self.frame_index)]

        # Flip sesuai arah hadap.
        # facing == 1  -> hadap kanan
        # facing == -1 -> hadap kiri
        flip = self.facing == 1

        if self.state == "attack" and self.attack_flip_inverted:
            # Base frame attack orientasinya kebalik dari idle/walk,
            # jadi kondisi flip-nya dibalik lagi khusus state ini,
            # supaya serangan beneran ngarah ke sisi tempat karakter menghadap.
            flip = not flip

        if flip:
            frame = pygame.transform.flip(frame, True, False)

        old_pos = self.rect.midbottom
        self.image = frame
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_pos

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