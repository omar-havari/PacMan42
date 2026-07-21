# Phase 7 — Highscore System — Change Log

This document walks through **every change made to finish Phase 7 (Tasks 7.1,
7.2, 7.3)**, in the exact order the work was done. For each step it explains:

- **What the step does for the project** (why it matters to Pac-Man).
- **A line-by-line reading of the code** (what each line does syntactically).

Phase 7 is the persistent highscore feature: a score table that survives
between runs, is robust to a broken/missing file, and is filled in by a
name-entry screen shown after every game ends.

Files touched, in order:

1. `src/highscore.py` — rewritten and hardened (Tasks 7.1 + 7.2)
2. `src/name_entry_UI.py` — new file, the name-entry screen (Task 7.3)
3. `src/main_menu_UI.py` — wired the save flow + a highscores viewer into the loop

---

## Step 1 — Harden `src/highscore.py` (Tasks 7.1 & 7.2)

### What this step contributes
Before this step, `HighscoreManager` existed but had three problems: the name
length cap was 20 (the subject requires **10**), the filename was hardcoded
instead of coming from the config, and it only survived *some* kinds of bad
files. This step turns it into the single, trustworthy owner of the highscore
file: it is the only class in the whole game that reads or writes that file, so
the on-disk format lives in exactly one place.

### Line-by-line

```python
import json
```
- `import json` — pulls in Python's standard JSON library; we use `json.load`
  (file → Python list) and `json.dump` (Python list → file).

```python
class HighscoreManager:
    def __init__(self, filename="highscores.json"):
        self.filename = filename
        self.scores = self.load()
```
- `class HighscoreManager:` — defines the class.
- `def __init__(self, filename="highscores.json"):` — the constructor.
  `filename` has a **default value**, so `HighscoreManager()` still works, but
  callers normally pass the config's path. `self` is the instance being built.
- `self.filename = filename` — stores the path on the instance so every method
  can reach it.
- `self.scores = self.load()` — immediately calls `load()` (below) so
  `self.scores` is a ready-to-use list the moment the object exists.

```python
    def load(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, OSError):
            print("Warning: highscore file corrupted, starting fresh.")
            return []
```
- `def load(self):` — reads the file and returns a clean list of scores.
- `try:` — start of the protected block; if anything inside raises, control
  jumps to a matching `except`.
- `with open(self.filename, "r", encoding="utf-8") as f:` — opens the file for
  reading (`"r"`) as UTF-8 text. `with` guarantees the file is closed even if an
  error happens; `as f` names the open file object.
- `data = json.load(f)` — parses the file's JSON text into a Python object.
- `except FileNotFoundError:` → `return []` — **Task 7.2 (missing file):** on
  first run the file doesn't exist yet; this is not an error, so we quietly
  return an empty list (the file gets created on the first `save()`).
- `except (json.JSONDecodeError, OSError):` — **Task 7.2 (corrupted file):**
  catches both "the text isn't valid JSON" and lower-level I/O problems
  (permissions, etc.). The parentheses make it catch either exception type.
- `print("Warning: ...")` — logs a clear message (subject: "no traceback").
- `return []` — recover by starting fresh instead of crashing.

```python
        if not isinstance(data, list):
            print("Warning: highscore file has unexpected format, starting fresh.")
            return []
        clean = []
        for entry in data:
            if (
                isinstance(entry, dict)
                and self._valid_name(entry.get("name"))
                and self._valid_score(entry.get("score"))
            ):
                clean.append({"name": entry["name"], "score": entry["score"]})
        clean.sort(key=lambda x: x["score"], reverse=True)
        return clean[:10]
```
- `if not isinstance(data, list):` — the JSON parsed, but it might be the wrong
  *shape* (e.g. someone wrote `{"a": 1}` or `5` into the file). If it isn't a
  list, we can't trust it → warn and reset. This is a robustness case beyond the
  literal subtasks, but directly serves "robust to file errors".
- `clean = []` — an accumulator for only the well-formed rows.
- `for entry in data:` — loop over each item the file contained.
- `if ( isinstance(entry, dict) and self._valid_name(...) and self._valid_score(...) ):`
  — keep an entry only if it is a dict **and** its name and score both pass the
  validators (defined below). `entry.get("name")` returns `None` if the key is
  missing, which the validators safely reject. `and` short-circuits, so a
  non-dict never reaches the name check.
- `clean.append({"name": entry["name"], "score": entry["score"]})` — rebuild the
  row from scratch with only the two keys we care about (drops any junk extra
  fields).
- `clean.sort(key=lambda x: x["score"], reverse=True)` — sort in place, highest
  score first. `key=lambda x: x["score"]` tells `sort` to order by each row's
  score; `reverse=True` makes it descending.
- `return clean[:10]` — `[:10]` is a slice: the first 10 elements. Even a file
  hand-edited to hold 50 rows is trimmed to the top 10.

```python
    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except OSError:
            print("Warning: could not save highscores.")
```
- `def save(self):` — writes the current table back to disk.
- `with open(self.filename, "w", ...)` — `"w"` opens for writing and **truncates**
  (empties) the file first, so we always overwrite with the fresh list.
- `json.dump(self.scores, f, indent=2)` — serialises the list to JSON text and
  writes it to `f`. `indent=2` pretty-prints it so the file is human-readable.
- `except OSError:` → `print(...)` — **Task 7.2 / 10.4:** a disk error at
  save-time (e.g. disk full, read-only folder) can't be allowed to crash the
  game right as it ends; we log and move on.

```python
    def _valid_name(self, name):
        return (
            isinstance(name, str)
            and 0 < len(name) <= 10
            and all(c.isalnum() or c == " " for c in name)
        )
```
- `def _valid_name(self, name):` — the leading `_` marks it "internal/private".
- `isinstance(name, str)` — the name must be a string.
- `0 < len(name) <= 10` — **Task 7.1 (the fix):** length must be at least 1 and
  **at most 10** (was 20). This is a chained comparison, read as
  `0 < len(name) and len(name) <= 10`.
- `all(c.isalnum() or c == " " for c in name)` — `all(...)` is `True` only if the
  condition holds for *every* character `c`; each character must be alphanumeric
  (`c.isalnum()`) or a space. Blocks punctuation/symbols.

```python
    def _valid_score(self, score):
        return isinstance(score, int) and not isinstance(score, bool) and score >= 0
```
- `isinstance(score, int)` — must be an integer.
- `not isinstance(score, bool)` — in Python `True`/`False` *are* ints
  (`True == 1`), so this explicitly rejects a stray boolean sneaking in as a
  "score".
- `score >= 0` — **Task 7.1:** scores are non-negative.

```python
    def add(self, name, score):
        if not self._valid_name(name) or not self._valid_score(score):
            return
        self.scores.append({"name": name, "score": score})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]
        self.save()
```
- `def add(self, name, score):` — the public "record one result" method.
- `if not self._valid_name(name) or not self._valid_score(score): return` — bail
  out silently on bad input. `return` with no value exits the method early, so a
  bad name can never crash the end-of-game flow.
- `self.scores.append({...})` — add the new row to the in-memory list.
- `self.scores.sort(..., reverse=True)` — re-sort so the new row lands in rank
  order.
- `self.scores = self.scores[:10]` — keep only the top 10; a score that isn't
  good enough falls off here.
- `self.save()` — **Task 7.1:** persist immediately, so the file always reflects
  the latest table.

```python
    def get_top10(self):
        return self.scores[:10]
```
- Returns a copy of the top 10 for display screens. `[:10]` is defensive — the
  list is already capped, but this guarantees callers never see more than 10.

---

## Step 2 — New file `src/name_entry_UI.py` (Task 7.3)

### What this step contributes
This is the screen that connects the highscore *storage* to actual *gameplay*:
after any game ends, the player types a name and it gets saved. It does the
real-time input validation the subject asks for (block bad characters, cap at
10) and is the only place that decides *when* a score is written.

### Line-by-line

```python
import os
import sys

import pygame

from src.highscore import HighscoreManager

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

_MAX_NAME_LENGTH = 10
```
- `import os`, `import sys`, `import pygame` — filesystem paths, clean exit, and
  the game/graphics library.
- `from src.highscore import HighscoreManager` — this screen saves through the
  manager from Step 1.
- `_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')`
  — builds the path to the `assets/` folder relative to *this file*:
  `__file__` is this file's path, `abspath` makes it absolute,
  `dirname` strips to the containing folder, and `os.path.join(..., '..', 'assets')`
  steps up one level and into `assets`. This is the same asset-path pattern used
  across the project, so the game works regardless of the working directory.
- `_MAX_NAME_LENGTH = 10` — one named constant for the cap, so the hint text and
  the validation can't drift apart.

```python
def _load_font(path, size):
    try:
        return pygame.font.Font(path, size)
    except FileNotFoundError:
        print(f"Error: font file '{path}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)
```
- The same defensive font loader used in `GameDemo`/`Player`.
- `pygame.font.Font(path, size)` — loads a TrueType font at a pixel size.
- `except FileNotFoundError:` — a missing font is a clean, explained exit
  (`sys.exit(1)` = non-zero exit code = "failure"), never a traceback.

```python
def run_name_entry(screen, score, config):
    font_title = _load_font(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 60)
    font_body = _load_font(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 36)

    name = ""
    clock = pygame.time.Clock()
```
- `def run_name_entry(screen, score, config):` — the entry point.
  `screen` is the surface to draw on, `score` is the just-finished game's final
  score, `config` carries the highscore filename.
- `font_title`/`font_body` — two font sizes for headings vs. body text.
- `name = ""` — the string being typed, starts empty and grows key by key.
- `clock = pygame.time.Clock()` — used to cap the loop at 60 FPS.

```python
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
```
- `while True:` — this screen runs its own loop (same style as the other
  screens) until a `return` breaks out.
- `for event in pygame.event.get():` — process every input event queued since
  last frame.
- `if event.type == pygame.QUIT:` — the window's close button; quit the whole
  program cleanly.

```python
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if name:
                        manager = HighscoreManager(config.highscore_file)
                        manager.add(name, score)
                        return
```
- `if event.type == pygame.KEYDOWN:` — a key was pressed.
- `if event.key == pygame.K_RETURN:` — the Enter key = "confirm".
- `if name:` — an empty string is "falsy", so this is only true when at least
  one character has been typed; pressing Enter on an empty box does nothing.
- `manager = HighscoreManager(config.highscore_file)` — **Task 7.1 wiring:**
  builds the manager from the **config's** filename (not a hardcoded one), which
  also reloads the current file so we merge into the latest table.
- `manager.add(name, score)` — validate + insert + save (Step 1).
- `return` — leave the screen; control goes back to the menu loop.

```python
                elif event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
```
- `elif event.key == pygame.K_ESCAPE:` → `return` — skip saving and go back to
  the menu (a deliberate "no thanks" option).
- `elif event.key == pygame.K_BACKSPACE:` → `name = name[:-1]` — delete the last
  character. `name[:-1]` is "everything except the last character"; on an empty
  string it harmlessly stays empty.

```python
                else:
                    char = event.unicode
                    if (
                        len(name) < _MAX_NAME_LENGTH
                        and len(char) == 1
                        and (char.isalnum() or char == " ")
                    ):
                        name += char
```
- `else:` — any other key.
- `char = event.unicode` — the actual character the key produced (`"a"`, `"7"`,
  `" "`); it's the empty string for non-printing keys like Shift.
- **Task 7.3 real-time validation** — accept the character only if all hold:
  - `len(name) < _MAX_NAME_LENGTH` — we're still under 10 characters.
  - `len(char) == 1` — it's a single printable character (filters out Shift etc.,
    whose `unicode` is `""`).
  - `char.isalnum() or char == " "` — it's alphanumeric or a space.
- `name += char` — append it. Invalid keys are simply never added, so the box
  can only ever contain a valid name.

```python
        screen.fill((0, 0, 0))
        width, height = screen.get_size()

        title = font_title.render("NEW SCORE", False, (255, 255, 0))
        screen.blit(title, title.get_rect(center=(width / 2, height / 2 - 180)))
```
- `screen.fill((0, 0, 0))` — clear to black each frame so old text doesn't
  smear.
- `width, height = screen.get_size()` — unpack the screen size into two
  variables, so layout is centered at any resolution.
- `font_title.render("NEW SCORE", False, (255, 255, 0))` — draw the text to a new
  surface. `False` = anti-aliasing off (crisp pixel look for this arcade font);
  `(255, 255, 0)` is yellow (R,G,B).
- `screen.blit(title, title.get_rect(center=(...)))` — `get_rect(center=...)`
  makes a rectangle the size of the text positioned by its center;
  `blit` copies the text onto the screen there. `width / 2, height / 2 - 180`
  centers it horizontally, 180 px above the middle.

```python
        score_line = font_body.render(f"Score  {score}", False, (255, 255, 255))
        screen.blit(score_line, score_line.get_rect(center=(width / 2, height / 2 - 90)))

        prompt = font_body.render("Enter your name:", False, (90, 140, 255))
        screen.blit(prompt, prompt.get_rect(center=(width / 2, height / 2 - 20)))
```
- `f"Score  {score}"` — an f-string: `{score}` is replaced by the number.
- The two `blit` calls stack the final score and the prompt under the title.
  `(90, 140, 255)` is the project's blue theme color.

```python
        caret = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = font_body.render(name + caret, False, (255, 255, 255))
        screen.blit(typed, typed.get_rect(center=(width / 2, height / 2 + 50)))
```
- `caret = "_" if ... else " "` — a **blinking cursor**. `pygame.time.get_ticks()`
  is milliseconds since start; `// 500` is integer division so it increments
  every half second; `% 2 == 0` alternates true/false → the caret shows for
  500 ms, hides for 500 ms.
- `name + caret` — the typed name with the caret appended, rendered together.

```python
        hint = font_body.render("ENTER = save    ESC = skip", False, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(width / 2, height / 2 + 150)))

        pygame.display.flip()
        clock.tick(60)
```
- `hint` — grey helper text so the controls are obvious.
- `pygame.display.flip()` — pushes everything drawn this frame to the actual
  display.
- `clock.tick(60)` — waits just long enough to hold the loop at 60 frames per
  second (keeps CPU usage sane).

---

## Step 3 — Wire it into the game in `src/main_menu_UI.py`

### What this step contributes
Steps 1–2 built the storage and the entry screen, but nothing *called* them
yet. This step connects them to the real game flow so Task 7 actually functions:
every finished game routes into the name-entry save, and the menu's "High scores"
button now shows the saved table (a minimal early version of Task 8.7) so the
whole save/load cycle is visible in-game.

### 3a — New imports (lines 6–7)

```python
from src.highscore import HighscoreManager
from src.name_entry_UI import run_name_entry
```
- Bring the manager (to *read* scores for the viewer) and the name-entry screen
  (to *write* them) into the menu module.

### 3b — New `run_highscores` viewer (lines 21–67)

```python
def run_highscores(screen, config):
    font_title = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 70)
    font_row = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 34)

    scores = HighscoreManager(config.highscore_file).get_top10()
```
- `def run_highscores(screen, config):` — a self-contained screen, same loop
  style as `run_name_entry`.
- `scores = HighscoreManager(config.highscore_file).get_top10()` — builds a
  manager (which **reloads the file from disk**) and grabs the top 10, so the
  list is current even immediately after a game saved to it.

```python
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                return
```
- The loop; `event.key in (pygame.K_ESCAPE, pygame.K_RETURN)` — `in` checks
  membership in that tuple, so **either** Esc or Enter returns to the menu.

```python
        screen.fill((0, 0, 0))
        width, height = screen.get_size()

        title = font_title.render("HIGH SCORES", False, (255, 255, 0))
        screen.blit(title, title.get_rect(center=(width / 2, 140)))
```
- Clear to black, read the screen size, draw the heading near the top.

```python
        if not scores:
            empty = font_row.render("No scores yet", False, (120, 120, 120))
            screen.blit(empty, empty.get_rect(center=(width / 2, height / 2)))
```
- `if not scores:` — an empty list is falsy; **Task 8.7 edge case:** show a
  friendly message instead of a blank box on first run.

```python
        else:
            for rank, entry in enumerate(scores, start=1):
                row = font_row.render(
                    f"{rank:2d}.  {entry['name']:<10}  {entry['score']}",
                    False,
                    (90, 140, 255),
                )
                screen.blit(row, row.get_rect(centerx=width / 2, top=260 + (rank - 1) * 50))
```
- `for rank, entry in enumerate(scores, start=1):` — `enumerate(..., start=1)`
  yields `(1, first_entry), (2, second_entry), ...`, giving both the rank number
  and the row.
- `f"{rank:2d}.  {entry['name']:<10}  {entry['score']}"` — a formatted line:
  - `{rank:2d}` — the rank as an integer padded to width 2 (so 1–9 align under 10).
  - `{entry['name']:<10}` — the name left-aligned in a 10-wide field, so all the
    scores line up in a neat column.
  - `{entry['score']}` — the score.
- `top=260 + (rank - 1) * 50` — each successive row is drawn 50 px lower than the
  last, starting at y=260. `rank - 1` makes the first row start exactly at 260.

```python
        hint = font_row.render("ESC = back", False, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(width / 2, height - 100)))

        pygame.display.flip()
        clock.tick(60)
```
- Grey "ESC = back" hint near the bottom, then present the frame at 60 FPS.

### 3c — Save on game end (lines 146–156)

```python
            if game_over:
                final_score = game.score
                failed = game.failed
                game = None
                if not failed:
                    run_name_entry(screen, final_score, config)
```
- `if game_over:` — `game.update()` returned `True`, meaning the game finished
  (win, lose, or a maze that failed to build).
- `final_score = game.score` — **capture the score before discarding the game
  object** — after `game = None` we couldn't reach it.
- `failed = game.failed` — likewise remember whether the maze failed to generate.
- `game = None` — drop the finished game; the loop's `if game is not None`
  check will now fall through to the menu branch next iteration.
- `if not failed: run_name_entry(...)` — **Task 7.2/7.3:** a genuinely-played
  game (win *or* lose) always routes through the name-entry save flow. A failed
  maze never really played, so it skips straight back to the menu — no point
  asking for a name on a score of 0 from a game that never started.

### 3d — Wire the "High scores" button (lines 174–176)

```python
                    if high_scores_box.collidepoint(event.pos):
                        run_highscores(screen, config)
```
- `if high_scores_box.collidepoint(event.pos):` — the mouse click landed inside
  the "High scores" button's rectangle.
- `run_highscores(screen, config)` — open the viewer (replaces the old
  `print("Placeholder")`). It blocks until the player presses Esc/Enter, then the
  menu resumes.

---

## How the pieces fit together (data flow)

```
Game ends (win/lose) ─► main loop captures game.score
        │
        ▼
run_name_entry(screen, score, config)   ← Task 7.3 screen
        │  player types a valid name, presses Enter
        ▼
HighscoreManager(config.highscore_file).add(name, score)   ← Tasks 7.1/7.2
        │  validates, sorts, caps to 10, writes JSON to disk
        ▼
highscores.json  ◄──────────────────────────────────────────┐
        │                                                     │
        ▼                                                     │
Menu "High scores" button ─► run_highscores(...)             │
        │  HighscoreManager(...).get_top10() reloads ─────────┘
        ▼
Ranked top-10 table drawn on screen   (early Task 8.7)
```

---

## Verification

A headless test (`SDL_VIDEODRIVER=dummy`) exercised every path end-to-end and
**all checks passed**:

- **7.1** — add/sort/cap to 10; the 10-char name cap accepts 10 and rejects 11;
  invalid inputs (punctuation, negative score, boolean score, non-string name)
  are silently ignored.
- **7.2** — missing file → empty; garbage-JSON file → empty + warning; wrong-shape
  JSON (an object instead of a list) → empty + warning; a mixed list keeps only
  the well-formed rows.
- **7.3** — synthetic key events drove the name-entry screen: typing `"Al 3"`
  (with a `!` correctly ignored) then Enter saved `{"name": "Al 3", "score": 555}`;
  pressing Esc after typing saved nothing.

## Status after this phase

| Task | Status |
|------|--------|
| 7.1 Persistent JSON storage | ✅ Done (filename from config, 10-char cap, top-10) |
| 7.2 Corrupted/missing file handling | ✅ Done (missing, corrupt, wrong-shape all safe; always saves at game end) |
| 7.3 Name entry UI | ✅ Done (real-time validation, Enter=save, Esc=skip, returns to menu) |

Note: `run_highscores` is a **minimal early version of Task 8.7** (highscores
screen). It was added here purely so Phase 7 is observable in-game; the full
GameState-driven version still belongs to Phase 8.
