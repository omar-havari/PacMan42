import pygame 
from src.maze_loader import MazeLoader

game = pygame.init()

screen = pygame.display.set_mode((800, 600))

maze = MazeLoader()
grid = maze.generate(15,15,42)

screen.fill((0,0,0))

maze.draw(screen, grid )
pygame.display.flip()

waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            waiting = False

pygame.quit()