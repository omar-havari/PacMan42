# Task 8 (8.5–8.8) — End Screens, Highscores & Instructions — Change Log

This document walks through **every change made to finish Phase 8** — Tasks
**8.5 (Game Over), 8.6 (Victory), 8.7 (Highscores)** and **8.8
(Instructions)** — in the order the work was done. For each step it explains:

- **What the step contributes to the project** (why it matters).
- **A line-by-line reading of the code** (what each line does syntactically).

Phase 8's earlier batch (8.1–8.4, see `Phase8_UI_Changes.md`) built the single
`GameState`-driven main loop and hung the Main Menu, HUD and Pause menu off it,
but left **one seam**: the end-of-game name entry was still a blocking
`run_name_entry()` loop. This batch closes that seam — Game Over and Victory
become **proper states** with the name entry folded in — and fills out the
Highscores and Instructions screens.

Files changed, in order:

1. `src/screens.py` — **new** `NameEntryScreen`; fleshed-out `InstructionsScreen`
2. `src/app.py` — real `GAME_OVER` / `VICTORY` states; the blocking bridge removed
3. `src/ghost.py` — the flee-speed knob (Task 8.6's side note)
4. `src/name_entry_UI.py` — **deleted** (its job now lives in a state-driven screen)

The Highscores screen (Task 8.7) already met every subtask from the Phase 7
work, so it needed only a cosmetic line-wrap; it is covered at the end.

---

## Step 1 — `NameEntryScreen`: fold name entry into a state (Tasks 8.5 / 8.6)

### What this contributes
The old flow, after a game ended, called `run_name_entry(...)` — a screen that
ran its **own** blocking `while` loop. That was the last screen in the game not
driven by the main loop. `NameEntryScreen` replaces it with the exact same
contract every other screen already uses (`handle_event` → action string /
`draw`, no loop of its own), so the Game Over and Victory states can be driven
by `app.py` frame-by-frame like everything else. One screen serves **both**
endings: the only difference is the heading text and its colour.

### Line-by-line

```python
_MAX_NAME_LENGTH = 10
```
- The one named constant for the name cap (subject rule: names are ≤ 10 chars).
  Kept next to the theme colours so the on-screen hint and the validation can't
  drift apart.

```python
class NameEntryScreen:
    def __init__(self, screen, score, config, title, won):
        self.score = score
        self.config = config
        self.title = title
        self.title_color = _HOVER_COLOR if won else _TEXT_COLOR
        self.font_title = load_font(80)
        self.font_body = load_font(34)
        self.name = ""
```
- `def __init__(self, screen, score, config, title, won):` — the constructor.
  `score` is the just-finished game's final score; `title` is the heading to
  show (`"YOU WIN!"` or `"GAME OVER"`); `won` is a bool that picks the colour.
- `self.title_color = _HOVER_COLOR if won else _TEXT_COLOR` — a **conditional
  expression**: a win gets the celebratory yellow, a loss gets the calmer blue
  theme colour. Same screen, different mood.
- `self.font_title` / `self.font_body` — two font sizes (heading vs. body),
  loaded through the shared defensive `load_font` (a missing font is a clean
  exit, never a traceback).
- `self.name = ""` — the string being typed, starts empty and grows key by key.

```python
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_RETURN:
            if self.name:
                HighscoreManager(self.config.highscore_file).add(self.name, self.score)
                return "DONE"
            return None
```
- `if event.type != pygame.KEYDOWN: return None` — we only care about key
  presses; anything else (mouse move, etc.) is ignored this frame.
- `if event.key == pygame.K_RETURN:` — the Enter key = "confirm".
- `if self.name:` — an empty string is falsy, so Enter on an empty box does
  nothing (`return None`); you can't save a blank name.
- `HighscoreManager(self.config.highscore_file).add(self.name, self.score)` —
  builds the manager from the **config's** filename (which also reloads the
  file, so we merge into the latest table) and `.add()` validates, sorts, caps
  to 10 and writes to disk.
- `return "DONE"` — tells `app.py` the screen is finished; the loop then
  returns to the menu.

```python
        if event.key == pygame.K_ESCAPE:
            return "DONE"
        if event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            return None
```
- `K_ESCAPE` → `"DONE"` — a deliberate "skip saving" option; still finishes the
  screen, just without writing anything.
- `K_BACKSPACE` → `self.name = self.name[:-1]` — delete the last character.
  `[:-1]` is "everything except the last character"; on an empty string it
  harmlessly stays empty.

```python
        char = event.unicode
        if (
            len(self.name) < _MAX_NAME_LENGTH
            and len(char) == 1
            and (char.isalnum() or char == " ")
        ):
            self.name += char
        return None
```
- **Task 7.3 real-time validation, unchanged from the old screen.** `char =
  event.unicode` is the actual character produced (`"a"`, `"7"`, `" "`); it's
  the empty string for non-printing keys like Shift.
- Accept the character only if **all** hold: we're under 10 chars, it's a single
  printable character (`len(char) == 1` filters out Shift, whose unicode is
  `""`), and it's alphanumeric or a space. Everything else is silently dropped,
  so the box can only ever hold a valid name.

```python
    def draw(self, screen):
        screen.fill(_BG_COLOR)
        width, height = screen.get_size()
        title = self.font_title.render(self.title, False, self.title_color)
        screen.blit(title, title.get_rect(center=(width / 2, height / 2 - 200)))
```
- Clear to black each frame, read the screen size so layout is centred at any
  resolution, then draw the heading. `False` = no anti-aliasing (crisp arcade
  look); `get_rect(center=...)` positions the text by its centre.

```python
        score_line = self.font_body.render(f"Score  {self.score}", False, _WHITE)
        screen.blit(score_line, score_line.get_rect(center=(width / 2, height / 2 - 90)))
        prompt = self.font_body.render("Enter your name:", False, _TEXT_COLOR)
        screen.blit(prompt, prompt.get_rect(center=(width / 2, height / 2 - 20)))
```
- **Task 8.5 / 8.6: "show final score".** The f-string `f"Score  {self.score}"`
  interpolates the number. The prompt sits just below it.

```python
        caret = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = self.font_body.render(self.name + caret, False, _WHITE)
        screen.blit(typed, typed.get_rect(center=(width / 2, height / 2 + 50)))
        hint = self.font_body.render("ENTER = save    ESC = skip", False, _DIM_COLOR)
        screen.blit(hint, hint.get_rect(center=(width / 2, height / 2 + 150)))
```
- `caret` — a **blinking underscore**. `get_ticks() // 500` increments every
  half-second; `% 2 == 0` alternates true/false, so the caret shows for 500 ms
  and hides for 500 ms.
- `self.name + caret` — the typed name with the caret appended, rendered
  together, then the grey `ENTER = save  ESC = skip` hint underneath.

---

## Step 2 — Wire the real end states into `src/app.py` (Tasks 8.5 / 8.6)

### What this contributes
This is where the blocking bridge finally disappears. `app.py` now decides the
outcome when a game finishes, builds the `NameEntryScreen`, and switches to the
`GAME_OVER` or `VICTORY` state — which it then drives with a normal per-frame
handler, exactly like the highscores/instructions screens.

### 2a — dispatch the new states in the main loop

```python
            elif self.state.is_game_over() or self.state.is_victory():
                self._end_frame(events)
```
- One new branch in the `if/elif` dispatch chain. Both endings share the same
  handler because they share the same screen — only the heading differs.

### 2b — decide the outcome when a game ends

```python
        done = self.game.update()
        self.game.draw()

        if done:
            self._finish_game()
```
- The game-frame's finish path is now a single call. `update()` returns `True`
  when the game is over (win, lose, or a maze that failed to build).

```python
    def _finish_game(self):
        if self.game.failed:
            self.game = None
            self._return_to_menu()
            return
        won = self.game.victory_time is not None
        score = self.game.score
        self.game = None
        title = "YOU WIN!" if won else "GAME OVER"
        self.end_screen = NameEntryScreen(self.screen, score, self.config, title, won)
        self.state.switch_to(GameState.VICTORY if won else GameState.GAME_OVER)
```
- `if self.game.failed:` — a maze that never generated was never really played,
  so it skips straight back to the menu (no point asking for a name).
- `won = self.game.victory_time is not None` — `GameDemo` sets `victory_time`
  when all 10 levels are cleared and leaves it `None` otherwise, so this bool
  distinguishes a **win** from a **loss** cleanly.
- `score = self.game.score` — **capture the score before dropping the game
  object** (`self.game = None`), or we couldn't reach it afterwards.
- `title = "YOU WIN!" if won else "GAME OVER"` — pick the heading; the same
  `won` flag is passed to the screen so its colour matches.
- `self.state.switch_to(GameState.VICTORY if won else GameState.GAME_OVER)` —
  enter the correct state. From here the main loop routes to `_end_frame`.

### 2c — drive the end screen each frame

```python
    def _end_frame(self, events):
        pygame.mouse.set_visible(True)
        for event in events:
            if self.end_screen.handle_event(event) == "DONE":
                self.end_screen = None
                self._return_to_menu()
                return
        self.end_screen.draw(self.screen)
```
- The generic screen pattern: show the mouse, feed each event to the screen; on
  `"DONE"` (name saved **or** skipped) drop the screen and go back to the menu
  (`_return_to_menu` rebuilds the menu so its top-scores preview reflects the
  new save); otherwise draw the screen.

### 2d — the import and the field
```python
from src.screens import (..., NameEntryScreen, ...)
...
        self.end_screen = None
```
- `run_name_entry` is no longer imported; `NameEntryScreen` takes its place.
  `self.end_screen` is the slot holding the active Game Over / Victory screen
  (`None` when not in those states).

---

## Step 3 — `src/ghost.py`: the flee-speed knob (Task 8.6 side note)

### What this contributes
Task 8.6 carried a note: *"also want to change the speed of the ghosts in flee
mode."* Fleeing-ghost speed was previously an **inline literal** buried in
`Ghost.update()` (`self._frighten_tick % 2 == 0`). This step lifts it into one
named constant so the flee speed is a single, obvious thing to tune.

### Line-by-line

```python
_FRIGHTENED_STEP_EVERY = 2
```
- A module-level constant: a frightened ghost only actually steps forward once
  every `_FRIGHTENED_STEP_EVERY` frames. `2` = half speed (the value that makes
  a fleeing ghost catchable). Raise it to make fleeing ghosts slower/easier,
  lower it to make the chase harder.

```python
            if frightened:
                self._frighten_tick += 1
                move_this_frame = self._frighten_tick % _FRIGHTENED_STEP_EVERY == 0
```
- The old `% 2` is now `% _FRIGHTENED_STEP_EVERY`. Same mechanism — the ghost
  keeps its full step size but only moves on some frames — now driven by the
  single knob instead of a magic number.

---

## Step 4 — delete `src/name_entry_UI.py`

### What this contributes
Its entire job (`run_name_entry`) is now done by `NameEntryScreen`, and nothing
imports it anymore. Leaving it would be dead code in a project that is about to
have a code-quality pass (Phase 10), so it is removed. It stays in git history
if ever needed.

---

## Task 8.7 — Highscores screen

`HighscoresScreen` already satisfied **every** 8.7 subtask from the Phase 7 /
8.1–8.4 work:

- **Ranked top 10** — `for rank, entry in enumerate(self.scores, start=1)` with
  `f"{rank:2d}.  {entry['name']:<10}  {entry['score']}"` (rank padded to width 2
  so 1–9 line up under 10; name left-aligned in a 10-wide field so the scores
  form a neat column).
- **Empty list handled** — `if not self.scores:` draws "No scores yet".
- **Return to Main Menu** — `handle_event` returns `"BACK"` on Esc/Enter.
- **Always current** — the constructor reloads the file
  (`HighscoreManager(config.highscore_file).get_top10()`), so a score saved on
  the Game Over screen a moment earlier is already in the table.

The only change this batch made was wrapping one long `screen.blit(...)` call
across two lines for the flake8 pass (Task 10.3) — no behaviour change.

---

## Task 8.8 — Instructions screen

### What this contributes
The early `InstructionsScreen` listed a few controls. Task 8.8 asks for the
movement controls, a short explanation of the pac-gum / super-pac-gum / ghost
mechanics, **and** the cheat-mode keys (which only exist once Phase 9 does — so
this was finished together with Phase 9). The rewrite groups the text into
labelled sections rendered in different colours.

### Line-by-line (the important parts)

```python
        self.lines = [
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
```
- Each row is a `(text, kind)` **tuple**. The `kind` string — `"head"`,
  `"body"` or `"cheat"` — picks the font size and colour when drawn, so section
  headings, normal lines and the cheat keys are visually distinct without
  hard-coding a colour per line. The three sections map exactly onto the three
  8.8 subtasks (controls / mechanics / cheat keys).

```python
    def draw(self, screen):
        ...
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
```
- Headings render yellow at the larger `font_head`; cheat lines render magenta
  (matching the in-game cheat overlay from Phase 9); everything else renders in
  the blue theme colour. `y += 42` steps each line down the screen by a fixed
  amount so blank `("", "body")` rows act as spacers between sections.

---

## How the pieces fit together (data flow)

```
Game ends ─► GameDemo.update() returns True
        │
        ▼
App._finish_game()  ── failed maze ─────────────► back to Main Menu (no name)
        │  win?  victory_time is not None
        ▼
NameEntryScreen(screen, score, config, "YOU WIN!"/"GAME OVER", won)
state ► VICTORY / GAME_OVER
        │  App._end_frame() drives it each frame
        ▼
player types a name + ENTER ─► HighscoreManager(...).add(name, score) ─► highscores.json
        │  (or ESC to skip)
        ▼
"DONE" ─► App._return_to_menu()  (rebuilds menu, refreshes top-scores preview)
```

---

## Verification

A headless test (`SDL_VIDEODRIVER=dummy`) drove the new screens and states
directly and **all checks passed**:

- **8.5** — a loss switches the app to `GAME_OVER` with a `"GAME OVER"` heading;
  ESC on the screen saves nothing and returns to the menu.
- **8.6** — a win switches to `VICTORY` with a `"YOU WIN!"` heading; typing
  `"AL 3"` (with a stray `!` correctly rejected) then ENTER writes
  `{"name": "AL 3", "score": 1234}`; the flee-speed constant drives the
  frightened move cadence.
- **8.7 / 8.8** — the highscores and instructions screens both draw without
  error; `is_game_over()` / `is_victory()` predicates behave.
- **App wiring** — `NEW_GAME → GAME`, loss `→ GAME_OVER → menu`, win `→ VICTORY
  → menu`, and a failed maze `→ menu` all transition correctly.

## Status after this batch

| Task | Status |
|------|--------|
| 8.5 Game Over screen | ✅ Done (real state; final score + name entry + return to menu) |
| 8.6 Victory screen | ✅ Done (real state; congrats + score + name entry; flee-speed knob) |
| 8.7 Highscores screen | ✅ Done (ranked top-10, empty-state, back to menu) |
| 8.8 Instructions screen | ✅ Done (controls + mechanics + cheat keys, sectioned) |

**Seam closed:** the blocking `run_name_entry` bridge flagged at the end of the
8.1–8.4 batch is gone — **every** screen in the game is now driven by the single
main loop.
