# Pac-Man Project — Full Task Plan

This plan follows the order you should actually build the project in, from where you are now (a basic moving/animated Pac-Man prototype) to a fully finished, submittable, peer-reviewable game. Each task explains **why it matters** and breaks down into **subtasks**.

---

## PHASE 0 — Foundation Cleanup (light refactor only)

### Task 0.1 — Finish the animation + game-over timing fix
**What it brings:** Removes the blocking `time.sleep()` calls so the game loop never freezes. This is required by the subject ("robust error handling, no crash" mindset extends to "no freezing").
**Subtasks:**
- [x] Confirm mouth animation cycles correctly in all 4 directions
- [x] Confirm game-over timer uses `get_ticks()` instead of `time.sleep()`
- [x] Confirm pacman is not drawn over the Game Over screen (use `else` branch)
- [x] Remove unused `import time`

### Task 0.2 — Create `game_state.py`
**What it brings:** A single source of truth for "which screen is currently active." Every later screen (pause, victory, highscores) plugs into this instead of creating its own separate loop. Without this, the codebase becomes unmanageable once you add 5+ screens.
**Subtasks:**
- [x] Create the `GameState` class with constants (MAIN_MENU, GAME, PAUSE, GAME_OVER, VICTORY, HIGHSCORES, INSTRUCTIONS)
- [x] Add `switch_to()` and `is_x()` helper methods
- [x] Do NOT migrate old code yet — just have the file ready

### Task 0.3 — Set up project skeleton matching subject requirements
**What it brings:** The subject grades structure, not just gameplay. Get the skeleton right early so you're not reshuffling files mid-project.
**Subtasks:**
- [x] Create folder structure: `src/`, `assets/` (images, fonts), `project-management/`, `tests/`
- [x] Create `Makefile` with `install`, `run`, `debug`, `clean`, `lint`, `lint-strict`
- [x] Create `.gitignore` (pycache, .mypy_cache, venv, etc.)
- [x] Create `requirements.txt` (pygame, mypy, flake8, pytest)
- [x] Create empty `config.json` placeholder

---

## PHASE 1 — Configuration System

### Task 1.1 — Config file loader with comment support
**What it brings:** This is the literal entry point of the program (`python3 pac-man.py config.json`). Nothing else can be properly tested without it, since lives, pacgum count, scoring values, and level count all come from here.
**Subtasks:**
- [x] Write a function that reads the file and strips `#` comment lines before parsing
- [x] Parse remaining content as JSON
- [x] Define all required keys with safe defaults (highscore_filename, level array, width, height, lives, pacgum, points_per_pacgum, points_per_super_pacgum, points_per_ghost, seed, level_max_time)
- [x] Build a `Config` dataclass or simple class to hold parsed values with type hints

### Task 1.2 — Faulty config handling
**What it brings:** The subject explicitly states the config will be modified during your defense to test robustness. This task is directly graded.
**Subtasks:**
- [x] Missing key → use default, print a clear log message, continue
- [x] Invalid value (e.g. negative lives, non-int) → clamp to default, log message
- [x] Unknown key → silently ignore
- [x] Missing file / file not found → clean error message, exit code, NO traceback
- [x] File exists but is not valid JSON after comment stripping → clean error, no traceback
- [x] Write simple manual tests (not graded, just for yourself) for each bad-input case

### Task 1.3 — CLI entry point: `pac-man.py`
**What it brings:** The actual program launcher required by the subject's usage spec.
**Subtasks:**
- [x] Accept exactly one CLI argument
- [x] Validate argument count and file extension
- [x] Load config via Task 1.1/1.2 logic
- [x] Pass loaded config into the game state / main loop

---

## PHASE 2 — Maze Generation Integration

### Task 2.1 — Install and wrap the assigned A-Maze-ing package
**What it brings:** This is a hard requirement — you are NOT allowed to write your own generator. Getting this working early de-risks the whole project, since everything else (ghosts, pacgums, player spawn) depends on having a maze.
**Subtasks:**
- [x] Install the assigned package (pip/local)
- [x] Read its actual interface/docs to learn its function signatures
- [x] Write a `MazeLoader` adapter class that calls the package and converts its output into your own internal grid format (e.g. 2D list of WALL/CORRIDOR)
- [x] Always call with `PERFECT=False`
- [x] Level 1 uses config's fixed seed; levels 2+ use random seeds

### Task 2.2 — Handle maze generator failure cleanly
**What it brings:** Directly required by subject: "If the generator fails, you must handle the error cleanly."
**Subtasks:**
- [x] Wrap generator call in try/except
- [x] On failure, log a clear message and either retry once or exit cleanly (decide and document which)
- [x] Test by temporarily feeding it a broken parameter to confirm no traceback appears

### Task 2.3 — Render the maze
**What it brings:** Without this you can't see or test anything visually — this is the first real visual milestone after the config/maze logic.
**Subtasks:**
- [x] Draw WALL cells as colored blocks
- [x] Draw CORRIDOR cells as background
- [x] Scale cell size dynamically to width/height from config
- [x] Confirm rendering matches maze data exactly (no off-by-one errors)

---

## PHASE 3 — Player & Core Movement

### Task 3.1 — Refactor Player into its own class (Player.py)
**What it brings:** Moves from "demo" code into real reusable architecture as required by "object-oriented programming, modular, reusable architecture."
**Subtasks:**
- [x] Move x, y, speed, direction, frames, animation logic out of `GameDemo.py` into `Player` class
- [x] Keep the chewing animation logic (already working)
- [x] Add `lives` attribute (from config)

### Task 3.2 — Grid-based movement + wall collision
**What it brings:** Currently pacman moves freely in open space. Real Pac-Man requires movement constrained to maze corridors — this is core to making it actually feel like the game.
**Subtasks:**
- [x] Convert pixel position to maze grid cell
- [x] Block movement into WALL cells
- [x] Decide and implement: free-pixel movement with collision checks, OR strict cell-snapping movement
- [x] Test all 4 directions against various wall configurations

### Task 3.3 — Player spawn at maze center + respawn on death
**What it brings:** Required by subject ("the player starts in the middle of the maze," "respawns in the middle after losing a life").
**Subtasks:**
- [x] Calculate maze center cell dynamically (not hardcoded)
- [x] Place player there on level start
- [x] On life loss, reset position to center
- [x] Add short respawn invincibility window (e.g. 1 second) to avoid instant double-death

### Task 3.4 — Lives, death, and Game Over condition
**What it brings:** Implements the actual lose-condition of the game loop described in the subject.
**Subtasks:**
- [x] Lose 1 life on ghost contact (placeholder collision for now, real ghost logic comes later)
- [x] Trigger Game Over screen when lives reach 0
- [x] Confirm Game Over uses non-blocking timer (already solved in Phase 0)

---

## PHASE 4 — Pacgums, Super-Pacgums, and Scoring

### Task 4.1 — Place pacgums and super-pacgums
**What it brings:** Required maze content — also the core "objective" of each level (eat all pacgums to win).
**Subtasks:**
- [x] Place small pacgum dot in every corridor cell except player start
- [x] Place super-pacgum in each of the 4 corners (or nearest valid corridor if corner is a wall)
- [x] Track total pacgum count for win-condition checking

### Task 4.2 — Collection logic and scoring
**What it brings:** Implements the scoring system described in section 6.2 and 6.6 of the subject.
**Subtasks:**
- [x] On player entering pacgum cell: remove dot, add `points_per_pacgum`
- [x] On player entering super-pacgum cell: remove it, add `points_per_super_pacgum`, trigger ghost edible mode (timer-based, placeholder until ghosts exist)
- [x] Ensure score never decreases
- [x] Display live score (used later by HUD)

### Task 4.3 — Level win condition
**What it brings:** Required game loop step: "Win or Lose" after eating all pacgums.
**Subtasks:**
- [x] Detect when remaining pacgum count hits 0
- [x] Transition to next level (new maze, same score/lives carried over)
- [x] Detect when final level (≥10) is completed → trigger Victory screen

---

## PHASE 5 — Ghosts

### Task 5.1 — Ghost base class and spawning
**What it brings:** Core antagonist mechanic — without ghosts there is no actual Pac-Man game, just a maze walker.
**Subtasks:**
- [x] Create `Ghost` class with position, speed, state (CHASE/FLEE/EATEN)
- [x] Spawn 4 ghosts, one per maze corner
- [x] Load the 4 ghost sprite images you already have (pink, orange, cyan, red)
- [x] Implement basic corridor-constrained movement (same wall logic as player)

### Task 5.2 — Chase behavior
**What it brings:** Required behavior: "Chase the player when not edible."
**Subtasks:**
- [ ] Choose and implement a chase algorithm (recommend: simple distance-based direction choice at each intersection — easiest to get working correctly)
- [x] Document the choice and reasoning in README later
- [x] Test all 4 ghosts chase simultaneously without freezing or glitching

### Task 5.3 — Flee behavior (edible ghosts)
**What it brings:** Required behavior tied to super-pacgum mechanic — this is what makes super-pacgums meaningful.
**Subtasks:**
- [x] On super-pacgum pickup, switch all ghosts to FLEE state for a fixed duration
- [x] In FLEE state, ghost moves away from player instead of toward
- [x] Change ghost sprite/color while fleeing (visual feedback)
- [x] Flash warning in the last ~2 seconds before flee ends
- [x] On timer expiry, return surviving ghosts to CHASE

### Task 5.4 — Eaten ghost + respawn
**What it brings:** Completes the scoring loop (`points_per_ghost`) and the cycle described in section 6.3.
**Subtasks:**
- [x] Detect collision between player and FLEE-state ghost → EATEN state, add `points_per_ghost`
- [x] Ghost disappears or shows "eyes only" sprite
- [x] After 5–10 seconds (configurable), ghost respawns at its corner in CHASE state

### Task 5.5 — Real player/ghost collision (replaces placeholder)
**What it brings:** Connects ghosts to the life-loss system built in Phase 3.
**Subtasks:**
- [x] Detect collision between player and CHASE-state ghost → lose life, respawn player
- [x] Confirm FLEE-state ghosts do not cause life loss
- [x] Confirm respawn invincibility window prevents double-hits

---

## PHASE 6 — Level Progression & Timer

### Task 6.1 — Per-level countdown timer
**What it brings:** Required HUD element and game-progression rule (`level_max_time`).
**Subtasks:**
- [x] Countdown from `level_max_time` each level using `get_ticks()` (non-blocking)
- [x] Decide behavior on timer expiry (restart level vs. game over) and document it
- [ ] Pause timer when game is paused (after Phase 8)

### Task 6.2 — Multi-level progression (≥10 levels)
**What it brings:** Required minimum level count and the "win the game" condition.
**Subtasks:**
- [x] Loop level generation using config's `level` array (or generate procedurally if array shorter than 10)
- [x] Carry score and lives across levels
- [x] Reset pacgum/super-pacgum/ghost positions each level
- [x] Confirm seed logic: level 1 fixed seed, levels 2+ random

---

## PHASE 7 — Highscore System

### Task 7.1 — Persistent JSON highscore storage
**What it brings:** Required feature — also one of the explicitly graded README sections.
**Subtasks:**
- [ ] Create `HighscoreManager` class with `load()`, `save()`, `add(name, score)`, `get_top10()`
- [ ] Store as JSON file (path from config's `highscore_filename`)
- [ ] Validate name: max 10 chars, alphanumeric + spaces only
- [ ] Validate score: non-negative integer
- [ ] Keep only top 10, sorted descending

### Task 7.2 — Corrupted/missing file handling
**What it brings:** Required robustness ("robust to file errors").
**Subtasks:**
- [ ] Missing file on first run → create new empty list, no crash
- [ ] Corrupted/invalid JSON → reset to empty list, log warning, no crash
- [ ] Confirm save happens at game end always (win or lose)

### Task 7.3 — Name entry UI
**What it brings:** Connects the highscore system to actual gameplay flow ("Enter name for highscore" step in the game loop).
**Subtasks:**
- [ ] Build simple text input screen after Game Over / Victory
- [ ] Real-time input validation (block invalid characters, enforce 10-char limit)
- [ ] On confirm, save score and return to Main Menu

---

## PHASE 8 — Full UI/Screens via GameState

### Task 8.1 — Migrate to single main loop driven by GameState
**What it brings:** This is the big refactor flagged earlier — now is the right time, since all core mechanics exist and adding more screens without this would create duplicate loops everywhere.
**Subtasks:**
- [ ] Remove `while` loop from `GameDemo.py` — convert to `update()` + `draw()` methods called once per frame
- [ ] Build one main loop in `pac-man.py` (or a new `main.py`) that checks `GameState.current` and dispatches to the right update/draw functions
- [ ] Confirm Main Menu and Game both work through the unified loop before continuing

### Task 8.2 — Main Menu screen
**What it brings:** Required entry screen.
**Subtasks:**
- [ ] Buttons: New Game, View Highscores, Instructions, Exit
- [ ] Hover cursor effect (already implemented, just migrate it)
- [ ] Display top highscores preview

### Task 8.3 — In-Game HUD
**What it brings:** Required always-visible gameplay info.
**Subtasks:**
- [ ] Score, lives, current level, remaining time
- [ ] Position HUD so it never overlaps the maze

### Task 8.4 — Pause Menu
**What it brings:** Required feature ("player can pause and resume").
**Subtasks:**
- [ ] P or ESC toggles `GameState.PAUSE`
- [ ] Freeze all movement, timers, ghost logic while paused
- [ ] Resume / Return to Main Menu options

### Task 8.5 — Game Over screen
**What it brings:** Required end-of-game screen.
**Subtasks:**
- [ ] Show final score
- [ ] Trigger name-entry flow (Task 7.3)
- [ ] Return to Main Menu after save

### Task 8.6 — Victory screen
**What it brings:** Required win-condition screen.also want to change the speed of the ghosts in flee mode 
**Subtasks:**
- [ ] Show congratulatory message + final score
- [ ] Trigger name-entry flow (Task 7.3)
- [ ] Return to Main Menu after save

### Task 8.7 — Highscores screen
**What it brings:** Required main-menu feature.
**Subtasks:**
- [ ] Display ranked top 10 (position, name, score)
- [ ] Handle empty list ("No scores yet")
- [ ] Return to Main Menu

### Task 8.8 — Instructions screen
**What it brings:** Required main-menu feature; also helps reviewers understand controls quickly.
**Subtasks:**
- [ ] List movement controls
- [ ] Explain pacgum/super-pacgum/ghost mechanics briefly
- [ ] List cheat mode keys (once Phase 9 exists)

---

## PHASE 9 — Cheat Mode

### Task 9.1 — Implement cheat toggles
**What it brings:** Required for peer review — reviewers need to test win/lose/ghost behavior quickly without playing a full 90-second level normally.
**Subtasks:**
- [ ] Invincibility toggle
- [ ] Level skip
- [ ] Ghost freeze
- [ ] Extra life
- [ ] Speed boost
- [ ] Display active cheats on HUD
- [ ] Document keys in Instructions screen

---

## PHASE 10 — Code Quality Pass

### Task 10.1 — Type hints + mypy
**What it brings:** Hard grading requirement.
**Subtasks:**
- [ ] Add type hints to every function/class across all files
- [ ] Run `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`
- [ ] Fix all reported errors

### Task 10.2 — Docstrings (PEP 257)
**What it brings:** Hard grading requirement.
**Subtasks:**
- [ ] Add docstrings to every class and function (Google or NumPy style)
- [ ] Document Args/Returns/Raises where relevant

### Task 10.3 — Flake8 compliance
**What it brings:** Hard grading requirement.
**Subtasks:**
- [ ] Run `flake8 .` and fix all reported issues
- [ ] Add `.flake8` or `setup.cfg` if custom line-length rules needed

### Task 10.4 — Exception handling audit
**What it brings:** Hard grading requirement ("if your program crashes... it will be considered non-functional").
**Subtasks:**
- [ ] Wrap every file I/O operation in try/except with context managers
- [ ] Wrap maze generator calls (already done in Task 2.2)
- [ ] Manually test: delete config, corrupt highscore file, bad CLI args, missing assets — confirm zero tracebacks

---

## PHASE 11 — Packaging & Deployment

### Task 11.1 — Build standalone executable
**What it brings:** Required deliverable — the game must run without Python installed.
**Subtasks:**
- [ ] Use PyInstaller (or similar) to bundle the game
- [ ] Test the built executable runs standalone on a clean environment
- [ ] Write the build script and place it at repo root

### Task 11.2 — Deploy to Itch.io (or Steam)
**What it brings:** Required public deployment for demonstration.
**Subtasks:**
- [ ] Create unlisted/private free build on Itch.io
- [ ] Include minimal in-package instructions (controls, config, options)
- [ ] Confirm build can be regenerated on request during peer review

---

## PHASE 12 — Documentation

### Task 12.1 — Write README.md
**What it brings:** Required deliverable, graded section by section.
**Subtasks:**
- [ ] Italic first line with logins
- [ ] Description
- [ ] Instructions
- [ ] Resources (+ AI usage disclosure)
- [ ] Configuration (all keys/defaults documented)
- [ ] Highscore (design + reasoning)
- [ ] Maze Generation (how A-Maze-ing package is used)
- [ ] Implementation summary
- [ ] General Software Architecture (modules/classes/relationships)
- [ ] Project Management overview + link to `/project-management`
- [ ] Confirm entire file is in English

### Task 12.2 — Project management artifacts
**What it brings:** Required deliverable, separately graded from README.
**Subtasks:**
- [ ] Timeline/Gantt or Kanban board (can literally be this task plan, formalized)
- [ ] Progress tracking vs. plan
- [ ] Risk analysis + mitigations
- [ ] Team organization (if solo, document your own role/process)
- [ ] Acceptance test plan (features tested, bugs found/fixed)
- [ ] Summary of blocking points encountered

---

## PHASE 13 — Final Verification

### Task 13.1 — Full playtest pass
**What it brings:** Catches integration bugs before submission.
**Subtasks:**
- [ ] Play through all 10+ levels start to finish
- [ ] Test every cheat mode key
- [ ] Test pause/resume mid-ghost-chase
- [ ] Test highscore save/load across multiple runs

### Task 13.2 — Fresh-environment test
**What it brings:** Simulates what your peer reviewer will actually do (reinstall the A-Maze-ing package, run from scratch).
**Subtasks:**
- [ ] Clone repo into a brand new folder
- [ ] Run `make install && make run` with zero manual fixes
- [ ] Confirm `make lint` passes cleanly
- [ ] Confirm packaged build still launches correctly
