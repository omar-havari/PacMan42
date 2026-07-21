# Phase 9 (Task 9.1) — Cheat Mode — Change Log

This document walks through **every change made for Phase 9**, in the order the
work was done. For each step it explains:

- **What the step contributes to the project** (why it matters).
- **A line-by-line reading of the code** (what each line does syntactically).

Phase 9 adds a **cheat mode** so a peer reviewer can test win/lose/ghost
behaviour quickly without playing a full 90-second level normally. Five cheats
are required: invincibility, level skip, ghost freeze, extra life, and speed
boost — plus a HUD readout of the active cheats and documentation of the keys
in the Instructions screen.

All of the logic lives in **`src/GameDemo.py`** (the in-game screen), with one
small supporting change in **`src/Player.py`** (a safe speed boost). The cheat
keys are also documented in **`src/screens.py`** (`InstructionsScreen`) — that
part is covered in the Task 8.8 change log.

Files changed, in order:

1. `src/Player.py` — an alignment-safe speed boost (`set_speed_boost`)
2. `src/GameDemo.py` — the cheat keys, their effects, and the HUD readout

---

## The key-choice principle

```python
_CHEAT_INVINCIBLE = pygame.K_i
_CHEAT_GHOST_FREEZE = pygame.K_g
_CHEAT_SPEED_BOOST = pygame.K_b
_CHEAT_EXTRA_LIFE = pygame.K_l
_CHEAT_SKIP_LEVEL = pygame.K_n
```
- The five cheat keys as module-level constants. They are deliberately chosen to
  **never collide** with the arrow keys (movement) or `P`/`ESC` (pause), so a
  cheat can be pressed at any time during play without accidentally steering
  Pac-Man or pausing. Keeping them in one place means the handling below and the
  Instructions screen document the exact same keys.

```python
_CHEAT_COLOR = (255, 0, 255)
```
- Magenta — the same colour as the hidden "42" in the maze — so the active-cheat
  readout reads as an obviously non-standard debug overlay.

---

## Step 1 — `src/Player.py`: an alignment-safe speed boost

### What this contributes
The speed-boost cheat needs Pac-Man to move faster. But his whole movement
system relies on an **invariant**: his step size must divide the cell size
evenly, or he'd step *over* the exact alignment point between two cells and the
"am I aligned?" check would never be true again — meaning he could never turn or
be stopped by a wall (he'd walk through them). Naïvely doubling the step size
breaks that invariant. The fix is to double the speed by taking **two whole
base-speed steps per frame** instead of one bigger step — each sub-step still
lands exactly on the grid.

### Line-by-line

```python
        self.steps_per_frame = 1
```
- In `__init__`: how many base-speed steps `update()` takes per frame. `1` is
  normal; the speed-boost cheat sets it to `2`. Because each step is a full
  base-speed move (which divides the cell), boosting never skips an alignment
  point.

```python
    def set_speed_boost(self, on):
        self.steps_per_frame = 2 if on else 1
```
- The toggle: `on=True` → two steps per frame (double speed); `on=False` → back
  to one. That's the entire boost — no change to `self.speed`, so the alignment
  invariant is untouched.

```python
    def update(self):
        if self.game_over_time:
            return pygame.time.get_ticks() - self.game_over_time >= 4000
        for _ in range(self.steps_per_frame):
            self._step()
        return False
```
- `update()` used to contain the movement logic directly. It now **loops**
  `self._step()` `steps_per_frame` times. Normally that's one call (identical to
  before); boosted, it's two — Pac-Man advances twice as far, but in two legal
  base-speed hops that both respect walls and turns.

```python
    def _step(self):
        # ... the exact movement/turn/animation body that used to live in update() ...
```
- `_step()` is the old `update()` body, extracted verbatim (opposite-turn
  handling, the grid-alignment turn/wall check, the move, and the mouth
  animation). Extracting it is what lets `update()` run it more than once per
  frame without duplicating any logic.

---

## Step 2 — `src/GameDemo.py`: the cheats and their effects

### What this contributes
`GameDemo` is where the cheats actually take effect: it reads the cheat keys,
holds the toggle state, applies each cheat's effect in the right place in the
per-frame logic, and draws the active-cheat readout.

### 2a — the toggle state

```python
        self.cheat_invincible = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_boost = False
```
- In `__init__`: the on/off state for the three **toggle** cheats. Extra-life
  and level-skip are one-shot **actions** (they happen once when pressed) and so
  need no flag. These are set **before** `_start_level()` runs, because
  `_start_level()` re-applies the speed boost to each freshly-built player.

### 2b — reading the keys

```python
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self._apply_cheat(event.key)
        self.player.handle_event(event)
```
- On any key-down, try to apply a cheat, **then** still forward the event to the
  player. This is safe because the cheat keys aren't arrow keys (the player
  ignores them) and arrow keys never match a cheat — so the two never interfere.

```python
    def _apply_cheat(self, key):
        if key == _CHEAT_INVINCIBLE:
            self.cheat_invincible = not self.cheat_invincible
        elif key == _CHEAT_GHOST_FREEZE:
            self.cheat_ghost_freeze = not self.cheat_ghost_freeze
        elif key == _CHEAT_SPEED_BOOST:
            self.cheat_speed_boost = not self.cheat_speed_boost
            self.player.set_speed_boost(self.cheat_speed_boost)
        elif key == _CHEAT_EXTRA_LIFE:
            self.player.lives += 1
        elif key == _CHEAT_SKIP_LEVEL:
            self._cheat_skip_level()
```
- `not self.cheat_*` — each toggle flips its flag on/off.
- For the speed boost, the new state is pushed straight to the current player
  via `set_speed_boost` (Step 1), so it takes effect immediately.
- `self.player.lives += 1` — the extra-life cheat, a one-shot bump.
- `self._cheat_skip_level()` — the level-skip cheat (below).
- Any other key falls through and does nothing.

### 2c — level skip

```python
    def _cheat_skip_level(self):
        if not self.is_pausable():
            return
        if self.level >= MAX_LEVEL:
            self.victory_time = pygame.time.get_ticks()
        else:
            self.level += 1
            if not self._start_level():
                self.failed = True
```
- `if not self.is_pausable(): return` — only during real play, not over a
  game-over/victory takeover (same guard the pause uses), so you can't skip a
  screen that isn't a level.
- `if self.level >= MAX_LEVEL:` — on the last level, skipping means **winning**:
  set `victory_time`, which `update()` turns into the Victory flow (Task 8.6).
- Otherwise bump the level and rebuild it with `_start_level()`. This **mirrors
  the real "all pac-gums eaten" win branch** in `update()`, so a skipped level
  behaves exactly like a genuinely cleared one (score and lives carry over). If
  the rebuild fails, `self.failed = True` sends the game cleanly back to the menu.

### 2d — invincibility (in `update()`)

```python
        if (
            not self.cheat_invincible
            and not self.player.is_invincible()
            and self.ghosts.resolve_chase_contact(self.player.current_cell())
        ):
            self.player.lives -= 1
            ...
```
- The life-loss check gains one more guard: `not self.cheat_invincible`. With
  the cheat on, a chase-ghost touching Pac-Man never costs a life — on top of
  the normal post-respawn grace window (`is_invincible()`). `and`
  short-circuits, so when the cheat is on the contact test isn't even run.

### 2e — ghost freeze (in `update()`)

```python
        fright_remaining = self.fright_until - pygame.time.get_ticks()
        if not self.cheat_ghost_freeze:
            self.ghosts.update(self.player.current_cell(), fright_remaining)
```
- The ghosts' movement update is simply **skipped** when the cheat is on, so
  they stay frozen exactly where they are. They are still drawn (their `draw`
  runs later) and still dangerous on contact — the cheat only stops them
  *hunting*, which is enough to make a level easy to walk through.

### 2f — re-applying the boost across level builds

```python
        self.player = Player(self.screen, lives, self.grid, cell, offset_x, offset_y)
        self.player.set_speed_boost(self.cheat_speed_boost)
```
- Inside `_start_level()`: a brand-new `Player` always starts un-boosted, so
  right after building it we re-apply the current speed-boost state. Without
  this, the boost would silently switch off whenever you skip or clear a level.

### 2g — the HUD readout

```python
    def _draw_cheats(self):
        active = []
        if self.cheat_invincible:
            active.append("INVINCIBLE")
        if self.cheat_ghost_freeze:
            active.append("GHOST-FREEZE")
        if self.cheat_speed_boost:
            active.append("SPEED")
        if not active:
            return
        text = "CHEATS: " + "  ".join(active)
        surface = self.hud_font.render(text, False, _CHEAT_COLOR)
        y = self.screen.get_height() - surface.get_height() - 10
        self.screen.blit(surface, (10, y))
```
- Collects the names of the currently-active **toggle** cheats into a list.
- `if not active: return` — draws **nothing** when no cheats are on, so a normal
  game looks exactly as before (no clutter).
- `"CHEATS: " + "  ".join(active)` — joins the active names into one line, drawn
  magenta in the bottom-left corner (below the maze, clear of the top HUD).
  Extra-life and level-skip aren't shown because they aren't ongoing states —
  their effect (a higher lives count / a higher level) is already visible in the
  main HUD.

```python
        self._draw_hud()
        self._draw_cheats()
```
- In `draw()`, the cheat readout is drawn right after the normal HUD, on top of
  everything, only on the real gameplay frame (not the countdown/takeover
  screens).

---

## The cheat map (quick reference)

| Key | Cheat | Type | Effect |
|-----|-------|------|--------|
| `I` | Invincibility | toggle | Chase-ghost contact never costs a life |
| `G` | Ghost freeze | toggle | Ghosts stop moving (still drawn, still solid) |
| `B` | Speed boost | toggle | Pac-Man moves at double speed (alignment-safe) |
| `L` | Extra life | one-shot | `+1` life immediately |
| `N` | Skip level | one-shot | Jump to the next level (or win on level 10) |

These keys are also listed on the **Instructions screen** (Task 8.8), in magenta
to match the in-game readout.

---

## Verification

A headless test (`SDL_VIDEODRIVER=dummy`) exercised every cheat directly and
**all checks passed**:

- **Toggles** — `I`, `G`, `B` each flip on then off; `B` sets the player's
  `steps_per_frame` to 2 and back to 1.
- **Extra life** — `L` increases `lives` by exactly 1.
- **Level skip** — `N` advances the level; repeated presses reach level 10 and
  then set `victory_time` (win).
- **Ghost freeze** — with the cheat on, ghost pixel positions are identical
  before and after an `update()`.
- **Invincibility** — a chase ghost placed on Pac-Man's cell costs a life
  normally, but **not** while the cheat is on.
- **Persistence** — the speed boost is correctly re-applied to the new player
  after a level (re)build.
- **Rendering** — `draw()` with the cheat overlay active runs without error, and
  a 400-frame play-loop with all cheats on advances cleanly.

## Status after this phase

| Task | Status |
|------|--------|
| 9.1 Invincibility toggle | ✅ Done (`I`) |
| 9.1 Level skip | ✅ Done (`N`, wins on level 10) |
| 9.1 Ghost freeze | ✅ Done (`G`) |
| 9.1 Extra life | ✅ Done (`L`) |
| 9.1 Speed boost | ✅ Done (`B`, alignment-safe via `steps_per_frame`) |
| 9.1 Active cheats on HUD | ✅ Done (magenta readout, bottom-left) |
| 9.1 Keys in Instructions | ✅ Done (see Task 8.8) |
