# Phase 10 (Tasks 10.1–10.4) — Code Quality Pass — Change Log

This document walks through **every change made for Phase 10**, in the order the
work was done. For each step it explains:

- **What the step contributes to the project** (why it matters — these are hard
  grading requirements for the 42 subject).
- **How it was applied**, with representative before/after code.

Phase 10 is a **quality pass over the whole finished codebase**: full type hints
checked by `mypy`, a docstring on every class and function, zero `flake8`
warnings, and an exception-handling audit that guarantees no traceback on
hostile inputs. No gameplay behaviour changes — every headless test from Phases
7–9 still passes unchanged afterward.

Files touched: **all 13 source modules** plus `pac-man.py`, a new
`src/__init__.py`, and a new `setup.cfg`.

---

## Step 0 — tooling: `setup.cfg` and `src/__init__.py`

### What this contributes
Task 10.3 explicitly allows *"Add `.flake8` or `setup.cfg` if custom
line-length rules needed."* The project's arcade-style code uses long,
explanatory comments and descriptive names, so the default 79-char limit is
impractical. One `setup.cfg` configures **both** tools in one place.

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = venv, graphify-out, scratchpad, .git, __pycache__

[mypy]
ignore_missing_imports = True
warn_return_any = True
warn_unused_ignores = True
disallow_untyped_defs = True
check_untyped_defs = True
```
- `max-line-length = 100` — readable on a normal editor, room for comments.
- `extend-ignore = E203, W503` — these two conflict with common slicing/line-break
  formatting and are safe to ignore.
- The `[mypy]` block is the exact strict flag set the task names:
  `ignore_missing_imports` (the `mazegenerator` package ships no type stubs),
  `warn_return_any`, `warn_unused_ignores`, `disallow_untyped_defs` (every
  function **must** be annotated) and `check_untyped_defs`.

```python
# src/__init__.py
"""PacMan42 game package."""
```
- A new empty package marker. Without it, `mypy` sees `src/config.py` under two
  names (`config` and `src.config`) and aborts. Adding `__init__.py` makes `src`
  an explicit package and fixes the module resolution — it does not change
  runtime behaviour (the `from src.x import y` imports already worked).

---

## Step 1 — Task 10.1: type hints on every function, checked by mypy

### What this contributes
`disallow_untyped_defs = True` means **every** `def` in the project must have
fully-annotated parameters and a return type, or mypy fails. This makes the
code self-documenting and catches whole classes of bugs (passing the wrong type,
returning `None` where a value is expected) before they ever run.

### How it was applied
Every function and method gained parameter and return annotations. A few shared
type aliases keep the signatures short:

```python
# movement.py
Cell = Tuple[int, int]
# ghost.py
Color = Tuple[int, int, int]
```

Representative before/after:

```python
# before
def pixel_to_cell(x, y, cell, offset_x, offset_y):
    ...
# after
def pixel_to_cell(
    x: int, y: int, cell: int, offset_x: int, offset_y: int
) -> Tuple[int, int]:
    ...
```

```python
# before
def handle_event(self, event):
    ...
# after
def handle_event(self, event: pygame.event.Event) -> Optional[str]:
    ...
```

Optional attributes are typed explicitly so mypy tracks the `None` case:

```python
self.game_over_time: Optional[int] = None      # Player
self.victory_time: Optional[int] = None         # GameDemo
self.game: Optional[GameDemo] = None            # App
self.end_screen: Optional[NameEntryScreen] = None
```

**One subtle case** — `GameDemo` creates `self.player`, `self.grid`,
`self.pacgums` and `self.ghosts` inside `_start_level()`, not `__init__`, and
uses `hasattr(self, "player")` to detect the very first level build. mypy can't
infer those types from a conditional attribute, so they're declared (without a
value) at class level:

```python
class GameDemo:
    player: Player
    grid: List[List[str]]
    pacgums: PacgumManager
    ghosts: GhostManager
```
- These are pure type declarations — they create no attribute at runtime, so the
  `hasattr` trick still works, but mypy now knows `self.player` is a `Player`.

In `app.py`, the per-frame handlers use `assert self.game is not None` etc.
before touching an optional screen — this both documents the invariant ("this
handler only runs in the GAME state, where `self.game` exists") and satisfies
mypy's `None`-narrowing.

### Result
```
$ mypy src pac-man.py
Success: no issues found in 14 source files
```

---

## Step 2 — Task 10.2: a docstring on every class and function (PEP 257)

### What this contributes
Another hard grading requirement. Every class and function now opens with a
one-line (or Args/Returns) docstring, following Google style where parameters
warrant it.

### How it was applied
Every `class` and `def` gained a docstring. Simple helpers get a one-liner;
anything with parameters or edge cases documents them:

```python
def can_go(grid: List[List[str]], row: int, col: int, direction: str) -> bool:
    """Return ``True`` if the cell ``direction`` leads into is a corridor.

    Args:
        grid: The expanded maze grid of cell-type strings.
        row: Current row.
        col: Current column.
        direction: One of the keys in :data:`_DIRECTIONS`.

    Returns:
        ``True`` when the neighbouring cell exists and is a ``"CORRIDOR"``.
    """
```

```python
def collect(self, cell_pos: Cell) -> Optional[str]:
    """Eat and remove the pac-gum at ``cell_pos``.

    Returns:
        ``"PACGUM"``, ``"SUPER"``, or ``None`` if the cell was empty.
    """
    return self.pacgums.pop(cell_pos, None)
```

Every module also gained a top-of-file docstring explaining its role (e.g.
`highscore.py`: *"the persistent highscore store … the ONLY thing that ever
touches the highscore file on disk"*). The dense inline `NEW:` / `CHANGED:`
comments from earlier phases were preserved — the docstrings sit **alongside**
them, summarising intent while the comments still explain the line-level "why".

---

## Step 3 — Task 10.3: zero flake8 warnings

### What this contributes
`flake8 .` must report nothing. This catches unused imports, inconsistent
whitespace, over-long lines and other style drift that makes code harder to read.

### How it was applied
Running `flake8` on the pre-pass code reported **32 issues**. They fell into a
handful of categories, all fixed:

- **`E501` line too long** — long image-path lists and comment lines wrapped
  across multiple lines (e.g. the three Pac-Man frame paths in `Player.py`, the
  chase-contact `if` in `GameDemo.py`).
- **`E225` missing whitespace around operator** — `config.py` and
  `maze_loader.py` had `self.lives<=0`, `cell & 1==0` etc.; spaced out to
  `self.lives <= 0`, `cell & 1 == 0`.
- **`W291` / `W293` trailing / blank-line whitespace** and **`E303` too many
  blank lines** — cleaned up in `config.py` and `maze_loader.py`.
- **`E302` expected 2 blank lines** — the class definitions in `config.py` and
  `maze_loader.py` were separated properly.
- **Unused symbols** — the never-used `_STATES = [...]` list in `ghost.py` was
  deleted.

Representative fix:

```python
# before  (config.py — E225, E211, E501)
if self.points_per_pacgum < 0 or self.points_per_super_pacgum <0 or self.points_per_ghost <0:
    print ("Warning: Points values must be non-negative. ...")
# after
if (
    self.points_per_pacgum < 0
    or self.points_per_super_pacgum < 0
    or self.points_per_ghost < 0
):
    print(
        "Warning: Points values must be non-negative. "
        "Using default values of 10, 50, and 200 respectively."
    )
```

### Result
```
$ flake8 src pac-man.py
$   # (no output = clean)
```

---

## Step 4 — Task 10.4: exception-handling audit

### What this contributes
The subject warns: *"if your program crashes … it will be considered
non-functional."* This step guarantees **zero tracebacks** on the failure modes
a reviewer will actually try: a missing/corrupt config, a corrupt highscore
file, bad CLI args, and missing asset files.

### How it was applied
Most I/O was already guarded (Phase 7 hardened the highscore file; fonts and
most images already had try/except). The audit tightened the remaining gaps:

- **Every file `open()` uses a context manager inside a try/except.** `config.py`
  now catches `OSError` alongside `FileNotFoundError`/`JSONDecodeError`, and adds
  `encoding="utf-8"`:

```python
try:
    with open(config_file, 'r', encoding="utf-8") as f:
        lines = f.readlines()
    ...
except FileNotFoundError:
    ... config_data = {}
except (json.JSONDecodeError, OSError) as e:
    ... config_data = {}
```

- **The last unguarded asset load — Pac-Man's own sprites — now degrades
  gracefully.** Previously `Player.__init__` loaded the three mouth frames with a
  bare `pygame.image.load`, which would crash if an image was missing (the
  pac-gums and ghosts already fell back to plain shapes; the player didn't). It
  now matches that pattern:

```python
def _load_frames(self, figure_paths: List[str]) -> List[pygame.Surface]:
    """Load and scale the three mouth frames, or a circle fallback."""
    try:
        raw_frames = [pygame.image.load(p).convert_alpha() for p in figure_paths]
        return [pygame.transform.scale(f, (self.cell, self.cell)) for f in raw_frames]
    except (FileNotFoundError, pygame.error):
        print("Warning: Pac-Man images not found, using a plain circle.")
        fallback = pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)
        pygame.draw.circle(
            fallback, (255, 255, 0),
            (self.cell // 2, self.cell // 2), self.cell // 2
        )
        return [fallback, fallback, fallback]
```

- The maze generator call was already wrapped (Task 2.2), returning `None` on
  failure so `GameDemo` can bail to the menu instead of crashing.

### Verification (the "chaos" test)
A dedicated headless test fed the game every hostile input and confirmed **no
traceback in any case** — all 9 checks passed:

| Hostile input | Result |
|---------------|--------|
| Missing config file | Falls back to defaults |
| Corrupt (invalid-JSON) config | Falls back to defaults |
| Out-of-range values (`lives:-5`, `width:0`, `seed:"x"`) | Each clamped to its default |
| Corrupt highscore file | Table starts empty, warning printed |
| Wrong-shape highscore (object, not list) | Table starts empty |
| Missing Pac-Man sprites | Falls back to a yellow circle |
| `python pac-man.py` with no args | Prints usage, exits 1, **no traceback** |

---

## Verification summary

After the whole pass:

```
$ flake8 src pac-man.py          # clean (0 warnings)
$ mypy src pac-man.py            # Success: no issues found in 14 source files
```

And **every behaviour test from the earlier phases still passes unchanged** — 21
checks for Tasks 8.5–9.1, 10 for the App state machine, 9 for the exception
audit, plus a 400-frame play-loop integration — confirming the quality pass
changed *how the code reads*, not *what it does*.

## Status after this phase

| Task | Status |
|------|--------|
| 10.1 Type hints + mypy | ✅ Done (strict flags, 14 files clean) |
| 10.2 Docstrings (PEP 257) | ✅ Done (every module, class and function) |
| 10.3 Flake8 compliance | ✅ Done (32 issues fixed, `setup.cfg` added) |
| 10.4 Exception handling audit | ✅ Done (all I/O guarded; zero tracebacks on hostile input) |

**Note:** per the plan, work stops at Phase 10. Phases 11–13 (packaging,
deployment, README/project-management docs, final playtest) are intentionally
**not** part of this batch.
