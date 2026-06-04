import pygame


# Creating new class that will be placeholder for maze
class GameDemo:
    def __init__(self, screen):
        self.screen = screen
        self.pacman = pygame.image.load("PacmanImages/pacman-removebg-preview.png").convert_alpha()
        self.pacman = pygame.transform.scale(self.pacman, (150, 150))
        self.x = self.screen.get_width() // 2
        self.y = self.screen.get_height() // 2
        self.speed = 7

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
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.x = self.x - self.speed
            if keys[pygame.K_RIGHT]:
                self.x = self.x + self.speed
            if keys[pygame.K_UP]:
                self.y = self.y - self.speed
            if keys[pygame.K_DOWN]:
                self.y = self.y + self.speed

            if self.x < 0 or self.x > self.screen.get_width():
                print("Game over")
                active = False
            if self.y < 0 or self.y > self.screen.get_height():
                print("Game over")
                active = False
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.pacman, (self.x, self.y))
            pygame.display.flip()
