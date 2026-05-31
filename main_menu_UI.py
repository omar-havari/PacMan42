import pygame
import sys

# Initializing pygame
pygame.init()

# 1. Get dimension of screen
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# 2. Pass the FULLSCREEN flag for true fullscreen
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Test")

font = pygame.font.Font("PressStart2P-Regular.ttf", 300)
main_title = font.render("Pacman", False, (255, 255, 0))

screen_width, screen_height = screen.get_size()
text_box = main_title.get_rect(center = (screen_width / 2, screen_height / 2 - 500))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 3. BONUS: Add an ESCAPE key exit
        # In full screen, the 'X' button disappears, so you need a keyboard shortcut to escape!
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        
        screen.fill((0, 0, 0))
        screen.blit(main_title, text_box)
        pygame.display.flip()

# Quit pygame
pygame.quit()
sys.exit()
