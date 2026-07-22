# Speed & Timer Tuning — line-by-line changes

## What it contributes

The game was effectively unwinnable: the level timer ran out before a level
could be cleared, and everything crawled. This pass makes the whole game play
faster and gives more time per level:

1. **Pac-Man default speed** doubled.
2. **Speed-boost cheat (`B`)** raised accordingly (kept at 2× the base).
3. **Ghost speed** doubled (chase balance vs. Pac-Man preserved).
4. **Per-level timer** raised from 90 s to **120 s**.

## The one constraint that shapes every speed change

Movement is **cell-snapped**. `pick_speed(cell)` / the loop in
`Player.__init__` pick the largest step size that **evenly divides the cell
size**, because the alignment test is an *exact* `position % cell == 0`. A
sprite that moved a non-dividing number of pixels would step *over* the
boundary between two cells and could never turn or be wall-stopped again.

So speed is **never** raised by enlarging the per-step pixel distance. It is
raised by taking **more whole base-speed steps per frame** — each sub-step still
lands exactly on the grid. This is the same alignment-safe trick already used
for the boost cheat; it is now the mechanism for the default speed and the
ghosts too.

Because Pac-Man and the ghosts both moved 1 base-step/frame before, doubling
both to 2 leaves their *relative* speeds unchanged — the chase feels the same,
just faster.

## Files changed

1. `src/Player.py` — default + boost speed via named step constants
2. `src/ghost.py` — ghost speed via a `_step()` sub-step loop
3. `config.json` + `src/config.py` — level timer 90 → 120

---

## Step 1 — `src/Player.py`: default and boost speed

### New module constants

```python
_BASE_STEPS_PER_FRAME = 2
_BOOST_STEPS_PER_FRAME = 4
```

- `_BASE_STEPS_PER_FRAME` — normal play. Was an implicit `1`; **doubled to 2**.
- `_BOOST_STEPS_PER_FRAME` — the `B` speed-boost cheat. Was `2`; **raised to 4**
  so the boost is still exactly **2× the base**, the same ratio as before.

### `__init__`

```python
self.steps_per_frame = _BASE_STEPS_PER_FRAME   # was: self.steps_per_frame = 1
```

- Pac-Man now takes two whole base-speed hops every frame by default.

### `set_speed_boost`

```python
self.steps_per_frame = _BOOST_STEPS_PER_FRAME if on else _BASE_STEPS_PER_FRAME
# was: self.steps_per_frame = 2 if on else 1
```

- On → 4 steps/frame; off → back to the normal 2. Both values are named
  constants now, so the two "speeds" live in one place.
- **No change to `update()` / `_step()`** — the existing
  `for _ in range(self.steps_per_frame)` loop already scales to any value.

---

## Step 2 — `src/ghost.py`: ghost speed

### New module constant

```python
_GHOST_STEPS_PER_FRAME = 2
```

- How many whole base-speed steps a ghost takes per frame while chasing.
  **Doubled from an implicit 1 to 2**, matching Pac-Man's doubled base speed.

### `update()` refactored into `update()` + `_step()`

Previously `update()` did the eaten-guard, then **one** alignment /
direction-pick / move, then set `state`/`flashing`. To move several base-speed
steps per frame (re-checking alignment between each), the single move body was
extracted into a new `_step(target_cell, frightened)` method, and `update()`
now loops it:

```python
        for _ in range(_GHOST_STEPS_PER_FRAME):
            self._step(target_cell, frightened)

        self.state = "FRIGHTENED" if frightened else "CHASE"
        self.flashing = flashing
```

- The eaten-guard and the final `state`/`flashing` assignment stay in
  `update()` (run once per frame). The per-step alignment check, direction
  choice and the `self.x/y += dx/dy * self.speed` move now live in `_step()`
  and run `_GHOST_STEPS_PER_FRAME` times.
- Each `_step()` re-checks `is_aligned(...)` before moving, so cell-snapping and
  wall collisions stay correct at any step count.

### Frightened ghosts stay proportionally slower — automatically

`_step()` still carries the `_frighten_tick % _FRIGHTENED_STEP_EVERY` gate
(`_FRIGHTENED_STEP_EVERY = 2`). With 2 steps/frame, a fleeing ghost actually
moves on **1 of those 2 steps** → half of its normal speed. That is the same
"fleeing = half speed" ratio as before, now doubled along with everything else,
so frightened ghosts remain catchable.

---

## Step 3 — the level timer: 90 → 120 s

### `config.json`

```json
    "level_max_time": 120
```

### `src/config.py`

```python
self.level_max_time: int = config_data.get("level_max_time", 120)   # default 90 → 120
```

```python
                "Using default value of 120."   # warning text
            )
            self.level_max_time = 120            # clamp fallback 90 → 120
```

- Both the `.get()` default and the `_validate()` clamp/warning now use 120, so
  the longer timer is the value used even if `config.json` is missing or a bad
  `level_max_time` is supplied.

---

## Effective speeds (per frame, in base-step units)

| Sprite / mode        | Before | After |
|----------------------|:------:|:-----:|
| Pac-Man normal       |   1    |   2   |
| Pac-Man boosted (`B`)|   2    |   4   |
| Ghost chasing        |   1    |   2   |
| Ghost fleeing        |  0.5   |   1   |

Every value doubled → relative balance unchanged, whole game faster.

## Verification

Headless (`SDL_VIDEODRIVER=dummy`), **all 12 checks passed**, plus a clean lint
gate (`flake8` clean, `mypy` "no issues found in 14 source files"):

| Check | Result |
|-------|--------|
| `level_max_time` from `config.json` is 120 | ✅ |
| `level_max_time` default fallback (missing file) is 120 | ✅ |
| Player base `steps_per_frame` == 2 | ✅ |
| Boost sets it to 4, off restores 2 | ✅ |
| Player moves `2 * speed` px/frame normally, `4 * speed` boosted | ✅ |
| Player stays step-aligned over 200 boosted frames (no clipping) | ✅ |
| Ghost moves `2 * speed` px/frame chasing | ✅ |
| Ghost moves `1 * speed` px/frame while frightened (half) | ✅ |
| Ghost stays step-aligned over 300 frames (no `NameError`, no clip) | ✅ |

## Status

| Ask | Status |
|-----|--------|
| Increase Pac-Man default speed | ✅ Done (1 → 2 steps/frame) |
| Increase boost accordingly | ✅ Done (2 → 4, still 2× base) |
| Increase ghost speed | ✅ Done (1 → 2 steps/frame, flee ratio preserved) |
| Timer to 120 s | ✅ Done (`config.json` + `config.py` default & clamp) |
