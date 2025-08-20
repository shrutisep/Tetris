import pygame, sys
from game import Game
from colors import Colors

pygame.init()
pygame.joystick.init()

# Initialize the first connected joystick
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Controller connected:", joystick.get_name())

title_font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 30)

score_surface = title_font.render("Score", True, Colors.white)
next_surface = title_font.render("Next", True, Colors.white)

score_rect = pygame.Rect(320, 55, 170, 60)
next_rect = pygame.Rect(320, 215, 170, 180)

screen = pygame.display.set_mode((500, 620))
pygame.display.set_caption("Python Tetris")
clock = pygame.time.Clock()

game = Game()

GAME_UPDATE = pygame.USEREVENT
pygame.time.set_timer(GAME_UPDATE, 200)

last_move_time = 0
move_delay = 150  # ms

RED_LINE_Y = 40  # Y position of red line

# NEW → Level System Variables
level = 1
level_threshold = 500  # points needed to level up
level_up_time = 0
show_level_up = False

while True:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if game.game_over:
                game.game_over = False
                game.reset()
                level = 1
                pygame.time.set_timer(GAME_UPDATE, 200)  # reset speed
            else:
                if event.key == pygame.K_LEFT:
                    game.move_left()
                if event.key == pygame.K_RIGHT:
                    game.move_right()
                if event.key == pygame.K_DOWN:
                    game.move_down()
                if event.key == pygame.K_UP:
                    game.rotate()

        if joystick:
            if game.game_over:
                # Press any button to restart
                if any(joystick.get_button(i) for i in range(joystick.get_numbuttons())):
                    game.game_over = False
                    game.reset()
                    level = 1
                    pygame.time.set_timer(GAME_UPDATE, 200)

        if event.type == GAME_UPDATE and not game.game_over:
            game.move_down()

    # Controller Handling
    if joystick and not game.game_over:
        pygame.event.pump()
        axis_x1 = joystick.get_axis(0)
        axis_y1 = joystick.get_axis(1)
        axis_x2 = joystick.get_axis(2)
        axis_y2 = joystick.get_axis(3)

        if current_time - last_move_time > move_delay:
            if axis_x1 < -0.5:
                game.move_left()
                last_move_time = current_time
            elif axis_x1 > 0.5:
                game.move_right()
                last_move_time = current_time
            if axis_y1 > 0.5:
                game.move_down()
                last_move_time = current_time
            if axis_x2 < -0.5:
                game.move_left()
                last_move_time = current_time
            elif axis_x2 > 0.5:
                game.move_right()
                last_move_time = current_time
            if axis_y2 > 0.5:
                game.move_down()
                last_move_time = current_time

        if any(joystick.get_button(i) for i in [4]):
            game.rotate()

    # Game Over Check (block crosses red line)
    if not game.game_over:
        for row in range(len(game.grid.grid)):
            for col in range(len(game.grid.grid[row])):
                if game.grid.grid[row][col] != 0:
                    block_y = row * 30  # adjust block size if needed
                    if block_y < RED_LINE_Y + 5:
                        game.game_over = True
                        break
            if game.game_over:
                break

    # 🟢 LEVEL UP CHECK
    if not game.game_over and game.score >= level * level_threshold:
        level += 1
        show_level_up = True
        level_up_time = pygame.time.get_ticks()

        # Speed up the game
        new_speed = max(50, 200 - (level - 1) * 30)  # Minimum delay = 50ms
        pygame.time.set_timer(GAME_UPDATE, new_speed)

    # Drawing
    score_value_surface = title_font.render(str(game.score), True, Colors.white)
    level_surface = small_font.render(f"Level: {level}", True, Colors.white)  # NEW

    screen.fill(Colors.dark_blue)
    screen.blit(score_surface, (365, 20, 50, 50))
    screen.blit(next_surface, (375, 180, 50, 50))
    screen.blit(level_surface, (365, 120))  # NEW

    # Red line
    pygame.draw.line(screen, (255, 0, 0), (0, RED_LINE_Y), (300, RED_LINE_Y), 3)

    pygame.draw.rect(screen, Colors.light_blue, score_rect, 0, 10)
    screen.blit(score_value_surface, score_value_surface.get_rect(centerx=score_rect.centerx, centery=score_rect.centery))
    pygame.draw.rect(screen, Colors.light_blue, next_rect, 0, 10)

    game.draw(screen)

    # 🟢 SHOW LEVEL UP OVERLAY FOR 2 SECONDS
    if show_level_up:
        overlay = pygame.Surface((500, 620))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        level_up_surface = title_font.render(f"LEVEL {level}!", True, Colors.white)
        screen.blit(level_up_surface, level_up_surface.get_rect(center=(250, 300)))

        if pygame.time.get_ticks() - level_up_time > 2000:
            show_level_up = False

    # Game Over Screen
    if game.game_over:
        overlay = pygame.Surface((500, 620))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        game_over_surface = title_font.render("GAME OVER", True, Colors.white)
        restart_surface = small_font.render("Press any key to restart", True, Colors.white)

        screen.blit(game_over_surface, game_over_surface.get_rect(center=(250, 270)))
        screen.blit(restart_surface, restart_surface.get_rect(center=(250, 320)))

    pygame.display.update()
    clock.tick(60)
