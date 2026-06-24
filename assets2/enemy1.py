import os
import pygame
import random

def load_frames(folder, scale=4):
    frames = []
    for file in sorted(os.listdir(folder)):
        if file.lower().endswith(".png"):
            img = pygame.image.load(os.path.join(folder, file)).convert_alpha()
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            frames.append(img)
    return frames


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

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, assets_folder='assets2/enemy1'):
        super().__init__()


        self.animations = {

                "walk": load_frames(f"{assets_folder}/Walk", 0.2),
                "die": load_frames(f"{assets_folder}/Die", 0.13),
                "attack": load_frames(f"{assets_folder}/Attack", 0.25),

            }

        # ================= HEALTHBAR SPRITE =================
        self.healthbar_frames = load_spritesheet_row(
            "assets2/healthbar_enemy.png", 
            5,
            scale=2
        )


        self.state = "walk"
        self.frame_index = 0
        self.anim_speed = 0.8

        self.image = self.animations["walk"][0]
        self.rect = self.image.get_rect(center=(x, y))

        # POSISI FLOAT
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        # STATS
        self.max_health = 10
        self.health = self.max_health
        self.speed = 1.2
        self.alive = True
        self.dying = False

        # ATTACK
        self.attack_range = 90
        self.attack_cooldown = 60
        self.attack_timer = 0
        self.attacking = False
        self.has_hit_player = False  

        # HIT
        self.hit_cooldown = 0
        self.hit_flash_timer = 0

        # KNOCKBACK
        self.knockback_x = 0

        # RESPAWN
        self.respawn_timer = 0

        self.facing = 1

    # ================= AI =================
    def ai(self, player):
        if not self.alive or self.dying:
            return

        if self.attacking:
            return

        px, py = player.rect.center
        dx = px - self.x
        dy = py - self.y

        if self.state == "attack":
            self.animations = 0.2
            self.facing = -1 if dx < 0 else 1

        else:
            self.facing = 1 if dx > 0 else -1

        if abs(dx) <= self.attack_range and self.attack_timer == 0:
            self.start_attack()
            return

        self.state = "walk"

        if abs(dx) > 3:
            self.x += self.speed if dx > 0 else -self.speed
        if abs(dy) > 3:
            self.y += self.speed if dy > 0 else -self.speed

        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

    # ================= ATTACK =================
    def start_attack(self):
        self.state = "attack"
        self.attacking = True
        self.frame_index = 0
        self.attack_timer = self.attack_cooldown
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
            45,
            60
        )

    # ================= DAMAGE =================
    def take_damage(self, direction, damage):
        if self.hit_cooldown == 0 and self.alive:
            self.health -= damage
            self.hit_cooldown = 20
            self.knockback_x = direction * 8
            self.hit_flash_timer = 6

            if self.health <= 0:
                self.start_death()

    # ================= DEATH =================
     
    def start_death(self):
        self.alive = False
        self.dying = True
        self.state = "die"
        self.frame_index = 0
        self.respawn_timer = 120
        self.hit_flash_timer = 0

    def respawn(self):
        self.health = self.max_health
        self.alive = True
        self.dying = False
        self.state = "walk"
        self.frame_index = 0

        # 🔥 RESET SEMUA FLAG
        self.attacking = False
        self.attack_timer = 0
        self.has_hit_player = False
        self.knockback_x = 0
        self.hit_cooldown = 0
        self.hit_flash_timer = 0

        # 🔥 RESET LOCK (kalau pakai sistem lock attack)
        self.locked_midbottom = None

        # posisi baru
        self.x = random.randint(80, 880)
        self.y = random.randint(80, 460)

        # 🔥 SYNC FLOAT + RECT
        self.rect.center = (int(self.x), int(self.y))

    # ================= ANIMATION =================
    def animate(self):
        frames = self.animations[self.state]
 
        self.frame_index += self.anim_speed
 
        if self.frame_index >= len(frames):
            if self.state == "die":
                self.frame_index = len(frames) - 1
            elif self.state == "attack":
                self.attacking = False
                self.state = "walk"
                self.frame_index = 0
            else:
                self.frame_index = 0
 
        # ===== FIX OFFSET =====
        old_midbottom = self.rect.midbottom  # simpan posisi kaki
 
        self.image = frames[int(self.frame_index)]
 
        # speed animasi
        if self.state == "attack":
            self.anim_speed = 0.4
        elif self.state == "die":
            self.anim_speed = 0.3
        elif self.state == "walk":
            self.anim_speed = 0.2
 
        # Flip berdasarkan facing untuk SEMUA state (termasuk "die"),
        # bukan selalu di-flip seperti sebelumnya. Sebelumnya kode lama
        # selalu memanggil flip saat state == "die" tanpa mengecek
        # facing, sehingga arah hadap mati tidak pernah benar-benar
        # mengikuti posisi player.
        if self.facing == -1:
            self.image = pygame.transform.flip(self.image, True, False)
 
        # reset rect biar gak geser
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_midbottom
 
        # hit flash
        if self.hit_flash_timer > 0:
            flash = self.image.copy()
            flash.fill((255, 255, 255, 120),
                    special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash

    # ================= UPDATE =================
    def update(self, player):
        if self.dying:
            self.animate()
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        if not self.alive:
            return

        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.knockback_x != 0:
            self.x += self.knockback_x
            self.knockback_x *= 0.85
            if abs(self.knockback_x) < 0.3:
                self.knockback_x = 0
            self.rect.centerx = int(self.x)

        self.ai(player)
        self.animate()

    # ================= HEALTH BAR =================
    def draw_healthbar(self, screen):

        # hitung index frame (0 - 4)
        ratio = self.health / self.max_health
        frame_index = int((1 - ratio) * 4)

        # biar aman
        frame_index = max(0, min(4, frame_index))

        bar_img = self.healthbar_frames[frame_index]

        # posisi di atas enemy
        bar_rect = bar_img.get_rect(
            midbottom=(self.rect.centerx, self.rect.top - 5)
        )

        screen.blit(bar_img, bar_rect)