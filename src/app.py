"""The single ``GameState``-driven main loop for the whole game (Task 8.1).

One :class:`App` object owns the window, a :class:`~src.game_state.GameState`,
and every screen, and runs ONE loop that dispatches by state. As of Tasks
8.5/8.6 no screen owns a ``while`` loop anymore - even the end-of-game name
entry is a proper state (GAME_OVER / VICTORY) driven from here.
"""
import sys
from typing import List, Optional

import pygame

from src.config import Config
from src.game_state import GameState
from src.GameDemo import GameDemo
from src.screens import (
    HighscoresScreen,
    InstructionsScreen,
    MainMenu,
    NameEntryScreen,
    PauseMenu,
)


class App:
    """Owns the window and every screen, and runs the one dispatch loop."""

    def __init__(self, config: Config) -> None:
        """Open a fullscreen window and build the entry (main menu) screen."""
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (info.current_w, info.current_h), pygame.FULLSCREEN
        )
        pygame.display.set_caption("Pacman")

        self.config = config
        self.state = GameState(GameState.MAIN_MENU)
        self.clock = pygame.time.Clock()
        self.running = True

        # Only the screen matching the current state is used each frame; the
        # rest sit idle or are None.
        self.menu = MainMenu(self.screen, config)
        self.game: Optional[GameDemo] = None
        self.highscores: Optional[HighscoresScreen] = None
        self.instructions: Optional[InstructionsScreen] = None
        self.pause_menu: Optional[PauseMenu] = None
        # Tasks 8.5/8.6: the shared Game Over / Victory screen (name entry
        # folded in), active in the GAME_OVER and VICTORY states.
        self.end_screen: Optional[NameEntryScreen] = None

        # Task 8.4 pause bookkeeping.
        self.pause_start = 0
        self.pause_snapshot: Optional[pygame.Surface] = None

    def run(self) -> None:
        """Run the main loop: drain events, dispatch by state, present at 60 FPS."""
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            if self.state.is_main_menu():
                self._main_menu_frame(events)
            elif self.state.is_game():
                self._game_frame(events)
            elif self.state.is_paused():
                self._pause_frame(events)
            elif self.state.is_game_over() or self.state.is_victory():
                self._end_frame(events)
            elif self.state.is_highscores():
                self._highscores_frame(events)
            elif self.state.is_instructions():
                self._instructions_frame(events)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def _main_menu_frame(self, events: List[pygame.event.Event]) -> None:
        """Drive the main menu: run any button action, else draw it."""
        pygame.mouse.set_visible(True)
        for event in events:
            action = self.menu.handle_event(event)
            if action:
                self._run_menu_action(action)
                # A menu action changes the state (or quits); stop touching the
                # menu this frame so we don't draw it over the new screen.
                if not self.state.is_main_menu() or not self.running:
                    return
        self.menu.update_hover(pygame.mouse.get_pos())
        self.menu.draw(self.screen)

    def _run_menu_action(self, action: str) -> None:
        """Turn a menu action string into a concrete screen + state change."""
        if action == "NEW_GAME":
            self.game = GameDemo(self.screen, self.config)
            self.state.switch_to(GameState.GAME)
        elif action == "HIGHSCORES":
            self.highscores = HighscoresScreen(self.screen, self.config)
            self.state.switch_to(GameState.HIGHSCORES)
        elif action == "INSTRUCTIONS":
            self.instructions = InstructionsScreen(self.screen)
            self.state.switch_to(GameState.INSTRUCTIONS)
        elif action == "EXIT":
            self.running = False

    def _game_frame(self, events: List[pygame.event.Event]) -> None:
        """Advance and draw the game; enter pause on P/Esc; finish when done."""
        assert self.game is not None
        pygame.mouse.set_visible(False)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_p
            ):
                # Task 8.4: pause, but only during real play.
                if self.game.is_pausable():
                    self._enter_pause()
                    return
            else:
                self.game.handle_event(event)

        done = self.game.update()
        self.game.draw()

        if done:
            self._finish_game()

    def _finish_game(self) -> None:
        """Switch to the proper end state once a game finishes.

        A failed maze (never really played) skips straight back to the menu; a
        real win/lose builds the Game Over / Victory screen (which owns the
        name-entry flow) and switches to that state - no blocking loop.
        """
        assert self.game is not None
        if self.game.failed:
            self.game = None
            self._return_to_menu()
            return
        won = self.game.victory_time is not None
        score = self.game.score
        self.game = None
        title = "YOU WIN!" if won else "GAME OVER"
        self.end_screen = NameEntryScreen(
            self.screen, score, self.config, title, won
        )
        self.state.switch_to(GameState.VICTORY if won else GameState.GAME_OVER)

    def _end_frame(self, events: List[pygame.event.Event]) -> None:
        """Drive the Game Over / Victory screen; return to menu when done."""
        assert self.end_screen is not None
        pygame.mouse.set_visible(True)
        for event in events:
            if self.end_screen.handle_event(event) == "DONE":
                self.end_screen = None
                self._return_to_menu()
                return
        self.end_screen.draw(self.screen)

    def _enter_pause(self) -> None:
        """Freeze the current frame as a snapshot and open the pause menu."""
        assert self.game is not None
        self.game.draw()
        self.pause_snapshot = self.screen.copy()
        self.pause_start = pygame.time.get_ticks()
        self.pause_menu = PauseMenu(self.screen)
        self.state.switch_to(GameState.PAUSE)

    def _pause_frame(self, events: List[pygame.event.Event]) -> None:
        """Draw the frozen snapshot + pause menu; handle Resume / Main Menu."""
        assert self.pause_menu is not None and self.pause_snapshot is not None
        pygame.mouse.set_visible(True)
        for event in events:
            action = self.pause_menu.handle_event(event)
            if action == "RESUME":
                self._resume()
                return
            if action == "MAIN_MENU":
                # Abandon the run and go back to the menu (no score saved).
                self.game = None
                self._return_to_menu()
                return
        self.pause_menu.update_hover(pygame.mouse.get_pos())
        self.screen.blit(self.pause_snapshot, (0, 0))
        self.pause_menu.draw(self.screen)

    def _resume(self) -> None:
        """Hand the game the paused duration so no timers advanced, then resume."""
        assert self.game is not None
        paused_ms = pygame.time.get_ticks() - self.pause_start
        self.game.shift_time(paused_ms)
        self.state.switch_to(GameState.GAME)

    def _highscores_frame(self, events: List[pygame.event.Event]) -> None:
        """Drive the highscores screen; return to the menu on BACK."""
        assert self.highscores is not None
        pygame.mouse.set_visible(True)
        for event in events:
            if self.highscores.handle_event(event) == "BACK":
                self.state.switch_to(GameState.MAIN_MENU)
                return
        self.highscores.draw(self.screen)

    def _instructions_frame(self, events: List[pygame.event.Event]) -> None:
        """Drive the instructions screen; return to the menu on BACK."""
        assert self.instructions is not None
        pygame.mouse.set_visible(True)
        for event in events:
            if self.instructions.handle_event(event) == "BACK":
                self.state.switch_to(GameState.MAIN_MENU)
                return
        self.instructions.draw(self.screen)

    def _return_to_menu(self) -> None:
        """Rebuild the menu (refreshing its score preview) and switch to it."""
        self.menu = MainMenu(self.screen, self.config)
        self.state.switch_to(GameState.MAIN_MENU)


def run_game(config: Config) -> None:
    """Build and run the whole game - the entry point ``pac-man.py`` calls."""
    App(config).run()
