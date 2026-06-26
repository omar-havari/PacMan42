# PacMan42

*This activity has been created as part of the 42 curriculum.*

---

## Description

PacMan42 is a full recreation of the classic 1980 arcade game Pac-Man, built in Python using the Pygame library. The goal is to build a complete, playable game with a polished UI, ghost AI, maze generation, a persistent highscore system, and a cheat mode for peer review — following professional software development standards including type hints, docstrings, flake8 compliance, and a Makefile.

---

## Instructions

### Install dependencies
```bash
make install
```

### Run the game
```bash
make run
```

### Run in debug mode
```bash
make debug
```

### Clean temporary files
```bash
make clean
```

### Lint
```bash
make lint
make lint-strict
```

The game is launched from the command line as:
```bash
python3 pac-man.py config.json
```

---

## Chronological Build History

### Phase 0 — `pacman_images.py` — The Image Utility (Built First)

**What was built:**
A reusable `ImageElement` class that handles loading, scaling, and drawing any image onto the screen.

**Why we built it first:**
Before building any screen or game logic, we needed a reliable, reusable way to load and place images. Every visual element in the game — Pac-Man, ghosts, icons — needs to be loaded from a file, scaled to the right size, and placed at precise coordinates. Rather than repeating this logic everywhere, we built it once as a utility class.

**How it was created:**
The `ImageElement` class takes three arguments:
- `image_path` — path to the image file
- `scale_size` — a tuple `(width, height)` to scale the image to
- `target_coordinates` — where to center the image on screen

It uses:
- `pygame.image.load()` — loads the raw image file
- `.convert_alpha()` — optimizes the image for rendering with transparency
- `pygame.transform.scale()` — resizes it
- `.get_rect()` + `.center` — positions it precisely

The `draw(surface)` method blits the image onto any surface passed to it.

**The connection:**
This class is imported directly by `main_menu_UI.py` to render the Pac-Man icon on the main menu. It is the foundation for all static image rendering in the project.

---

### Phase 1 — `main_menu_UI.py` — The Main Menu (Built Second)

**What was built:**
The main entry point and game loop for the main menu screen. This is the first thing the player sees when they launch the game.

**Why we built it next:**
With image rendering available from Phase 0, we could now build the actual screen. The main menu is the root of the entire game flow — every other screen branches from it. It had to exist before the game itself because it is what launches the game.

**How it was created:**

*Pygame initialization:*
```python
pygame.init()
```
Starts all pygame modules. Must be called before anything else.

*Fullscreen setup:*
```python
info = pygame.display.Info()
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
```
Gets the monitor's resolution and creates a true fullscreen window.

*Custom font rendering:*
```python
font_main = pygame.font.Font("PressStart2P-Regular.ttf", 300)
main_title = font_main.render("Pacman", False, (255, 255, 0))
```
Loads the retro pixel font and renders text as a surface. The title and buttons are all rendered this way in yellow `(255, 255, 0)` on black.

*Rect-based positioning:*
```python
main_title_box = main_title.get_rect(center=(screen_width / 2, screen_height / 2 - 500))
```
Every text element gets a rect so it can be precisely centered on screen and used for click detection.

*Hover cursor:*
```python
if start_game_box.collidepoint(mouse_pos):
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
```
Detects if the mouse is over a button and changes the cursor to a hand icon.

*Click detection:*
```python
if event.type == pygame.MOUSEBUTTONDOWN:
    if start_game_box.collidepoint(event.pos):
        GameDemo(screen).run_demo()
```
On click, launches the game by creating a `GameDemo` instance and calling `run_demo()`.

*ESC to quit:*
Added because in fullscreen mode the window has no X button.

*The game loop:*
```
while running:
    handle events
    check mouse position
    draw everything
    pygame.display.flip()
```

**The connection:**
- Imports `ImageElement` from `pacman_images.py` to render the Pac-Man icon
- Imports `GameDemo` from `GameDemo.py` and launches it on "New Game" click
- Passes `screen` to `GameDemo` so the game renders on the same fullscreen window

---

### Phase 2 — `GameDemo.py` — The Game Screen (Built Third)

**What was built:**
The `GameDemo` class — a placeholder game screen where Pac-Man can move around the screen freely using arrow keys, with a working mouth animation and a Game Over screen when he leaves the screen boundaries.

**Why we built it next:**
The main menu needed something to launch when "New Game" is clicked. This class serves as the foundation for the real game — it establishes the game loop structure, movement system, and animation system that the full game will build on.

**How it was created:**

*`__init__` — Setup:*

The constructor initializes all state before the game loop runs:

```python
self.current_frame = 0
self.last_switch = pygame.time.get_ticks()
self.x = self.screen.get_width() // 2
self.y = self.screen.get_height() // 2
self.speed = 3
self.direction = "right"
```

- `current_frame` — which animation frame (0, 1, or 2) is currently showing
- `last_switch` — timestamp of the last frame switch, used to measure 150ms intervals
- `x`, `y` — Pac-Man's pixel position, starts at screen center
- `speed` — pixels moved per frame
- `direction` — current movement direction

*Animation loading:*
```python
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
self.frames = [
    pygame.transform.scale(frame, (150, 150))
    for frame in self.frames
]
```
Three images are loaded (mouth open, half open, closed) and stored in a list. They are then scaled to 150x150 in a second pass. `self.frames[self.current_frame]` always gives the image to draw this frame.

*`run_demo()` — The Game Loop:*

The loop has three clear sections every iteration:

**1. Event handling:**
```python
for event in pygame.event.get():
```
Listens for QUIT, ESC, and arrow keys. Arrow keys update `self.direction`.

**2. Update state (animation + movement):**

Animation timing:
```python
now = pygame.time.get_ticks()
if now - self.last_switch >= 150:
    self.current_frame = (self.current_frame + 1) % 3
    self.last_switch = now
```
`get_ticks()` returns total milliseconds since pygame started. Subtracting `last_switch` gives ms since last frame switch. When it hits 150ms, advance to the next frame and reset. `% 3` wraps 0→1→2→0.

Movement and rotation:
```python
if self.direction == "right":
    self.x += self.speed
    rotated = pygame.transform.rotate(self.frames[self.current_frame], 180)
elif self.direction == "left":
    ...
```
Each direction moves the x/y position and rotates the current animation frame to face that direction.

Game over boundary check:
```python
if self.x < 0 or self.x > self.screen.get_width():
    # show game over screen
    time.sleep(4)
    active = False
```
If Pac-Man exits the screen, a "Game Over" text is rendered and the loop ends after 4 seconds.

**3. Draw:**
```python
self.screen.fill((0, 0, 0))
self.screen.blit(rotated, (self.x, self.y))
pygame.display.flip()
clock.tick(60)
```
Clears the screen, draws Pac-Man, flips the buffer to display it, then caps at 60 FPS.

**The connection:**
- Receives `screen` from `main_menu_UI.py` and renders directly onto it
- Uses `pygame.time.Clock()` and `pygame.time.get_ticks()` for frame control
- Returns control to `main_menu_UI.py` when `active = False` (game over)

---

## Component Map

```
main_menu_UI.py  (entry point)
│
├── imports ──► pacman_images.py
│                   └── ImageElement
│                         ├── pygame.image.load()
│                         ├── pygame.transform.scale()
│                         └── surface.blit()
│
├── imports ──► GameDemo.py
│                   └── GameDemo
│                         ├── __init__()
│                         │     ├── pygame.time.get_ticks()
│                         │     ├── pygame.image.load() x3
│                         │     └── pygame.transform.scale() x3
│                         └── run_demo()
│                               ├── pygame.time.Clock()
│                               ├── pygame.event.get()
│                               ├── pygame.time.get_ticks()
│                               ├── pygame.transform.rotate()
│                               └── pygame.display.flip()
│
└── pygame (fullscreen window, font, event loop)
```

**How a single "New Game" click flows through the system:**

```
Player clicks "New Game"
        │
        ▼
main_menu_UI.py detects MOUSEBUTTONDOWN on start_game_box
        │
        ▼
GameDemo(screen) created — __init__ runs:
    loads 3 Pac-Man frames from PacmanImages/
    scales them to 150x150
    sets starting position to screen center
        │
        ▼
.run_demo() starts the game loop:
    every iteration:
        1. read keyboard → update direction
        2. check 150ms timer → advance animation frame
        3. move x/y by speed in current direction
        4. rotate current frame to face direction
        5. check boundary → game over if out of screen
        6. draw frame to screen
        7. clock.tick(60) → wait to maintain 60 FPS
        │
        ▼
active = False → run_demo() returns
        │
        ▼
main_menu_UI.py resumes its own loop → player sees main menu again
```

---

## Current State

**Fully functional:**
- Fullscreen main menu with title, buttons, and Pac-Man icon
- Hover cursor effect on buttons
- ESC to quit from anywhere
- Pac-Man spawns at screen center and moves in 4 directions with arrow keys
- Mouth animation cycles through 3 frames every 150ms
- Pac-Man sprite rotates to face movement direction
- Game Over screen displays when Pac-Man exits screen boundaries
- 60 FPS cap via pygame clock
- Return to main menu after game over

**Not yet built:**
- Maze generation and rendering
- Wall collision detection
- Pacgums and super-pacgums
- Ghost AI (chase, flee, eaten states)
- Lives system and respawn
- Scoring system
- Highscore persistence
- Timer per level
- Pause menu
- Victory screen
- Cheat mode
- Config file parser
- Packaging for Itch.io/Steam

---

## Resources

- [Pygame documentation](https://www.pygame.org/docs/)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [Original Pac-Man Wikipedia](https://en.wikipedia.org/wiki/Pac-Man)

**AI usage:** Claude (Anthropic) was used to assist with debugging syntax errors, explaining Pygame concepts (frame timing, clock, get_ticks), structuring the animation system, creating GitHub issues from the project subject, and generating this README. All code was written, reviewed, and understood by the development team before being used.
