# Phase 8 (Tasks 8.1–8.4) — Unified UI & Screens — Change Log

This document walks through **every change made for Tasks 8.1–8.4**, in the
exact order the work was done. For each step it explains:

- **What the step contributes to the project** (why it matters).
- **A line-by-line reading of the code** (what each line does syntactically).

Phase 8 is the big architecture change flagged since Phase 0: replace the
per-screen `while` loops with **one** main loop driven by `GameState`, then hang
the Main Menu, the in-game HUD, and the Pause menu off that loop.

### The core idea (why this refactor exists)

Before, `src/main_menu_UI.py` owned a loop that flipped between "in menu" and
"in game", and every other screen (name entry, highscores) ran its *own*
blocking `while` loop. Adding pause, instructions, victory, etc. that way means
a new loop each time — unmanageable. Task 8.1 fixes this: a single loop asks
"what state am I in?" every frame and draws exactly one screen. Every screen
becomes a small object with `handle_event()` / `draw()` methods instead of a
loop.

Files changed, in order:

1. `src/game_state.py` — made the state object usable as the loop's backbone
2. `src/maze_loader.py` — reserve a top strip for the HUD (Task 8.3)
3. `src/Player.py`, `src/ghost.py` — `shift_time()` for pause (Task 8.4)
4. `src/GameDemo.py` — HUD bar + `shift_time()` + `is_pausable()` (8.3 / 8.4)
5. `src/screens.py` — **new**: MainMenu, Highscores, Instructions, Pause
6. `src/app.py` — **new**: the single `GameState`-driven main loop (8.1)
7. `pac-man.py` — points at the new loop; `src/main_menu_UI.py` deleted

---

## Step 1 — `src/game_state.py`: make the state object the loop's backbone

### What this contributes
`GameState` already existed (from Task 0.2) but was never used and would crash
if you called `is_game()` before `switch_to()` (the `self.state` attribute
didn't exist yet). This step makes it safe to use as the very first thing the
main loop checks each frame.

### Line-by-line

```python
class GameState:
    MAIN_MENU = 0
    GAME = 1
    PAUSE = 2
    GAME_OVER = 3
    VICTORY = 4
    HIGHSCORES = 5
    INSTRUCTIONS = 6
```
- These are **class attributes** used as named constants. `GameState.GAME` reads
  far better than a bare `1`, and there's one canonical spelling of each state.

```python
    def __init__(self, state=MAIN_MENU):
        self.state = state
```
- `def __init__(self, state=MAIN_MENU):` — the constructor. `state=MAIN_MENU` is a
  **default argument**: `GameState()` starts on the menu, but a caller can pass a
  different start state. (`MAIN_MENU` is visible here because the default is
  evaluated while the class body is still executing.)
- `self.state = state` — store the current state on the instance. This is the one
  attribute the whole class revolves around.

```python
    def switch_to(self, state):
        self.state = state
```
- The only way the state ever changes: assign a new constant. Every screen
  transition in `app.py` goes through this.

```python
    def is_paused(self):
        return self.state == GameState.PAUSE
```
- One `is_*` predicate per state (only `is_paused` shown). `==` compares the
  stored value to the constant and returns a bool. **CHANGED:** the old method
  was misspelled `is_pauseed`; fixed to `is_paused`. The rest (`is_main_menu`,
  `is_game`, `is_highscores`, `is_instructions`, …) follow the identical pattern.

---

## Step 2 — `src/maze_loader.py`: reserve a top strip for the HUD (Task 8.3)

### What this contributes
Task 8.3 requires the HUD to *never overlap the maze*. The clean way to
guarantee that is geometric: shrink the area the maze is allowed to use so it
starts **below** a reserved HUD bar. This one change to the layout math makes
overlap impossible — the player, pacgums and ghosts all derive their pixel
positions from this same function, so they all move down together.

### Line-by-line (the changed method)

```python
    def get_layout(self, screen, grid, top_margin=0):
        rows = len(grid)
        cols = len(grid[0])
        screen_width = screen.get_width()
        screen_height = screen.get_height()
```
- `top_margin=0` — **new** parameter. Default 0 means "no reserved strip", so any
  old call still behaves exactly as before.
- `rows` / `cols` — the grid's dimensions (`len(grid)` = number of rows,
  `len(grid[0])` = length of the first row = number of columns).
- `screen_width` / `screen_height` — the window size in pixels.

```python
        available_height = screen_height - top_margin
        cell = min(screen_width // cols, available_height // rows)
```
- `available_height = screen_height - top_margin` — the maze may only use the
  screen height *minus* the reserved strip.
- `cell = min(screen_width // cols, available_height // rows)` — the size of one
  square cell. `//` is integer division. Taking the **smaller** of "pixels per
  column" and "pixels per row" keeps cells square and guarantees the whole maze
  fits in the available box (no stretching, no clipping).

```python
        offset_x = (screen_width - cell * cols) // 2
        offset_y = top_margin + (available_height - cell * rows) // 2
        return cell, offset_x, offset_y
```
- `offset_x` — left letterbox: the leftover horizontal space, halved, so the maze
  is centred left-to-right.
- `offset_y = top_margin + (available_height - cell * rows) // 2` — **the key
  line.** It centres the maze within the *available* area and then adds
  `top_margin`, pushing the whole maze past the reserved strip. Because the
  second term is `>= 0`, `offset_y` is always `>= top_margin` — the maze can
  never start inside the HUD bar.
- `return cell, offset_x, offset_y` — hand back the three numbers every drawable
  object uses to place itself.

```python
    def draw(self, screen, grid, top_margin=0):
        ...
        cell, offset_x, offset_y = self.get_layout(screen, grid, top_margin)
```
- `draw()` gained the same `top_margin` parameter and forwards it to
  `get_layout`, so the drawn walls line up with the shifted layout.

---

## Step 3 — `Player.shift_time()` and ghost `shift_time()` (Task 8.4 groundwork)

### What this contributes
Pause has a subtle trap: every timer in this game is an **absolute** timestamp
compared against `pygame.time.get_ticks()` (the milliseconds-since-start wall
clock). If you simply stop calling `update()`, the wall clock keeps advancing,
so on resume the level timer would have "lost" the paused seconds, the fright
window would have expired, the ready-countdown would have skipped, etc. The fix
is to slide every timestamp **forward** by the paused duration on resume. This
step adds that capability to the player and the ghosts; Step 4 adds it to
`GameDemo` and ties it together.

### `src/Player.py`

```python
    def shift_time(self, delta):
        self.invincible_until += delta
        self.last_switch += delta
        if self.game_over_time:
            self.game_over_time += delta
```
- `def shift_time(self, delta):` — `delta` is how many milliseconds the pause
  lasted.
- `self.invincible_until += delta` — push the respawn-invincibility deadline
  forward, so the grace window resumes with the same time left.
- `self.last_switch += delta` — the mouth-animation timer, so the animation
  doesn't jump on resume.
- `if self.game_over_time:` — `game_over_time` is `None` during normal play
  (falsy), a timestamp once you die (truthy). Only shift it when it's actually
  set, so we never do `None + delta` (which would crash).

### `src/ghost.py`

```python
    def shift_time(self, delta):
        if self.eaten_until:
            self.eaten_until += delta
```
- A ghost's only absolute timer is `eaten_until` (when an eaten ghost respawns).
  `0` means "not eaten" (falsy), so `if self.eaten_until:` shifts it only when a
  respawn is genuinely pending.

```python
    def shift_time(self, delta):          # on GhostManager
        for ghost in self.ghosts:
            ghost.shift_time(delta)
```
- `GhostManager` owns the four ghosts, so its `shift_time` just loops and
  forwards the shift to each — `GameDemo` only ever talks to the manager.

---

## Step 4 — `src/GameDemo.py`: HUD bar, `shift_time()`, `is_pausable()`

### What this contributes
This wires the HUD strip (8.3) into the real game screen and completes the pause
machinery (8.4): it tells the maze to keep the top strip clear, draws the
four readouts into it, exposes `is_pausable()` so the loop knows when pausing is
allowed, and exposes `shift_time()` to un-freeze cleanly.

### 4a — the reserved-height constant

```python
_HUD_HEIGHT = 60
```
- A module-level constant: the HUD strip is 60 px tall. Used both to shrink the
  maze and to lay out the HUD, so the two can't disagree.

### 4b — pass the margin wherever the layout is computed

```python
cell, offset_x, offset_y = self.maze.get_layout(self.screen, self.grid, _HUD_HEIGHT)
```
- In `_start_level()` **and** `_restart_level_in_place()`, the layout is now
  computed with `_HUD_HEIGHT`. Since the player, pacgums and ghosts are all built
  from these returned offsets, the entire playfield sits below the HUD.

```python
self.maze.draw(self.screen, self.grid, _HUD_HEIGHT)
```
- In `draw()`, the maze is drawn with the same margin, so the walls match.

### 4c — `is_pausable()`

```python
    def is_pausable(self):
        return (
            not self.failed
            and not self.victory_time
            and not self.player.game_over_time
        )
```
- Returns `True` only during genuine play. `not self.failed` — the maze actually
  built; `not self.victory_time` — the "You Win!" screen isn't up;
  `not self.player.game_over_time` — the "Game Over" screen isn't up. `and`
  short-circuits, so any one of these being set blocks pausing. This stops you
  pausing *over* a full-screen takeover, which would look broken.

### 4d — `shift_time()`

```python
    def shift_time(self, delta):
        self.countdown_until += delta
        self.level_start_time += delta
        self.fright_until += delta
        if self.victory_time:
            self.victory_time += delta
        if self.time_up_freeze_until is not None:
            self.time_up_freeze_until += delta
        if self.ghost_death_freeze_until is not None:
            self.ghost_death_freeze_until += delta
        self.player.shift_time(delta)
        self.ghosts.shift_time(delta)
```
- Shifts **every** absolute deadline `GameDemo` owns forward by `delta`:
  - `countdown_until` — the "Ready" countdown end.
  - `level_start_time` — the anchor the level timer counts from (this is what
    makes the on-screen "TIME" freeze across a pause).
  - `fright_until` — when the current super-pacgum effect ends.
  - `victory_time` / `time_up_freeze_until` / `ghost_death_freeze_until` — these
    are `None`/optional, so each is guarded with `if ... is not None`/truthy
    before shifting (avoids `None + delta`).
- `self.player.shift_time(delta)` / `self.ghosts.shift_time(delta)` — fan the same
  shift out to the player and ghosts (Step 3). After this call, the game behaves
  as if the pause consumed zero game time.

### 4e — the HUD itself

```python
        self.maze.draw(self.screen, self.grid, _HUD_HEIGHT)
        self.pacgums.draw(self.screen)
        self.ghosts.draw(self.screen)
        self.player.draw()

        self._draw_hud()
```
- Same layered draw order as before (maze → pacgums → ghosts → player), now
  finished by a dedicated `_draw_hud()` call instead of an inline one-liner.

```python
    def _draw_hud(self):
        time_left = max(
            0,
            self.config.level_max_time
            - (pygame.time.get_ticks() - self.level_start_time) // 1000,
        )
```
- `pygame.time.get_ticks() - self.level_start_time` — milliseconds elapsed this
  level; `// 1000` converts to whole seconds.
- `self.config.level_max_time - ...` — seconds remaining.
- `max(0, ...)` — clamp so it never shows a negative number on the frame the
  timer hits zero.

```python
        items = [
            f"SCORE {self.score}",
            f"LEVEL {self.level}",
            f"LIVES {self.player.lives}",
            f"TIME {time_left}",
        ]
        screen_width = self.screen.get_width()
        slice_width = screen_width / len(items)
        for index, text in enumerate(items):
            surface = self.hud_font.render(text, False, (255, 255, 0))
            x = slice_width * index + (slice_width - surface.get_width()) / 2
            y = (_HUD_HEIGHT - surface.get_height()) / 2
            self.screen.blit(surface, (x, y))
```
- `items` — the four required readouts (Task 8.3) as f-strings.
- `slice_width = screen_width / len(items)` — divide the bar into four equal
  columns.
- `for index, text in enumerate(items):` — `enumerate` gives the column index
  (0–3) with each string.
- `surface = self.hud_font.render(text, False, (255, 255, 0))` — render the text
  yellow (`False` = no anti-aliasing, matching the arcade font).
- `x = slice_width * index + (slice_width - surface.get_width()) / 2` — the left
  edge of this column, plus the gap needed to **centre** the text within its
  column.
- `y = (_HUD_HEIGHT - surface.get_height()) / 2` — vertically centre it in the
  60 px strip.
- `self.screen.blit(surface, (x, y))` — draw it. Everything lands inside the
  reserved strip, so it can't touch the maze.

---

## Step 5 — `src/screens.py` (new): the menu-style screens

### What this contributes
This is where Tasks 8.2 (Main Menu) and 8.4 (Pause menu) live, plus state-driven
versions of the highscores and instructions screens. Every class here follows
the same contract so the main loop can treat them uniformly: an `__init__` that
builds its layout once, a `handle_event()` that returns an **action string** (or
`None`), and a `draw()`. None of them own a loop.

### 5a — shared theme + font loader

```python
_FONT = os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf')
_BORDER_COLOR = (33, 33, 255)
_TEXT_COLOR = (90, 140, 255)
_HOVER_COLOR = (255, 255, 0)
...
def load_font(size):
    try:
        return pygame.font.Font(_FONT, size)
    except FileNotFoundError:
        print(f"Error: font file '{_FONT}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)
```
- Module-level colour constants so all screens share one palette.
- `load_font(size)` — the project's standard defensive loader: a missing font is
  a clean exit (`sys.exit(1)` = non-zero = failure), never a traceback.

### 5b — the reusable `_Button`

```python
class _Button:
    def __init__(self, label, action, font, center):
        self.action = action
        self.normal = font.render(label, False, _TEXT_COLOR)
        self.hover = font.render(label, False, _HOVER_COLOR)
        self.rect = self.normal.get_rect(center=center)
```
- Pre-renders the label **twice** (normal blue, hover yellow) so drawing is just
  picking one — no re-rendering each frame.
- `self.action` — the string the owning screen returns when this button is
  clicked (e.g. `"NEW_GAME"`).
- `self.rect = self.normal.get_rect(center=center)` — the clickable box, sized to
  the text and positioned by its centre.

```python
    def draw(self, screen, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        screen.blit(self.hover if hovered else self.normal, self.rect)
```
- `self.rect.collidepoint(mouse_pos)` — `True` when the cursor is inside the box.
- `self.hover if hovered else self.normal` — a conditional expression choosing
  which pre-rendered surface to draw.

```python
    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        )
```
- `True` only for a mouse-down **inside** this button. `event.pos` is where the
  click happened.

### 5c — `MainMenu` (Task 8.2)

```python
    def __init__(self, screen, config):
        self.config = config
        screen_width, screen_height = screen.get_size()
        font_title = load_font(120)
        font_buttons = load_font(45)
        self.font_preview = load_font(24)
        self.title = font_title.render("Pacman", False, _TEXT_COLOR)
        self.title_box = self.title.get_rect(centerx=screen_width / 2, top=80)
```
- Reads the screen size and renders the big "Pacman" title, positioned by its
  horizontal centre with its top 80 px down.

```python
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
            button = _Button(label, action, font_buttons, (screen_width / 2, 0))
            button.rect.centerx = int(screen_width / 2)
            button.rect.top = int(y)
            self.buttons.append(button)
            y += button.rect.height + gap
```
- `labels` — the **four required buttons** (Task 8.2), each paired with its action
  string.
- The loop builds one `_Button` per entry, stacks them vertically (`y` advances by
  each button's height plus the gap), and collects them in `self.buttons`. Making
  the button at a throwaway centre then setting `rect.top = y` lets us use its
  real rendered height for spacing.

```python
        panel = self.title_box.unionall([b.rect for b in self.buttons])
        self.panel = panel.inflate(140, 140)
```
- `unionall([...])` — the smallest rectangle that contains the title **and** every
  button box.
- `.inflate(140, 140)` — grow it 70 px on each side for padding; this is the blue
  border panel drawn around the menu.

```python
        try:
            self.icon = ImageElement(..., (150, 150), (screen_width / 2, screen_height - 140))
        except (FileNotFoundError, pygame.error):
            self.icon = None
        self.top_scores = HighscoreManager(config.highscore_file).get_top10()[:5]
```
- The decorative pacman image, wrapped in `try/except` so a missing image degrades
  to "no icon" instead of crashing.
- `self.top_scores = ...[:5]` — **Task 8.2 preview:** load the current scores and
  keep the top 5. Reading them here (in `__init__`) means the preview reflects the
  file as it was when the menu was built — and `app.py` rebuilds the menu after
  each game, so it stays current.

```python
    def update_hover(self, mouse_pos):
        over_button = any(b.rect.collidepoint(mouse_pos) for b in self.buttons)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if over_button else pygame.SYSTEM_CURSOR_ARROW
        )
```
- `any(... for b in self.buttons)` — `True` if the cursor is over *any* button.
- Switches to a hand cursor over buttons, arrow otherwise — **Task 8.2's hover
  effect.**

```python
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "EXIT"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None
```
- Esc is a shortcut for Exit. Otherwise, if a button was clicked, return its
  action; else `None`. The loop in `app.py` switches on this string.

```python
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
```
- Clear to black, draw the rounded border panel (`width=6` = outline only,
  `border_radius=16` = rounded corners), the title, each button (hover-aware), the
  icon if present, then the scores preview.

```python
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
```
- Draws the preview down the right side (`x = screen_width - 360`).
- `if not self.top_scores:` — empty list is falsy → show "No scores yet".
- Otherwise `enumerate(..., start=1)` numbers the rows 1..5; `{entry['name']:<10}`
  left-aligns the name in a 10-wide field so the scores line up; each row is 40 px
  lower than the last.

### 5d — `HighscoresScreen` and `InstructionsScreen`

These follow the exact same `__init__` / `handle_event` → `"BACK"` / `draw`
contract. `HighscoresScreen` is Phase 7's `run_highscores` with its `while` loop
removed (the loop now lives in `app.py`); it reloads the file so it's current and
renders the ranked top-10 (or "No scores yet"). `InstructionsScreen` renders a
fixed list of control/mechanic lines. Both return `"BACK"` on Esc/Enter. The
per-line rendering is the same `render` → `get_rect(center=...)` → `blit` pattern
explained above.

### 5e — `PauseMenu` (Task 8.4)

```python
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
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))
```
- Builds the "PAUSED" title and the two required buttons (Resume, Main Menu).
- `pygame.Surface((width, height), pygame.SRCALPHA)` — a full-screen surface **with
  an alpha channel** (per-pixel transparency).
- `self.overlay.fill((0, 0, 0, 180))` — fill it black at alpha `180` (out of 255):
  a translucent dim layer, so the frozen game shows faintly through the pause menu.

```python
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
            return "RESUME"
        for button in self.buttons:
            if button.is_clicked(event):
                return button.action
        return None
```
- `event.key in (pygame.K_ESCAPE, pygame.K_p)` — **Task 8.4:** Esc *or* P resumes,
  mirroring how pause was entered. Otherwise a button click returns its action.

```python
    def draw(self, screen):
        screen.blit(self.overlay, (0, 0))
        screen.blit(self.title, self.title_box)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(screen, mouse_pos)
```
- The caller draws the frozen game first; this blits the dim overlay over it, then
  the title and buttons.

---

## Step 6 — `src/app.py` (new): the single main loop (Task 8.1)

### What this contributes
This is the heart of Task 8.1: one `App` object owns the window, a `GameState`,
and every screen, and runs **one** loop that dispatches by state. Everything
built in Steps 1–5 plugs in here.

### 6a — construction

```python
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

        self.menu = MainMenu(self.screen, config)
        self.game = None
        self.highscores = None
        self.instructions = None
        self.pause_menu = None

        self.pause_start = 0
        self.pause_snapshot = None
```
- `pygame.init()` then `set_mode(..., pygame.FULLSCREEN)` — open a fullscreen
  window sized to the desktop (`info.current_w/current_h`).
- `self.state = GameState(GameState.MAIN_MENU)` — the loop's backbone; starts on
  the menu.
- `self.clock = pygame.time.Clock()` — used to cap the loop at 60 FPS.
- `self.running = True` — the loop's on/off switch.
- The screen slots: `self.menu` is built now (it's the entry screen); `game`,
  `highscores`, `instructions`, `pause_menu` start `None` and are created on
  demand.
- `pause_start` / `pause_snapshot` — Task 8.4 bookkeeping (when the pause began,
  and the frozen frame to show).

### 6b — the loop

```python
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
```
- `events = pygame.event.get()` — drain this frame's input **once**, then pass the
  same list to whichever handler runs (so nobody double-drains the queue).
- The `QUIT` (window close) check is global — it works in every state.
- The `if/elif` chain is the **dispatch**: exactly one screen handler runs per
  frame, chosen by the current state. *This chain is the whole point of Task 8.1.*
- `pygame.display.flip()` — present the frame. `self.clock.tick(60)` — sleep just
  enough to hold 60 FPS.
- After the loop: quit pygame and exit the process.

### 6c — menu frame + action dispatch

```python
    def _main_menu_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            action = self.menu.handle_event(event)
            if action:
                self._run_menu_action(action)
                if not self.state.is_main_menu() or not self.running:
                    return
        self.menu.update_hover(pygame.mouse.get_pos())
        self.menu.draw(self.screen)
```
- Shows the mouse, then feeds each event to the menu.
- `if action:` — a non-`None` action means a button fired; `_run_menu_action`
  handles it, and if it changed state (or quit) we `return` immediately so we don't
  draw the menu over the new screen.
- If nothing changed, update the hover cursor and draw the menu.

```python
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
```
- Maps each action string to "build the screen object + switch state" (or, for
  Exit, stop the loop). This is where the menu's abstract "the user chose X" turns
  into a concrete transition.

### 6d — game frame (with the pause hook, Task 8.4)

```python
    def _game_frame(self, events):
        pygame.mouse.set_visible(False)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                if self.game.is_pausable():
                    self._enter_pause()
                    return
            else:
                self.game.handle_event(event)

        done = self.game.update()
        self.game.draw()

        if done:
            score = self.game.score
            failed = self.game.failed
            self.game = None
            if not failed:
                run_name_entry(self.screen, score, self.config)
            self._return_to_menu()
```
- Hide the cursor during play.
- **Pause hook:** an Esc/P key-down enters pause *if* `is_pausable()`, then
  `return`s (skips this frame's update). Any other event goes to
  `self.game.handle_event(event)` (arrow keys, etc.).
- `done = self.game.update()` then `self.game.draw()` — advance and render one
  frame. `update()` returns `True` when the game has finished.
- **Finish handling (Task 7.3 bridge):** capture `score`/`failed`, drop the game,
  run the blocking name-entry screen unless the maze had failed, then return to the
  menu. (This one blocking call is a temporary seam; Tasks 8.5/8.6 turn it into
  proper Game Over / Victory states.)

### 6e — pause enter / frame / resume (Task 8.4)

```python
    def _enter_pause(self):
        self.game.draw()
        self.pause_snapshot = self.screen.copy()
        self.pause_start = pygame.time.get_ticks()
        self.pause_menu = PauseMenu(self.screen)
        self.state.switch_to(GameState.PAUSE)
```
- `self.game.draw()` then `self.screen.copy()` — render one clean game frame and
  **snapshot** its pixels, so the paused screen is a perfectly frozen image (no
  timers driving it).
- `self.pause_start = get_ticks()` — remember when the pause began, so resume knows
  how long it lasted.
- Build the `PauseMenu` and switch state.

```python
    def _pause_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            action = self.pause_menu.handle_event(event)
            if action == "RESUME":
                self._resume()
                return
            if action == "MAIN_MENU":
                self.game = None
                self._return_to_menu()
                return
        self.pause_menu.update_hover(pygame.mouse.get_pos())
        self.screen.blit(self.pause_snapshot, (0, 0))
        self.pause_menu.draw(self.screen)
```
- Resume → `_resume()`; Main Menu → drop the game and go back (the run is
  abandoned, no score saved — a deliberate choice for a manual quit).
- When neither fired: draw the **frozen snapshot** first, then the pause menu on
  top. Because we blit the snapshot every frame, the game underneath never
  animates while paused.

```python
    def _resume(self):
        paused_ms = pygame.time.get_ticks() - self.pause_start
        self.game.shift_time(paused_ms)
        self.state.switch_to(GameState.GAME)
```
- `paused_ms` = how long we were paused. `self.game.shift_time(paused_ms)` — Step
  4d/3: slide every timer forward by exactly that much, so **no game time passed
  during the pause.** Then switch back to GAME.

### 6f — highscores / instructions frames + helpers

```python
    def _highscores_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if self.highscores.handle_event(event) == "BACK":
                self.state.switch_to(GameState.MAIN_MENU)
                return
        self.highscores.draw(self.screen)
```
- The generic screen pattern: feed events; on `"BACK"` return to the menu;
  otherwise draw. `_instructions_frame` is identical with `self.instructions`.

```python
    def _return_to_menu(self):
        self.menu = MainMenu(self.screen, self.config)
        self.state.switch_to(GameState.MAIN_MENU)
```
- Rebuilds the menu (so its top-scores preview picks up any score just saved) and
  switches back to it.

```python
def run_game(config):
    App(config).run()
```
- A tiny module-level entry point so `pac-man.py` doesn't need to know about the
  `App` class — it just calls `run_game(config)`.

---

## Step 7 — `pac-man.py` + removing `main_menu_UI.py`

```python
from src.app import run_game
...
    config = Config(config_file_path)
    run_game(config)
```
- The launcher now hands off to the single loop. The CLI-argument validation above
  it is unchanged.
- `src/main_menu_UI.py` was **deleted**: its `run_main_menu` is replaced by
  `app.py`, and its `run_highscores` became `screens.HighscoresScreen`. (It's in
  git history if ever needed.) A stale comment in `name_entry_UI.py` that mentioned
  it was updated to point at `app.py`.

---

## Verification

A headless test (`SDL_VIDEODRIVER=dummy`) drove the state machine directly and
**all checks passed**:

- **8.1** — menu actions switch to the right states; New Game builds a working
  `GameDemo`; a finished game (name-entry stubbed) returns to the menu.
- **8.2** — a click on a menu button returns the correct action string
  (`"NEW_GAME"`).
- **8.3** — with the HUD margin, the maze's `offset_y` is always `>= _HUD_HEIGHT`
  (proven no-overlap); `game.draw()` runs without error.
- **8.4** — `shift_time(1234)` moves every timestamp (level timer, fright,
  invincibility, animation, a mid-respawn ghost) forward by exactly 1234 and leaves
  un-eaten ghosts at 0; `is_pausable()` is `False` over the game-over screen;
  Esc in-game enters PAUSE (with a snapshot); Esc in pause resumes (timers
  shifted); the Main Menu button abandons the run.

## Status after this batch

| Task | Status |
|------|--------|
| 8.1 Single GameState-driven main loop | ✅ Done (`app.py`; no more per-screen while-loops except the name-entry bridge) |
| 8.2 Main Menu screen | ✅ Done (New Game / Highscores / Instructions / Exit, hover, top-scores preview) |
| 8.3 In-Game HUD | ✅ Done (score/level/lives/time in a reserved top bar that can't overlap the maze) |
| 8.4 Pause Menu | ✅ Done (P/ESC toggles, everything frozen via snapshot + time-shift, Resume / Main Menu) |

### Notes / seams left for later
- **Name entry** after a game is still a blocking call (`run_name_entry`) — the one
  remaining non-loop screen. Tasks **8.5 (Game Over)** and **8.6 (Victory)** will
  fold it into proper states so the win/lose screens own that flow.
- `HighscoresScreen` / `InstructionsScreen` are minimal early versions of Tasks
  **8.7 / 8.8**; they already work, but 8.7/8.8 flesh them out (e.g. cheat-key docs
  once Phase 9 exists).
- Returning to the menu from Pause abandons the run without saving — a deliberate
  choice for a manual quit; revisit if you'd rather save on quit.
