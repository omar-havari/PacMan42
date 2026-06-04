import pygame


# Creating new class that will be placeholder for maze
class GameDemo:
    def __init__(self, screen):
        self.screen = screen

    # Creating a run_demo function to make new window appear
    def run_demo(self):
        active = True
        while active == True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    active = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        active = False

            self.screen.fill((0, 0, 0))
            pygame.display.flip()
