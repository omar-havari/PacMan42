import pygame
import sys


# Creating new class that will be placeholder for maze
class GameDemo:
    def __init__(self, screen):

        self.screen = screen
        self.current_frame = 0
        self.last_switch = pygame.time.get_ticks()
        self.x = self.screen.get_width() // 2  # Initializing x-position
        self.y = self.screen.get_height() // 2  # Initializing y-position
        self.speed = 3  # Speed of movement
        self.direction = "right"  # Initial direction
        self.game_over_time = None
        # NEW: self.rotated will hold the current rotated/animated frame.
        # update() sets it, draw() reads it. It must live on self because
        # update() and draw() are now two separate calls instead of one
        # big loop, so a local variable wouldn't survive between them.
        self.rotated = None

        # *************ANIMATION SET-UP *****************
        # Load pacman images: open, half-open, closed
        figure_paths = [
            "PacmanImages/Screenshot_From_2026-06-13_15-13-44-removebg-preview.png",
            "PacmanImages/Screenshot_From_2026-06-13_15-13-58-removebg-preview.png",
            "PacmanImages/Screenshot_From_2026-06-13_15-17-12-removebg-preview.png",
        ]

        self.frames = [
            pygame.image.load(figure_paths[0]).convert_alpha(),
            pygame.image.load(figure_paths[1]).convert_alpha(),
            pygame.image.load(figure_paths[2]).convert_alpha(),
        ]
        # Scaling the pictures/frames
        self.frames = [
            pygame.transform.scale(frame, (150, 150))
            for frame in self.frames
        ]

    # NEW: small helper so we don't repeat the same try/except every time
    # we need to load a font. Added "self" since it's a method now.
    def load_path(self, path, size):
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Error: font file '{path}' not found. Cannot start the game.")
            pygame.quit()
            sys.exit(1)

    # REPLACED run_demo's event-handling block.
    # This used to be the "for event in pygame.event.get():" section
    # inside run_demo's while loop. Now it reacts to ONE event at a time,
    # passed in by the outer loop (which we build next in main_menu_UI.py).
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.direction = "left"
            elif event.key == pygame.K_RIGHT:
                self.direction = "right"
            elif event.key == pygame.K_UP:
                self.direction = "up"
            elif event.key == pygame.K_DOWN:
                self.direction = "down"
            # NOTE: K_ESCAPE used to set active = False here.
            # That variable doesn't exist anymore. ESC handling now
            # belongs to the OUTER loop (it decides whether to quit
            # the whole program or just return to the menu), not here.

    # REPLACED run_demo's movement/animation/game-over-detection logic.
    # This is everything that used to decide "what should change this
    # frame" - no drawing, no event handling, just calculations.
    def update(self):
        # FIX: moved this to the TOP of the function. Before, screen_width
        # was being used in the "if self.x < 0..." check BEFORE it was
        # ever calculated - that would have crashed.
        screen_width, screen_height = self.screen.get_size()

        # --- animation timer: switch mouth frame every 150ms ---
        now = pygame.time.get_ticks()
        if now - self.last_switch >= 150:
            self.current_frame = (self.current_frame + 1) % 3
            self.last_switch = now

        # --- movement + pick the correct rotated frame ---
        # FIX: changed "rotated = ..." to "self.rotated = ..." in all 4
        # branches, since draw() needs to read it after update() finishes.
        if self.direction == "right":
            self.x += self.speed
            self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 180)
        elif self.direction == "left":
            self.x -= self.speed
            self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 360)
        elif self.direction == "up":
            self.y -= self.speed
            self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 270)
        elif self.direction == "down":
            self.y += self.speed
            self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 90)

        # --- detect game over (x out of bounds) ---
        if self.x < 0 or self.x > screen_width:
            if self.game_over_time is None:
                self.game_over_time = pygame.time.get_ticks()

        # --- detect game over (y out of bounds) ---
        if self.y < 0 or self.y > screen_height:
            if self.game_over_time is None:
                self.game_over_time = pygame.time.get_ticks()

        # --- has the 4-second game-over screen finished showing? ---
        if self.game_over_time and pygame.time.get_ticks() - self.game_over_time >= 4000:
            return True   # tell the outer loop: game is done

        return False      # still playing

    # REPLACED run_demo's drawing logic.
    # This is everything that used to put pixels on the screen - no
    # decision-making here, it just looks at what update() already
    # decided (self.game_over_time, self.rotated, self.x, self.y).
    def draw(self):
        screen_width, screen_height = self.screen.get_size()

        if self.game_over_time:
            game_over_font = self.load_path("PressStart2P-Regular.ttf", 300)
            game_over = game_over_font.render(
                "Game Over",
                False,
                (255, 255, 0)
            )
            game_over_box = game_over.get_rect(
                center=(screen_width / 2, screen_height / 2)
            )
            self.screen.fill((0, 0, 0))
            self.screen.blit(game_over, game_over_box)
        else:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.rotated, (self.x, self.y))

        # NOTE: only flip ONCE, at the end, instead of inside every
        # branch like before - both branches need it so no point
        # repeating it three times.
        pygame.display.flip()

    # NOTE: run_demo() and its own "while active:" loop, "clock", and
    # "pygame.mouse.set_visible" calls have all been DELETED.
    # - The while loop is now built in main_menu_UI.py (one master loop
    #   for the whole program, not a separate one per screen).
    # - clock.tick(60) moves there too, since it controls the speed of
    #   EVERYTHING, not just this screen.
    # - pygame.mouse.set_visible(False) will be set once, wherever the
    #   outer loop switches INTO the game screen.