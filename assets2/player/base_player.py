import pygame
import os

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

    return frames

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
                    "walk": load_frames(f"{assets_folder}/Walk", 0.5),
                    "dash": load_spritesheet_row(f"{assets_folder}/Dash.png", 1, 0.2),
                    "attack": load_frames(f"{assets_folder}/Attack", 0.2),

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
        self.dash_speed = 25
        self.facing = 1

        # DASH
        self.dashing = False
        self.dash_timer = 0
        self.dash_duration = 10
        self.dash_cooldown = 40

        # ATTACK
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 25

        # HEALTH
        self.max_health = 5
        self.health = self.max_health

        # DAMAGE
        self.damage = 1


    def input(self):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        moving = False

        # ATTACK
        if keys[pygame.K_p] and not self.attacking and self.attack_timer == 0:

            self.attacking = True
            self.state = "attack"
            self.frame_index = 0


        if self.attacking:

            self.anim_speed = 0.05
            return

        else:

            self.anim_speed = 5


        # DASH
        if keys[pygame.K_LSHIFT] and not self.dashing and self.dash_timer == 0:

            self.dashing = True
            self.dash_timer = self.dash_duration
            self.state = "dash"


        if self.dashing:

            dx = self.facing * self.dash_speed

            self.dash_timer -= 1

            if self.dash_timer <= 0:

                self.dashing = False
                self.dash_timer = -self.dash_cooldown


        # MOVE
        if not self.dashing:

            if keys[pygame.K_a]:

                dx = -self.speed
                self.facing = -1
                moving = True


            if keys[pygame.K_d]:

                dx = self.speed
                self.facing = 1
                moving = True


            if keys[pygame.K_w]:

                dy = -self.speed
                moving = True


            if keys[pygame.K_s]:

                dy = self.speed
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

    def update(self):

        if self.hit_cooldown > 0:
         self.hit_cooldown -= 1

        self.input()

        self.animate()