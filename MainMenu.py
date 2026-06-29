import pygame
import sys

# Initializing pygame
pygame.init()

s_width = pygame.display.Info().current_w
s_height = pygame.display.Info().current_h

# Screen dimensions
screen = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption("Test")

font = pygame.font.Font(None, 50)

text = font.render("Your Message Here", True, (255, 255, 255))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Clear the screen with a background color (so text doesn't smear)
    screen.fill((0, 0, 0)) 

    # 2. Draw the text inside the loop
    screen.blit(text, (s_width / 2 - 200, s_height / 2))

    # 3. Refresh the display to show the changes
    pygame.display.flip()

# Quit pygame
pygame.quit()
