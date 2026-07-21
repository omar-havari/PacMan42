"""The menu-style screens driven by the single main loop in :mod:`src.app`.

Every class here follows the same contract so the loop can treat them
uniformly: an ``__init__`` that builds its layout once, a ``handle_event`` that
returns an action string (or ``None``), and a ``draw``. None of them own a loop.
"""
import os
import sys
from typing import List, Optional, Tuple

import pygame

from src.config import Config
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
_WHITE = (255, 255, 255)
_CHEAT_COLOR = (255, 0, 255)  # magenta, matches GameDemo's cheat readout

# Task 7.3 / 8.5 / 8.6: the name-entry input rules, kept as named constants so
# the on-screen hint text and the validation can never drift apart.
_MAX_NAME_LENGTH = 10

Color = Tuple[int, int, int]


def load_font(size: int) -> pygame.font.Font:
    """Load the shared arcade font, exiting cleanly if it is missing."""
    try:
        return pygame.font.Font(_FONT, size)
    except FileNotFoundError:
        print(f"Error: font file '{_FONT}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)


class _Button:
    """A clickable text button, pre-rendered in normal and hover colours."""

    def __init__(
        self,
        label: str,
        action: str,
        font: pygame.font.Font,
        center: Tuple[float, float],
    ) -> None:
        """Pre-render the label twice and remember the ``action`` to return."""
        self.action = action
        self.normal = font.render(label, False, _TEXT_COLOR)
        self.hover = font.render(label, False, _HOVER_COLOR)
        self.rect = self.normal.get_rect(center=center)

    def draw(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]) -> None:
        """Draw the button, highlighted when the mouse is over it."""
        hovered = self.rect.collidepoint(mouse_pos)
        screen.blit(self.hover if hovered else self.normal, self.rect)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Return ``True`` for a mouse-down inside this button."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )


class MainMenu:
    """Task 8.2: four buttons plus a live preview of the top scores."""

    def __init__(self, screen: pygame.Surface, config: Config) -> None:
        """Build the title, the four buttons, the border panel and preview."""
        self.config = config
        screen_width, screen_height = screen.get_size()

        font_title = load_font(120)
        font_buttons = load_font(45)
        self.font_preview = load_font(24)

        self.title = font_title.render("Pacman", False, _TEXT_COLOR)
        self.title_box = self.title.get_rect(centerx=screen_width / 2, top=80)

        # The four required buttons, each paired with the action string app.py
        # switches on. Stacked below the title, evenly spaced.
        labels = [
            ("New Game", "NEW_GAME"),
            ("View Highscores", "HIGHSCORES"),
            ("Instructions", "INSTRUCTIONS"),
            ("Exit", "EXIT"),
        ]
        gap = 30
        y = self.title_box.bottom + 70
        self.buttons: List[_Button] = []
        for label, action in labels:
            # Build at a throwaway centre, then move the box to y so we can
            # advance y by its real rendered height.
            button = _Button(label, action, font_buttons, (screen_width / 2, 0))
            button.rect.centerx = int(screen_width / 2)
            button.rect.top = int(y)
            self.buttons.append(button)
            y += button.rect.height + gap

        # Border panel wrapping the title + buttons.
        panel = self.title_box.unionall([b.rect for b in self.buttons])
        self.panel = panel.inflate(140, 140)

        # The decorative pacman mascot, or None if the image is missing.
        self.icon: Optional[ImageElement]
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

        # Load the current top scores once, for the preview panel.
        self.top_scores = HighscoreManager(config.highscore_file).get_top10()[:5]

    def update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Show a hand cursor while over any button (Task 8.2 hover effect)."""
        over_button = any(b.rect.collidepoint(mouse_pos) for b in self.buttons)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if over_button else pygame.SYSTEM_CURSOR_ARROW
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Return the clicked button's action string (or ``"EXIT"`` on Esc)."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "EXIT"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the panel, title, buttons, icon and score preview."""
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(_BG_COLOR)
        pygame.draw.rect(
            screen, _BORDER_COLOR, self.panel, width=6, border_radius=16
        )
        screen.blit(self.title, self.title_box)
        for button in self.buttons:
            button.draw(screen, mouse_pos)
        if self.icon:
            self.icon.draw(screen)
        self._draw_preview(screen)

    def _draw_preview(self, screen: pygame.Surface) -> None:
        """Draw the "TOP SCORES" preview down the right-hand side."""
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


class HighscoresScreen:
    """Task 8.7: the full ranked top-10 highscores screen."""

    def __init__(self, screen: pygame.Surface, config: Config) -> None:
        """Reload the scores from disk so the table is always current."""
        self.font_title = load_font(70)
        self.font_row = load_font(34)
        self.scores = HighscoreManager(config.highscore_file).get_top10()

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Return ``"BACK"`` on Esc/Enter, otherwise ``None``."""
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_RETURN
        ):
            return "BACK"
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the ranked table, or "No scores yet" when empty."""
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
                screen.blit(
                    row, row.get_rect(centerx=width / 2, top=260 + (rank - 1) * 50)
                )
        hint = self.font_row.render("ESC = back", False, _DIM_COLOR)
        screen.blit(hint, hint.get_rect(center=(width / 2, height - 100)))


class InstructionsScreen:
    """Task 8.8: controls, mechanics, and (Task 9.1) the cheat keys."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Build the fixed list of instruction lines, tagged by kind."""
        self.font_title = load_font(60)
        self.font_head = load_font(26)
        self.font_line = load_font(20)
        # Each row is (text, kind); "kind" picks the colour/size so headings,
        # body lines and cheat lines are visually distinct.
        self.lines: List[Tuple[str, str]] = [
            ("CONTROLS", "head"),
            ("Arrow keys   -   move Pac-Man", "body"),
            ("P or ESC     -   pause / resume", "body"),
            ("", "body"),
            ("HOW TO PLAY", "head"),
            ("Eat every pac-gum to clear a level.", "body"),
            ("Super pac-gums turn ghosts blue and edible", "body"),
            ("for a few seconds - eat them for bonus points.", "body"),
            ("A ghost touching you costs a life; lose them", "body"),
            ("all and it's game over. Clear 10 levels to win.", "body"),
            ("", "body"),
            ("CHEAT KEYS", "head"),
            ("I - invincibility     G - freeze ghosts", "cheat"),
            ("B - speed boost       L - extra life", "cheat"),
            ("N - skip to next level", "cheat"),
        ]

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Return ``"BACK"`` on Esc/Enter, otherwise ``None``."""
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_RETURN
        ):
            return "BACK"
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the title and every instruction line, coloured by kind."""
        screen.fill(_BG_COLOR)
        width, height = screen.get_size()
        title = self.font_title.render("INSTRUCTIONS", False, _HOVER_COLOR)
        screen.blit(title, title.get_rect(center=(width / 2, 90)))
        y = 180
        for text, kind in self.lines:
            if kind == "head":
                surface = self.font_head.render(text, False, _HOVER_COLOR)
            elif kind == "cheat":
                surface = self.font_line.render(text, False, _CHEAT_COLOR)
            else:
                surface = self.font_line.render(text, False, _TEXT_COLOR)
            screen.blit(surface, surface.get_rect(center=(width / 2, y)))
            y += 42
        hint = self.font_line.render("ESC = back", False, _DIM_COLOR)
        screen.blit(hint, hint.get_rect(center=(width / 2, height - 60)))


class NameEntryScreen:
    """Tasks 8.5 / 8.6: the shared Game Over / Victory + name-entry screen.

    Shows the outcome heading and final score AND folds the Task 7.3 name-entry
    flow directly into a proper ``GameState`` (GAME_OVER / VICTORY), replacing
    the old blocking ``run_name_entry`` bridge. It owns no loop: app.py drives
    it and returns to the menu when ``handle_event`` reports ``"DONE"``.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        score: int,
        config: Config,
        title: str,
        won: bool,
    ) -> None:
        """Set up the heading (colour depends on win/lose), score and input."""
        self.score = score
        self.config = config
        self.title = title
        # Win = yellow heading (celebratory), loss = the blue theme colour.
        self.title_color = _HOVER_COLOR if won else _TEXT_COLOR
        self.font_title = load_font(80)
        self.font_body = load_font(34)
        self.name = ""

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Drive name entry; return ``"DONE"`` once saved or skipped.

        Same real-time validation as Task 7.3: only alphanumeric-or-space
        characters, capped at 10. Enter saves a non-empty name, Esc skips.
        """
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_RETURN:
            if self.name:
                HighscoreManager(self.config.highscore_file).add(
                    self.name, self.score
                )
                return "DONE"
            return None
        if event.key == pygame.K_ESCAPE:
            return "DONE"
        if event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            return None
        char = event.unicode
        if (
            len(self.name) < _MAX_NAME_LENGTH
            and len(char) == 1
            and (char.isalnum() or char == " ")
        ):
            self.name += char
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the heading, score, prompt, live-typed name and hint."""
        screen.fill(_BG_COLOR)
        width, height = screen.get_size()

        title = self.font_title.render(self.title, False, self.title_color)
        screen.blit(title, title.get_rect(center=(width / 2, height / 2 - 200)))

        score_line = self.font_body.render(f"Score  {self.score}", False, _WHITE)
        screen.blit(
            score_line, score_line.get_rect(center=(width / 2, height / 2 - 90))
        )

        prompt = self.font_body.render("Enter your name:", False, _TEXT_COLOR)
        screen.blit(prompt, prompt.get_rect(center=(width / 2, height / 2 - 20)))

        # A blinking underscore caret: get_ticks()//500 flips twice a second.
        caret = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = self.font_body.render(self.name + caret, False, _WHITE)
        screen.blit(typed, typed.get_rect(center=(width / 2, height / 2 + 50)))

        hint = self.font_body.render(
            "ENTER = save    ESC = skip", False, _DIM_COLOR
        )
        screen.blit(hint, hint.get_rect(center=(width / 2, height / 2 + 150)))


class PauseMenu:
    """Task 8.4: the translucent pause overlay with Resume / Main Menu."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Build the PAUSED title, the two buttons and the dim overlay."""
        self.font_title = load_font(90)
        font_buttons = load_font(45)
        width, height = screen.get_size()
        self.title = self.font_title.render("PAUSED", False, _HOVER_COLOR)
        self.title_box = self.title.get_rect(center=(width / 2, height / 2 - 120))
        self.buttons = [
            _Button("Resume", "RESUME", font_buttons, (width / 2, height / 2 + 10)),
            _Button(
                "Main Menu", "MAIN_MENU", font_buttons, (width / 2, height / 2 + 90)
            ),
        ]
        # A full-screen translucent black layer (alpha 180), built once.
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))

    def update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Show a hand cursor while over any button."""
        over_button = any(b.rect.collidepoint(mouse_pos) for b in self.buttons)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if over_button else pygame.SYSTEM_CURSOR_ARROW
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Return a button action, or ``"RESUME"`` on P/Esc."""
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_p
        ):
            return "RESUME"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the dim overlay, title and buttons over the frozen game."""
        screen.blit(self.overlay, (0, 0))
        screen.blit(self.title, self.title_box)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(screen, mouse_pos)
