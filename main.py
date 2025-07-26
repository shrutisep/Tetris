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
score_surface = title_font.render("Score", True, Colors.white)
next_surface = title_font.render("Next", True, Colors.white)
game_over_surface = title_font.render("GAME OVER", True, Colors.white)

score_rect = pygame.Rect(320, 55, 170, 60)
next_rect = pygame.Rect(320, 215, 170, 180)

screen = pygame.display.set_mode((500, 620))
pygame.display.set_caption("Python Tetris")
clock = pygame.time.Clock()

game = Game()

GAME_UPDATE = pygame.USEREVENT
pygame.time.set_timer(GAME_UPDATE, 200)

# For debounce delay
last_move_time = 0
move_delay = 150  # ms

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
            if event.key == pygame.K_LEFT and not game.game_over:
                game.move_left()
            if event.key == pygame.K_RIGHT and not game.game_over:
                game.move_right()
            if event.key == pygame.K_DOWN and not game.game_over:
                game.move_down()
            
            if event.key == pygame.K_UP and not game.game_over:
                game.rotate()

        if event.type == GAME_UPDATE and not game.game_over:
            game.move_down()

    # --- Controller Handling ---
    if joystick and not game.game_over:
        pygame.event.pump()

        axis_x1 = joystick.get_axis(0)  # Left stick horizontal
        axis_y1 = joystick.get_axis(1)  # Left stick vertical
        axis_x2= joystick.get_axis(2)  # Left stick horizontal
        axis_y2 = joystick.get_axis(3)  # Left stick vertical

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

        # Rotate if button 0 (A), left stick press (9), or right stick press (10)
        if any(joystick.get_button(i) for i in [11,0]):
            game.rotate()

        # Restart game with Start button (e.g., button 7)
        if joystick.get_button(7):
            game.game_over = False
            game.reset()

    # --- Drawing ---
    score_value_surface = title_font.render(str(game.score), True, Colors.white)

    screen.fill(Colors.dark_blue)
    screen.blit(score_surface, (365, 20, 50, 50))
    screen.blit(next_surface, (375, 180, 50, 50))

    if game.game_over:
        screen.blit(game_over_surface, (320, 450, 50, 50))
        game.game_over = False
        game.reset()

    


    pygame.draw.rect(screen, Colors.light_blue, score_rect, 0, 10)
    screen.blit(score_value_surface, score_value_surface.get_rect(centerx=score_rect.centerx, centery=score_rect.centery))
    pygame.draw.rect(screen, Colors.light_blue, next_rect, 0, 10)

    game.draw(screen)
    pygame.display.update()
    clock.tick(60)
