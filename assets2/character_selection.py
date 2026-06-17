import pygame
import sys

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Character Selection")

font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

characters = [
    {"name": "Scorpion", "color": (255, 180, 0)},
    {"name": "Sub-Zero", "color": (0, 180, 255)},
    {"name": "Liu Kang", "color": (200, 50, 50)},
    {"name": "Sonya", "color": (200, 180, 255)},
    {"name": "Raiden", "color": (100, 240, 240)},
    {"name": "Kitana", "color": (150, 50, 180)},
    {"name": "Jax", "color": (80, 80, 80)},
    {"name": "Kano", "color": (180, 80, 20)},
]

GRID_COLS = 4
GRID_ROWS = 2
CARD_WIDTH = 160
CARD_HEIGHT = 210
CARD_MARGIN_X = 40
CARD_MARGIN_Y = 40
START_X = (SCREEN_WIDTH - (CARD_WIDTH * GRID_COLS + CARD_MARGIN_X * (GRID_COLS - 1))) // 2
START_Y = 140

selected_index = 0
confirmed_index = None

def draw_character_card(index, rect, character, is_current, is_confirmed):
    pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=12)
    pygame.draw.rect(screen, character["color"], rect.inflate(-16, -16), border_radius=10)
    if is_current:
        pygame.draw.rect(screen, (255, 255, 255), rect, 4, border_radius=12)
    if is_confirmed:
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, rect.topleft)
        confirm_text = small_font.render("SELECTED", True, (255, 255, 255))
        screen.blit(confirm_text, (rect.centerx - confirm_text.get_width() // 2, rect.centery - 12))
    name_text = font.render(character["name"], True, (255, 255, 255))
    screen.blit(name_text, (rect.centerx - name_text.get_width() // 2, rect.bottom + 10))

def get_card_position(index):
    col = index % GRID_COLS
    row = index // GRID_COLS
    x = START_X + col * (CARD_WIDTH + CARD_MARGIN_X)
    y = START_Y + row * (CARD_HEIGHT + CARD_MARGIN_Y + 40)
    return pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

def move_cursor(dx, dy):
    global selected_index
    col = selected_index % GRID_COLS
    row = selected_index // GRID_COLS
    col = max(0, min(GRID_COLS - 1, col + dx))
    row = max(0, min(GRID_ROWS - 1, row + dy))
    selected_index = row * GRID_COLS + col

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_LEFT:
                move_cursor(-1, 0)
            elif event.key == pygame.K_RIGHT:
                move_cursor(1, 0)
            elif event.key == pygame.K_UP:
                move_cursor(0, -1)
            elif event.key == pygame.K_DOWN:
                move_cursor(0, 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                confirmed_index = selected_index

    screen.fill((15, 15, 15))

    title = font.render("Choose Your Fighter", True, (240, 240, 240))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

    for idx, character in enumerate(characters):
        rect = get_card_position(idx)
        is_current = idx == selected_index
        is_confirmed = idx == confirmed_index
        draw_character_card(idx, rect, character, is_current, is_confirmed)

    instructions = small_font.render(
        "Arrow keys to move, Enter/Space to select, Esc to quit", True, (200, 200, 200)
    )
    screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT - 40))

    if confirmed_index is not None:
        confirmed_name = characters[confirmed_index]["name"]
        status = font.render(f"Selected: {confirmed_name}", True, (255, 255, 255))
        screen.blit(status, (SCREEN_WIDTH // 2 - status.get_width() // 2, SCREEN_HEIGHT - 100))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()