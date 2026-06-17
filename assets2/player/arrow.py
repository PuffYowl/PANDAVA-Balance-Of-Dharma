import pygame

class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()

        # ==== SHAPE ARROW (simple pixel) ====
        self.image = pygame.Surface((20, 6), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (200, 200, 200), (0, 2, 14, 2))
        pygame.draw.polygon(self.image, (255, 255, 255), [(14,0),(20,3),(14,6)])

        self.rect = self.image.get_rect(center=(x, y))

        self.speed = 15
        self.direction = direction  # 1 kanan, -1 kiri

        if direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self):
        self.rect.x += self.speed * self.direction

        # hapus kalau keluar layar
        if self.rect.right < 0 or self.rect.left > 960:
            self.kill()