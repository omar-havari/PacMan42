# Task 0.2 / 8.1: the single source of truth for "which screen is active".
# The main loop in app.py reads this every frame and dispatches to the right
# screen, so there is exactly ONE loop instead of a separate while-loop per
# screen.
class GameState:
    MAIN_MENU = 0
    GAME = 1
    PAUSE = 2
    GAME_OVER = 3
    VICTORY = 4
    HIGHSCORES = 5
    INSTRUCTIONS = 6

    # NEW (Task 8.1): start on the main menu by default so is_*() is always
    # safe to call - previously self.state didn't exist until switch_to() ran.
    def __init__(self, state=MAIN_MENU):
        self.state = state

    def switch_to(self, state):
        self.state = state

    def is_main_menu(self):
        return self.state == GameState.MAIN_MENU

    def is_game(self):
        return self.state == GameState.GAME

    # CHANGED (Task 8.4): fixed the old "is_pauseed" typo.
    def is_paused(self):
        return self.state == GameState.PAUSE

    def is_game_over(self):
        return self.state == GameState.GAME_OVER

    def is_victory(self):
        return self.state == GameState.VICTORY

    def is_highscores(self):
        return self.state == GameState.HIGHSCORES

    def is_instructions(self):
        return self.state == GameState.INSTRUCTIONS
