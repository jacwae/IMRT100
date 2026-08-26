import random
import sys

import pygame


WIDTH = 800
HEIGHT = 480
GROUND_Y = 385
FPS = 60

BACKGROUND = (247, 244, 234)
INK = (35, 41, 38)
GROUND = (104, 116, 102)
CACTUS = (49, 111, 78)
ACCENT = (225, 111, 72)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Dino Run")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 64)


def draw_dinosaur(surface, rectangle):
    pygame.draw.rect(surface, INK, rectangle)
    pygame.draw.rect(
        surface,
        INK,
        (rectangle.x + rectangle.width - 8, rectangle.y - 22, 16, 28),
    )
    pygame.draw.rect(surface, BACKGROUND, (rectangle.right - 7, rectangle.y - 15, 4, 4))
    pygame.draw.rect(surface, INK, (rectangle.x + 6, rectangle.bottom - 2, 7, 18))
    pygame.draw.rect(surface, INK, (rectangle.right - 13, rectangle.bottom - 2, 7, 18))


def draw_cactus(surface, rectangle):
    pygame.draw.rect(surface, CACTUS, rectangle)
    pygame.draw.rect(surface, CACTUS, (rectangle.x - 10, rectangle.y + 18, 10, 8))
    pygame.draw.rect(surface, CACTUS, (rectangle.x - 10, rectangle.y + 10, 8, 16))
    pygame.draw.rect(surface, CACTUS, (rectangle.right, rectangle.y + 32, 10, 8))
    pygame.draw.rect(surface, CACTUS, (rectangle.right + 2, rectangle.y + 24, 8, 16))


def reset_game():
    return {
        "dinosaur": pygame.Rect(100, GROUND_Y - 58, 42, 58),
        "vertical_speed": 0.0,
        "obstacles": [],
        "obstacle_timer": 80,
        "score": 0,
        "game_over": False,
        "ground_offset": 0,
    }


game = reset_game()
running = True

while running:
    jump_requested = False
    restart_requested = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP):
                jump_requested = True
            elif event.key == pygame.K_r:
                restart_requested = True
            elif event.key == pygame.K_ESCAPE:
                running = False

    if restart_requested and game["game_over"]:
        game = reset_game()

    dinosaur = game["dinosaur"]

    if not game["game_over"]:
        if jump_requested and dinosaur.bottom >= GROUND_Y:
            game["vertical_speed"] = -16

        game["vertical_speed"] += 0.8
        dinosaur.y += int(game["vertical_speed"])
        if dinosaur.bottom >= GROUND_Y:
            dinosaur.bottom = GROUND_Y
            game["vertical_speed"] = 0

        game["obstacle_timer"] -= 1
        if game["obstacle_timer"] <= 0:
            height = random.choice((35, 45, 60))
            width = random.choice((18, 24, 30))
            game["obstacles"].append(
                pygame.Rect(WIDTH + 20, GROUND_Y - height, width, height)
            )
            game["obstacle_timer"] = random.randint(65, 115)

        for obstacle in game["obstacles"]:
            obstacle.x -= 7

        game["obstacles"] = [
            obstacle for obstacle in game["obstacles"] if obstacle.right > 0
        ]
        game["score"] += 1
        game["ground_offset"] = (game["ground_offset"] + 7) % 40

        dinosaur_hitbox = dinosaur.inflate(-10, -8)
        if any(dinosaur_hitbox.colliderect(obstacle) for obstacle in game["obstacles"]):
            game["game_over"] = True

    screen.fill(BACKGROUND)
    pygame.draw.line(screen, GROUND, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    for x in range(-40, WIDTH + 40, 40):
        line_x = x - game["ground_offset"]
        pygame.draw.line(screen, GROUND, (line_x, GROUND_Y + 14), (line_x + 16, GROUND_Y + 14), 2)

    draw_dinosaur(screen, dinosaur)
    for obstacle in game["obstacles"]:
        draw_cactus(screen, obstacle)

    score_text = font.render(f"SCORE {game['score'] // 6:04d}", True, INK)
    screen.blit(score_text, (WIDTH - score_text.get_width() - 24, 24))

    if game["game_over"]:
        title = big_font.render("GAME OVER", True, ACCENT)
        prompt = font.render("SPACE to jump    R to restart", True, INK)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 24)))
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 32)))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
