import pygame

class ImageElement:
    def __init__(self, image_path, scale_size, target_coordinates):
        # Load and scale the image
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, scale_size)
        
        # Create the rectangle box
        self.rect = self.image.get_rect()
        
        # Place the center of the image EXACTLY at your screen coordinates
        self.rect.center = target_coordinates

    def draw(self, surface):
        surface.blit(self.image, self.rect)