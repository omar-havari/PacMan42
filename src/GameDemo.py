from src.Player import Player


# Creating new class that will be placeholder for maze
class GameDemo:
    def __init__(self, screen, config):
        self.config = config  # Used to assign values to all the parameters needed
        self.player = Player(screen, config.lives)  # Initiating player object

    def handle_event(self, event):
        self.player.handle_event(event)
    
    def update(self):
        return self.player.update()
    
    def draw(self):
        self.player.draw()