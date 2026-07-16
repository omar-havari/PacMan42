import sys

import pygame

from src.game_state import GameState
from src.GameDemo import GameDemo
from src.name_entry_UI import run_name_entry
from src.screens import (
    HighscoresScreen,
    InstructionsScreen,
    MainMenu,
    PauseMenu,
)


# Task 8.1: the ONE main loop for the whole game. It holds a GameState and,
# every frame, dispatches to exactly one screen based on that state. No screen
# has its own while-loop anymore (except run_name_entry, a temporary bridge
# until the Game Over / Victory states arrive in Tasks 8.5/8.6).
class App:
    def __init__(self, config):
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

        # The currently active screen objects. Only the one matching the
        # state is used each frame; the rest sit idle or are None.
        self.menu = MainMenu(self.screen, config)
        self.game = None
        self.highscores = None
        self.instructions = None
        self.pause_menu = None

        # Task 8.4 pause bookkeeping.
        self.pause_start = 0
        self.pause_snapshot = None

    # The single loop. Grab this frame's events once, hand them to whichever
    # screen is active, then present the frame at 60 FPS.
    def run(self):
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
            elif self.state.is_highscores():
                self._highscores_frame(events)
            elif self.state.is_instructions():
                self._instructions_frame(events)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    # --- MAIN_MENU (Task 8.2) ---
    def _main_menu_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            action = self.menu.handle_event(event)
            if action:
                self._run_menu_action(action)
                # A menu action changes the state (or quits); stop touching
                # the menu this frame so we don't draw it over the new screen.
                if not self.state.is_main_menu() or not self.running:
                    return
        self.menu.update_hover(pygame.mouse.get_pos())
        self.menu.draw(self.screen)

    def _run_menu_action(self, action):
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

    # --- GAME (Tasks 8.1 / 8.3, with pause hook for 8.4) ---
    def _game_frame(self, events):
        pygame.mouse.set_visible(False)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                # Task 8.4: pause, but only when the game is in real play
                # (not over a game-over/victory takeover screen).
                if self.game.is_pausable():
                    self._enter_pause()
                    return
            else:
                self.game.handle_event(event)

        done = self.game.update()
        self.game.draw()

        if done:
            # Task 7.3 bridge: a finished game (win or lose) still routes to
            # the blocking name-entry screen, then back to the menu. Capture
            # what we need before dropping the game object.
            score = self.game.score
            failed = self.game.failed
            self.game = None
            if not failed:
                run_name_entry(self.screen, score, self.config)
            self._return_to_menu()

    # --- PAUSE (Task 8.4) ---
    def _enter_pause(self):
        # Freeze the exact current frame: draw the game once, snapshot the
        # pixels, and remember when the pause began so _resume() knows how
        # much game time to give back.
        self.game.draw()
        self.pause_snapshot = self.screen.copy()
        self.pause_start = pygame.time.get_ticks()
        self.pause_menu = PauseMenu(self.screen)
        self.state.switch_to(GameState.PAUSE)

    def _pause_frame(self, events):
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
        # Frozen game underneath, then the dim overlay + pause menu on top.
        self.screen.blit(self.pause_snapshot, (0, 0))
        self.pause_menu.draw(self.screen)

    def _resume(self):
        # Hand the game exactly the time that elapsed while paused, so none of
        # its timers advanced during the freeze (Task 8.4).
        paused_ms = pygame.time.get_ticks() - self.pause_start
        self.game.shift_time(paused_ms)
        self.state.switch_to(GameState.GAME)

    # --- HIGHSCORES (early Task 8.7) ---
    def _highscores_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if self.highscores.handle_event(event) == "BACK":
                self.state.switch_to(GameState.MAIN_MENU)
                return
        self.highscores.draw(self.screen)

    # --- INSTRUCTIONS (Task 8.2 button / early Task 8.8) ---
    def _instructions_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if self.instructions.handle_event(event) == "BACK":
                self.state.switch_to(GameState.MAIN_MENU)
                return
        self.instructions.draw(self.screen)

    # Rebuild the menu (so its top-scores preview reflects any new save) and
    # switch back to it.
    def _return_to_menu(self):
        self.menu = MainMenu(self.screen, self.config)
        self.state.switch_to(GameState.MAIN_MENU)


def run_game(config):
    App(config).run()
