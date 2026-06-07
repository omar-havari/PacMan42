import pygame
import time


# Creating new class that will be placeholder for maze
class GameDemo:
    def __init__(self, screen):
        self.screen = screen
        self.pacman = pygame.image.load(  # Loads pacman image
            "PacmanImages/pacman-removebg-preview.png"
        ).convert_alpha()
        self.pacman = pygame.transform.scale(  # Scales the image
            self.pacman, (150, 150)
        )
        self.x = self.screen.get_width() // 2  # Initializing x-position
        self.y = self.screen.get_height() // 2  # Initializing y-position
        self.speed = 7  # Speed of movement
        self.direction = "right"  # Initial direction

    # Creating a run_demo function to make new window appear
    def run_demo(self):
        active = True
        while active is True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    active = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        active = False
                    if event.key == pygame.K_LEFT:
                        self.direction = "left"
                    if event.key == pygame.K_RIGHT:
                        self.direction = "right"
                    if event.key == pygame.K_UP:
                        self.direction = "up"
                    if event.key == pygame.K_DOWN:
                        self.direction = "down"

            if self.direction == "right":
                self.x += self.speed
                rotated = self.pacman
            elif self.direction == "left":
                self.x -= self.speed
                rotated = pygame.transform.rotate(self.pacman, 180)
            elif self.direction == "up":
                self.y -= self.speed
                rotated = pygame.transform.rotate(self.pacman, 90)
            elif self.direction == "down":
                self.y += self.speed
                rotated = pygame.transform.rotate(self.pacman, 270)

            screen_width, screen_height = self.screen.get_size()

            if (self.x < 0 or self.x > self.screen.get_width()):
                game_over_font = pygame.font.Font(
                    "PressStart2P-Regular.ttf", 300
                )
                game_over = game_over_font.render(
                    "Game Over",
                    False,
                    (255, 255, 0)
                    )
                game_over_box = game_over.get_rect(
                    center=(screen_width / 2, screen_height / 2)
                )
                self.screen.fill((0, 0, 0))
                self.screen.blit(game_over, game_over_box)
                pygame.mouse.set_visible(False)
                pygame.display.flip()
                time.sleep(4)
                active = False

            if self.y < 0 or self.y > self.screen.get_height():
                game_over_font = pygame.font.Font(
                    "PressStart2P-Regular.ttf", 300
                )
                game_over = game_over_font.render(
                    "Game Over", False, (255, 255, 0)
                )
                game_over_box = game_over.get_rect(
                    center=(screen_width / 2, screen_height / 2)
                )
                self.screen.fill((0, 0, 0))
                self.screen.blit(game_over, game_over_box)
                pygame.mouse.set_visible(False)
                pygame.display.flip()
                time.sleep(4)
                active = False

            self.screen.fill((0, 0, 0))
            self.screen.blit(rotated, (self.x, self.y))
            pygame.display.flip()
