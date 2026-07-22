"""The single source of truth for which screen is currently active.

The main loop in :mod:`src.app` reads this every frame and dispatches to the
right screen, so there is exactly ONE loop for the whole game instead of a
separate ``while`` loop per screen.
"""


class GameState:
    """Holds the current screen state and answers ``is_*`` predicates.

    The class-level constants are the canonical names for each screen; storing
    one of them in :attr:`state` is the only thing the whole class tracks.
    """

    MAIN_MENU = 0
    GAME = 1
    PAUSE = 2
    GAME_OVER = 3
    VICTORY = 4
    HIGHSCORES = 5
    INSTRUCTIONS = 6

    def __init__(self, state: int = MAIN_MENU) -> None:
        """Start in ``state`` (the main menu by default).

        A default is provided so ``is_*()`` is always safe to call - previously
        ``self.state`` did not exist until :meth:`switch_to` ran.
        """
        self.state = state

    def switch_to(self, state: int) -> None:
        """Change the active state to ``state`` (the only mutator)."""
        self.state = state

    def is_main_menu(self) -> bool:
        """Return ``True`` when the main menu is active."""
        return self.state == GameState.MAIN_MENU

    def is_game(self) -> bool:
        """Return ``True`` when a game is being played."""
        return self.state == GameState.GAME

    def is_paused(self) -> bool:
        """Return ``True`` when the game is paused."""
        return self.state == GameState.PAUSE

    def is_game_over(self) -> bool:
        """Return ``True`` when the Game Over screen is active."""
        return self.state == GameState.GAME_OVER

    def is_victory(self) -> bool:
        """Return ``True`` when the Victory screen is active."""
        return self.state == GameState.VICTORY

    def is_highscores(self) -> bool:
        """Return ``True`` when the highscores screen is active."""
        return self.state == GameState.HIGHSCORES

    def is_instructions(self) -> bool:
        """Return ``True`` when the instructions screen is active."""
        return self.state == GameState.INSTRUCTIONS
