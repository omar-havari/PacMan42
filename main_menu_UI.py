import pygame
import sys
from pacman_images import ImageElement

# Initializing pygame
pygame.init()

# Get dimension of screen
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# Pass the FULLSCREEN flag for true fullscreen
screen = pygame.display.set_mode(
                            (screen_width, screen_height), pygame.FULLSCREEN
                        )
pygame.display.set_caption("Test")


# Creating font for main title and main title text
font_main = pygame.font.Font("PressStart2P-Regular.ttf", 300)
main_title = font_main.render("Pacman", False, (255, 255, 0))


# Creating font for buttons and the texts which will serve as buttons
font_menu_buttons = pygame.font.Font("PressStart2P-Regular.ttf", 100)
start_game = font_menu_buttons.render("New Game", False, (255, 255, 0))
high_scores = font_menu_buttons.render("High scores", False, (255, 255, 0))


# Applying dimensions
screen_width, screen_height = screen.get_size()
main_title_box = main_title.get_rect(
                                center=(
                                    screen_width / 2, screen_height / 2 - 500
                                )
                            )
start_game_box = start_game.get_rect(
                                center=(screen_width / 2, screen_height / 2)
                            )
high_scores_box = high_scores.get_rect(
                                center=(
                                    screen_width / 2, screen_height / 2 + 180
                                )
                            )


# Icons of pacman and ghosts
pacman_icon = ImageElement(
    "PacmanImages/pacman-removebg-preview.png",
    (150, 150),
    (screen_width / 2, 3 * screen_height / 4)
)


# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 3. BONUS: Add an ESCAPE key exit
        # In full screen, the 'X' button disappears
        # We need ESC to quit
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Drawing main title and buttons
    screen.fill((0, 0, 0))
    screen.blit(main_title, main_title_box)
    screen.blit(start_game, start_game_box)
    screen.blit(high_scores, high_scores_box)
    pacman_icon.draw(screen)
    pygame.display.flip()

# Quit pygame
pygame.quit()
sys.exit()
