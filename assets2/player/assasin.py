import pygame
from .base_player import BasePlayer, load_frames

def load_spritesheet_row(path, frame_count, scale=1):
    sheet = pygame.image.load(path).convert_alpha()

    frame_width = sheet.get_width() // frame_count
    frame_height = sheet.get_height()

    frames = []

    for i in range(frame_count):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))

        if scale != 1:
            frame = pygame.transform.scale(
                frame,
                (int(frame_width * scale), int(frame_height * scale))
            )

        frames.append(frame)

    return frames

class Assasin(BasePlayer):

    def __init__(self, x, y, assets_folder='assets2/player_assasin', scale=2):
        super().__init__(x, y, assets_folder, scale)

        # ================= HEALTHBAR SPRITE =================
        self.healthbar_frames = load_spritesheet_row(
            "assets2/healthbar_assasin.png",  # sesuaikan path kamu
            5,
            scale=2
)

        self.animations = {

            "idle": load_frames(f"{assets_folder}/Idle", scale=3),

            "walk": load_frames(f"{assets_folder}/Walk", scale=1.5),

            "dash": load_frames(f"{assets_folder}/Dash", scale=1.5),

            "attack": load_frames(f"{assets_folder}/Attack", scale=3),

        }

        # === STATS ASSASIN ===
        self.speed = 4
        self.dash_speed = 18
        self.attack_cooldown = 40

        self.attack_anim_speed = 0.18

        self.damage = 2
        self.max_health = 6
        self.health = self.max_health


        # === ATTACK DASH SYSTEM ===
        self.attack_dash_speed = 14
        self.attack_dash_duration = 8
        self.attack_dash_timer = 0


        # === AFTERIMAGE SYSTEM ===
        self.afterimages = []
        self.afterimage_timer = 0
        self.afterimage_interval = 1

        self.spawn_arrow = False

    # ================= INPUT =================
    def input(self):

        keys = pygame.key.get_pressed()

        # mulai attack
        if keys[pygame.K_p] and not self.attacking and self.attack_timer == 0:

            self.attacking = True
            self.state = "attack"
            self.frame_index = 0

            # aktifkan dash
            self.attack_dash_timer = self.attack_dash_duration

        super().input()

    # ================= HEALTHBAR =================
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

    # ================= UPDATE =================
    def update(self):

        super().update()

        # attack animation lebih cepat
        if self.state == "attack":
            self.anim_speed = 0.18
        else:
            self.anim_speed = 0.25


        # DASH SAAT ATTACK
        if self.attack_dash_timer > 0:

            self.rect.x += self.facing * self.attack_dash_speed
            self.attack_dash_timer -= 1


        # AFTERIMAGE UPDATE
        self.update_afterimage()


    # ================= AFTERIMAGE =================
    def update_afterimage(self):

        if self.attack_dash_timer > 0 or self.state == "attack":

            self.afterimage_timer += 1

            if self.afterimage_timer >= self.afterimage_interval:

                self.afterimage_timer = 0

                ghost = self.image.copy()

                self.afterimages.append({
                    "image": ghost,
                    "x": self.rect.x,
                    "y": self.rect.y,
                    "alpha": 140
                })


        # fade
        for img in self.afterimages:
            img["alpha"] -= 12

        # remove
        self.afterimages = [img for img in self.afterimages if img["alpha"] > 0]


    # ================= DRAW =================
    def draw(self, surface):

        for img in self.afterimages:

            ghost = img["image"].copy()
            ghost.set_alpha(img["alpha"])

            surface.blit(ghost, (img["x"], img["y"]))

        surface.blit(self.image, self.rect)


    # ================= HITBOX =================
    def get_attack_hitbox(self):

        if self.state != "attack":
            return None

        offset = 50 if self.facing == 1 else -50

        return pygame.Rect(
            self.rect.centerx + offset,
            self.rect.centery - 30,
            60,
            50
        )