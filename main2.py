import pygame, sys
from game import Game
from colors import Colors

pygame.init()
pygame.joystick.init()

# ---------- CONTROLLER SETUP ----------
if pygame.joystick.get_count() == 0:
    print("No controller detected")
else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Controller:", joystick.get_name())

# ---------- VARIABLES ----------
last_move_time = 0
move_delay = 150  # ms

# ---------- UI ----------
title_font = pygame.font.Font(None, 40)
score_surface = title_font.render("Score", True, Colors.white)
next_surface = title_font.render("Next", True, Colors.white)
game_over_surface = title_font.render("GAME OVER", True, Colors.white)

score_rect = pygame.Rect(320, 55, 170, 60)
next_rect = pygame.Rect(320, 215, 170, 180)

screen = pygame.display.set_mode((500, 620))
pygame.display.set_caption("Python Tetris")
clock = pygame.time.Clock()

# ---------- GAME ----------
game = Game()

GAME_UPDATE = pygame.USEREVENT
pygame.time.set_timer(GAME_UPDATE, 200)

# ======================================================
#                       MAIN LOOP
# ======================================================
while True:

    for event in pygame.event.get():

        current_time = pygame.time.get_ticks()

        # -------- QUIT --------
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # -------- KEYBOARD --------
        if event.type == pygame.KEYDOWN:

            if game.game_over:
                game.game_over = False
                game.reset()

            if event.key == pygame.K_LEFT and not game.game_over:
                game.move_left()

            if event.key == pygame.K_RIGHT and not game.game_over:
                game.move_right()

            if event.key == pygame.K_DOWN and not game.game_over:
                game.move_down()
                game.update_score(0, 1)

            if event.key == pygame.K_UP and not game.game_over:
                game.rotate()

        # -------- CONTROLLER AXIS --------
        if event.type == pygame.JOYAXISMOTION and not game.game_over:

            # Left / Right
            if event.axis == 0 and current_time - last_move_time > move_delay:
                if event.value < -0.7:
                    game.move_left()
                    last_move_time = current_time

                elif event.value > 0.7:
                    game.move_right()
                    last_move_time = current_time

            # Down
            if event.axis == 1 and event.value > 0.7:
                game.move_down()
                game.update_score(0, 1)

        # -------- CONTROLLER BUTTONS --------
        if event.type == pygame.JOYBUTTONDOWN:

            # Rotate
            if event.button == 0 and not game.game_over:
                game.rotate()

            # Restart
            if event.button == 7 and game.game_over:
                game.game_over = False
                game.reset()

        # -------- GAME TIMER --------
        if event.type == GAME_UPDATE and not game.game_over:
            game.move_down()

    # ================= DRAWING =================
    score_value_surface = title_font.render(str(game.score), True, Colors.white)

    screen.fill(Colors.dark_blue)
    screen.blit(score_surface, (365, 20))
    screen.blit(next_surface, (375, 180))

    if game.game_over:
        screen.blit(game_over_surface, (320, 450))

    pygame.draw.rect(screen, Colors.light_blue, score_rect, 0, 10)
    screen.blit(
        score_value_surface,
        score_value_surface.get_rect(
            centerx=score_rect.centerx,
            centery=score_rect.centery
        )
    )

    pygame.draw.rect(screen, Colors.light_blue, next_rect, 0, 10)
    game.draw(screen)

    pygame.display.update()
    clock.tick(60)
