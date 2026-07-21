"""A tiny helper for loading, scaling and positioning a decorative image."""
from typing import Tuple

import pygame


class ImageElement:
    """A pre-scaled image positioned by its centre, ready to blit."""

    def __init__(
        self,
        image_path: str,
        scale_size: Tuple[int, int],
        target_coordinates: Tuple[float, float],
    ) -> None:
        """Load ``image_path``, scale it, and centre it on ``target_coordinates``.

        Args:
            image_path: Path to the image file.
            scale_size: ``(width, height)`` to scale the image to.
            target_coordinates: Screen ``(x, y)`` the image's centre sits on.
        """
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, scale_size)

        self.rect = self.image.get_rect()
        self.rect.center = (int(target_coordinates[0]), int(target_coordinates[1]))

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the image onto ``surface`` at its stored position."""
        surface.blit(self.image, self.rect)
