import os
import sys

import pygame

from src.highscore import HighscoreManager
from src.pacman_images import ImageElement

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# Shared blue theme (matches the maze walls at (33, 33, 255)), reused by every
# menu-style screen so they all look like one game.
_FONT = os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf')
_BORDER_COLOR = (33, 33, 255)
_TEXT_COLOR = (90, 140, 255)
_HOVER_COLOR = (255, 255, 0)
_DIM_COLOR = (120, 120, 120)
_BG_COLOR = (0, 0, 0)


def load_font(size):
    # Same defensive font loader used across the project: a missing font is a
    # clean, explained exit instead of a traceback.
    try:
        return pygame.font.Font(_FONT, size)
    except FileNotFoundError:
        print(f"Error: font file '{_FONT}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)


# A clickable text button. It pre-renders itself in two colours (normal and
# hover) so drawing is just picking one based on the mouse position, and it
# remembers the action string the screen should return when it is clicked.
class _Button:
    def __init__(self, label, action, font, center):
        self.action = action
        self.normal = font.render(label, False, _TEXT_COLOR)
        self.hover = font.render(label, False, _HOVER_COLOR)
        self.rect = self.normal.get_rect(center=center)

    def draw(self, screen, mouse_pos):
        # collidepoint() is True when the mouse is inside this button's box.
        hovered = self.rect.collidepoint(mouse_pos)
        screen.blit(self.hover if hovered else self.normal, self.rect)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


# Task 8.2: the main menu. Four buttons plus a live preview of the top scores.
# It owns no loop of its own - app.py calls handle_event()/update_hover()/draw()
# each frame, exactly like every other screen.
class MainMenu:
    def __init__(self, screen, config):
        self.config = config
        screen_width, screen_height = screen.get_size()

        font_title = load_font(120)
        font_buttons = load_font(45)
        self.font_preview = load_font(24)

        self.title = font_title.render("Pacman", False, _TEXT_COLOR)
        self.title_box = self.title.get_rect(centerx=screen_width / 2, top=80)

        # Task 8.2: the four required buttons, each paired with the action
        # string app.py switches on. Stacked below the title, evenly spaced.
        labels = [
            ("New Game", "NEW_GAME"),
            ("View Highscores", "HIGHSCORES"),
            ("Instructions", "INSTRUCTIONS"),
            ("Exit", "EXIT"),
        ]
        gap = 30
        y = self.title_box.bottom + 70
        self.buttons = []
        for label, action in labels:
            # Build the button at a throwaway centre first, then move its box
            # to y so we can advance y by its real height.
            button = _Button(label, action, font_buttons, (screen_width / 2, 0))
            button.rect.centerx = int(screen_width / 2)
            button.rect.top = int(y)
            self.buttons.append(button)
            y += button.rect.height + gap

        # Border panel wrapping the title + buttons, same look as before.
        panel = self.title_box.unionall([b.rect for b in self.buttons])
        self.panel = panel.inflate(140, 140)

        # Task 8.2: the pacman mascot image under the panel (decorative).
        try:
            self.icon = ImageElement(
                os.path.join(
                    _ASSETS, 'images',
                    'Screenshot_From_2026-07-10_12-31-14-removebg-preview.png'
                ),
                (150, 150),
                (screen_width / 2, screen_height - 140),
            )
        except (FileNotFoundError, pygame.error):
            self.icon = None

        # Task 8.2: load the current top scores once, for the preview panel.
        self.top_scores = HighscoreManager(config.highscore_file).get_top10()[:5]

    # Task 8.2 hover effect: show a hand cursor while over any button.
    def update_hover(self, mouse_pos):
        over_button = any(b.rect.collidepoint(mouse_pos) for b in self.buttons)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if over_button else pygame.SYSTEM_CURSOR_ARROW
        )

    # Returns the clicked button's action string, or None. app.py acts on it.
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "EXIT"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(_BG_COLOR)
        pygame.draw.rect(screen, _BORDER_COLOR, self.panel, width=6, border_radius=16)
        screen.blit(self.title, self.title_box)
        for button in self.buttons:
            button.draw(screen, mouse_pos)
        if self.icon:
            self.icon.draw(screen)
        self._draw_preview(screen)

    # Task 8.2: a small "top scores" preview down the right-hand side.
    def _draw_preview(self, screen):
        screen_width = screen.get_size()[0]
        x = screen_width - 360
        heading = self.font_preview.render("TOP SCORES", False, _HOVER_COLOR)
        screen.blit(heading, (x, 80))
        if not self.top_scores:
            empty = self.font_preview.render("No scores yet", False, _DIM_COLOR)
            screen.blit(empty, (x, 130))
            return
        for rank, entry in enumerate(self.top_scores, start=1):
            row = self.font_preview.render(
                f"{rank}. {entry['name']:<10} {entry['score']}", False, _TEXT_COLOR
            )
            screen.blit(row, (x, 130 + (rank - 1) * 40))


# Task 8.7 (minimal): the full ranked highscores screen. Kept from Phase 7's
# run_highscores, now a state-driven screen (no loop of its own).
class HighscoresScreen:
    def __init__(self, screen, config):
        self.font_title = load_font(70)
        self.font_row = load_font(34)
        # Reload from disk so it's current even right after a game saved.
        self.scores = HighscoreManager(config.highscore_file).get_top10()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            return "BACK"
        return None

    def draw(self, screen):
        screen.fill(_BG_COLOR)
        width, height = screen.get_size()
        title = self.font_title.render("HIGH SCORES", False, _HOVER_COLOR)
        screen.blit(title, title.get_rect(center=(width / 2, 140)))
        if not self.scores:
            empty = self.font_row.render("No scores yet", False, _DIM_COLOR)
            screen.blit(empty, empty.get_rect(center=(width / 2, height / 2)))
        else:
            for rank, entry in enumerate(self.scores, start=1):
                row = self.font_row.render(
                    f"{rank:2d}.  {entry['name']:<10}  {entry['score']}",
                    False, _TEXT_COLOR,
                )
                screen.blit(row, row.get_rect(centerx=width / 2, top=260 + (rank - 1) * 50))
        hint = self.font_row.render("ESC = back", False, _DIM_COLOR)
        screen.blit(hint, hint.get_rect(center=(width / 2, height - 100)))


# Task 8.2 (button target) / early Task 8.8: a simple instructions screen.
# The full version (cheat keys etc.) is fleshed out in Task 8.8.
class InstructionsScreen:
    def __init__(self, screen):
        self.font_title = load_font(70)
        self.font_line = load_font(28)
        self.lines = [
            "Arrow keys  -  move Pac-Man",
            "P or ESC    -  pause the game",
            "",
            "Eat every pac-gum to clear a level.",
            "Super pac-gums make ghosts edible",
            "for a few seconds - eat them for points!",
            "Ghosts cost you a life on contact.",
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            return "BACK"
        return None

    def draw(self, screen):
        screen.fill(_BG_COLOR)
        width, height = screen.get_size()
        title = self.font_title.render("INSTRUCTIONS", False, _HOVER_COLOR)
        screen.blit(title, title.get_rect(center=(width / 2, 130)))
        for index, line in enumerate(self.lines):
            surface = self.font_line.render(line, False, _TEXT_COLOR)
            screen.blit(surface, surface.get_rect(center=(width / 2, 280 + index * 55)))
        hint = self.font_line.render("ESC = back", False, _DIM_COLOR)
        screen.blit(hint, hint.get_rect(center=(width / 2, height - 90)))


# Task 8.4: the pause overlay. app.py blits the frozen game snapshot first,
# then this draws a translucent dim layer + the PAUSED title + two buttons.
class PauseMenu:
    def __init__(self, screen):
        self.font_title = load_font(90)
        font_buttons = load_font(45)
        width, height = screen.get_size()
        self.title = self.font_title.render("PAUSED", False, _HOVER_COLOR)
        self.title_box = self.title.get_rect(center=(width / 2, height / 2 - 120))
        self.buttons = [
            _Button("Resume", "RESUME", font_buttons, (width / 2, height / 2 + 10)),
            _Button("Main Menu", "MAIN_MENU", font_buttons, (width / 2, height / 2 + 90)),
        ]
        # A full-screen translucent black layer (the 4th value is alpha:
        # 0 = invisible, 255 = solid), built once and reused each frame.
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))

    def update_hover(self, mouse_pos):
        over_button = any(b.rect.collidepoint(mouse_pos) for b in self.buttons)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if over_button else pygame.SYSTEM_CURSOR_ARROW
        )

    def handle_event(self, event):
        # P or ESC also resumes, mirroring how the pause was triggered.
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
            return "RESUME"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None

    def draw(self, screen):
        # The caller has already blitted the frozen game frame underneath.
        screen.blit(self.overlay, (0, 0))
        screen.blit(self.title, self.title_box)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(screen, mouse_pos)
