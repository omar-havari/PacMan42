class GameState:
    MAIN_MENU = 0
    GAME = 1
    PAUSE = 2
    GAME_OVER = 3
    VICTORY = 4
    HIGHSCORES = 5
    INSTRUCTIONS = 6

    def switch_to(self,state):
        self.state = state


    def is_main_menu(self):
        return self.state == GameState.MAIN_MENU

    def is_game(self):
        return self.state == GameState.GAME

    def is_pauseed(self):
        return self.state == GameState.PAUSE

    def is_game_over(self):
        return self.state == GameState.GAME_OVER

    def is_victory(self):
        return self.state == GameState.VICTORY

    def is_highscores(self):
        return self.state == GameState.HIGHSCORES

    def is_instructions(self):
        return self.state == GameState.INSTRUCTIONS

