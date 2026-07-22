# Graph Report - .  (2026-07-22)

## Corpus Check
- 42 files · ~68,300 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 442 nodes · 704 edges · 37 communities (31 shown, 6 thin omitted)
- Extraction: 85% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.59)
- Token cost: 124,902 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]

## God Nodes (most connected - your core abstractions)
1. `GameDemo` - 28 edges
2. `Config` - 27 edges
3. `HighscoreManager` - 27 edges
4. `App` - 25 edges
5. `Player` - 23 edges
6. `MainMenu` - 21 edges
7. `NameEntryScreen` - 21 edges
8. `MazeGenerator` - 17 edges
9. `GameState` - 17 edges
10. `GhostManager` - 16 edges

## Surprising Connections (you probably didn't know these)
- `NameEntryScreen` --semantically_similar_to--> `run_name_entry (deleted)`  [INFERRED] [semantically similar]
  src/screens.py → C:/Users/keidi/OneDrive/PacMan42/Phase7_Highscores_Changes.md
- `Single GameState-Driven Main Loop` --implements--> `App`  [EXTRACTED]
  C:/Users/keidi/OneDrive/PacMan42/Phase8_UI_Changes.md → src/app.py
- `Screen Contract (handle_event/draw, no own loop)` --rationale_for--> `MainMenu`  [EXTRACTED]
  C:/Users/keidi/OneDrive/PacMan42/Phase8_UI_Changes.md → src/screens.py
- `Cheat Mode` --references--> `InstructionsScreen`  [EXTRACTED]
  C:/Users/keidi/OneDrive/PacMan42/Task9_CheatMode_Changes.md → src/screens.py
- `Strict Type Hints + mypy` --references--> `GameDemo`  [EXTRACTED]
  C:/Users/keidi/OneDrive/PacMan42/Task10_CodeQuality_Changes.md → src/GameDemo.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Number-to-tile maze build pipeline** — src_gamedemo, src_maze_loader, mazegenerator_mazegenerator, maze_build_phases_number_maze, maze_build_phases_tile_maze [EXTRACTED 0.90]
- **Cell-snapped movement system** — src_player, phase4_changes_cell_snapping, phase4_changes_wanted_direction, phase4_changes_two_coordinate_systems [EXTRACTED 0.90]
- **Ghost reuse of player movement manager patterns** — src_ghost, src_player, src_movement, src_pacgums [EXTRACTED 0.85]
- **Pause Time-Shift Fan-Out** — src_gamedemo_gamedemo_shift_time, src_player_player_shift_time, src_ghost_ghostmanager_shift_time, src_ghost_ghost_shift_time, src_app_app__resume [EXTRACTED 1.00]
- **GameState Main-Loop Screen Dispatch** — src_app_app_run, src_screens_mainmenu, src_gamedemo_gamedemo, src_screens_pausemenu, src_game_state_gamestate [EXTRACTED 0.85]
- **Highscore Save/Load Cycle** — src_screens_nameentryscreen, src_highscore_highscoremanager_add, highscores_json, src_screens_mainmenu, src_screens_highscoresscreen [EXTRACTED 0.85]
- **Uniformly Doubled Speeds Preserve Chase Balance** — task_speed_timer_changes_base_player_speed, task_speed_timer_changes_boost_player_speed, task_speed_timer_changes_ghost_step_per_frame, task_speed_timer_changes_frightened_slowdown [INFERRED 0.85]
- **Cell-Snapped Alignment-Safe Sub-Stepping** — task_speed_timer_changes_cell_alignment_invariant, task_speed_timer_changes_steps_per_frame_mechanism, task_speed_timer_changes_pick_speed [EXTRACTED 1.00]

## Communities (37 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (39): Color, Frightened-Ghost Flee-Speed Knob, HowEverythingWorks build guide, Tile maze WALL CORRIDOR grid, get_layout geometry source of truth, Cell-snapped movement, fright_until edible-ghost timer, Grid vs pixel coordinate systems (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (35): Any, Relative Asset-Path Pattern, Blinking Caret via get_ticks, Blocking run_name_entry Bridge Seam (closed), Defensive Font Loader (clean exit on missing font), Game Over / Victory as Proper States, Exception-Handling Audit (zero tracebacks), Persistent Highscore System (+27 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (20): _Button, load_font(), Config, Font, Surface, Draw the panel, title, buttons, icon and score preview., Draw the "TOP SCORES" preview down the right-hand side., Reload the scores from disk so the table is always current. (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (8): Wall bitmask encoding 1-2-4-8, FT_WALL hidden 42 logo, Number maze grid of ints, mazegenerator package top_level.txt, MazeGenerator, Unwinnable-levels pacgum-in-42 bug, Generating the maze grid and drawing it in the classic Pac-Man tube style.  :cla, Generate an expanded ``(2h+1) x (2w+1)`` WALL/CORRIDOR grid.          Args:

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (22): Phase 7 Highscore System Change Log, Phase 8 (8.1-8.4) Unified UI & Screens Change Log, Phase 10 Code Quality Pass Change Log, Task 8 (8.5-8.8) End Screens Change Log, Phase 9 Cheat Mode Change Log, Task 10.1 Type Hints + mypy, Task 10.2 Docstrings, Task 10.3 Flake8 Compliance (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (13): Alignment-Safe Speed Boost (two sub-steps), Non-Colliding Cheat-Key Choice, Cheat Mode, Grid-Alignment Step-Size Invariant, GameDemo._apply_cheat, GameDemo._cheat_skip_level, Return ``True`` only during real play (not over a takeover screen).          Not, Player._step (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (11): Single GameState-Driven Main Loop, GameState, Holds the current screen state and answers ``is_*`` predicates.      The class-l, Start in ``state`` (the main menu by default).          A default is provided so, Change the active state to ``state`` (the only mutator)., Return ``True`` when the main menu is active., Return ``True`` when a game is being played., Return ``True`` when the Game Over screen is active. (+3 more)

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (9): App, Advance and draw the game; enter pause on P/Esc; finish when done., Switch to the proper end state once a game finishes.          A failed maze (nev, Drive the Game Over / Victory screen; return to menu when done., Freeze the current frame as a snapshot and open the pause menu., Draw the frozen snapshot + pause menu; handle Resume / Main Menu., Hand the game the paused duration so no timers advanced, then resume., Rebuild the menu (refreshing its score preview) and switch to it. (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (11): Sectioned Instructions (tuple kind tags), Turn a menu action string into a concrete screen + state change., ImageElement, A tiny helper for loading, scaling and positioning a decorative image., Load ``image_path``, scale it, and centre it on ``target_coordinates``., A pre-scaled image positioned by its centre, ready to blit., HighscoresScreen, InstructionsScreen (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (10): 42 PacMan subject PDF, Mouth animation frame timing, Command-line entry point: validate the args and launch the game.  Usage::, PacMan42 README, Config, Loading and validating the JSON game configuration.  The config file drives ever, Parsed, validated game settings loaded from a JSON file., Read and validate ``config_file``, falling back to defaults.          Args: (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.19
Nodes (9): Flake8 Compliance, Strict Type Hints + mypy, setup.cfg (flake8 + mypy config), GameDemo, Render the current frame (maze/sprites/HUD, or a takeover screen)., Draw score, level, lives and remaining time across the top strip.          Becau, Draw a magenta line listing active cheats (nothing if none are on)., Draw a single large centred line on a black screen.          Used for the Victor (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (8): Screen Contract (handle_event/draw, no own loop), Per-Frame State Dispatch Chain, Event, Drive the highscores screen; return to the menu on BACK., Drive the instructions screen; return to the menu on BACK., Run the main loop: drain events, dispatch by state, present at 60 FPS., Drive the main menu: run any button action, else draw it., Return ``True`` when the game is paused.

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (10): Config, Font, Surface, Load a font, exiting cleanly (no traceback) if the file is missing., Set up the game and build level 1.          Score and level live here (not on th, MazeLoader, Builds and draws the expanded maze grid for a level., PacgumManager (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (7): Event, Return the clicked button's action string (or ``"EXIT"`` on Esc)., Return ``"BACK"`` on Esc/Enter, otherwise ``None``., Return ``"BACK"`` on Esc/Enter, otherwise ``None``., Drive name entry; return ``"DONE"`` once saved or skipped.          Same real-ti, Return a button action, or ``"RESUME"`` on P/Esc., Return ``True`` for a mouse-down inside this button.

### Community 14 - "Community 14"
Cohesion: 0.20
Nodes (12): flake8, mazegenerator wheel, mypy, pygame, Base Player Speed (_BASE_STEPS_PER_FRAME=2), Boost Player Speed (_BOOST_STEPS_PER_FRAME=4), Cell-Alignment Invariant, Frightened-Ghost Slowdown Ratio (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (8): Player, Event, Font, Return ``True`` during the post-respawn grace period., Load a font, exiting cleanly (no traceback) if the file is missing., Record the last arrow key pressed as the WISHED direction.          The turn its, Blit Pac-Man's sprite, or the full-screen Game Over text if dead., The player sprite: movement, animation, lives and the game-over screen.

### Community 16 - "Community 16"
Cohesion: 0.18
Nodes (7): Absolute-Timestamp Timers vs get_ticks, Pause Time-Shift Mechanism, App._resume, Slide every absolute deadline forward by ``delta`` ms (pause support)., Slide the respawn deadline forward by ``delta`` ms (pause support).          The, Fan the pause time-shift out to every ghost., Slide every absolute timer forward by ``delta`` ms (pause support).          The

### Community 17 - "Community 17"
Cohesion: 0.20
Nodes (9): Active-Cheat HUD Readout, HUD Reserved Top-Strip (no maze overlap), Config.level_max_time, _HUD_HEIGHT, GameDemo._draw_cheats, GameDemo._draw_hud, Surface, Draw the maze: solid fills, then carved channels for the tube look.          The (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.20
Nodes (6): Cell, Surface, Draw every remaining pac-gum (sprite, or a circle fallback)., Place a pac-gum in every corridor (bar the player's start cell).          Four c, Load and scale an asset, or return ``None`` if it is missing., Eat and remove the pac-gum at ``cell_pos``.          Returns:             ``"PAC

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (8): Action-String Return Protocol, Pause Frozen-Frame Snapshot, Pre-Rendered Two-State Button, App._enter_pause, _Button, PauseMenu, Task 8.4: the translucent pause overlay with Resume / Main Menu., Show a hand cursor while over any button.

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (6): Main Menu Top-Scores Preview, Config, Open a fullscreen window and build the entry (main menu) screen., MainMenu, Show a hand cursor while over any button (Task 8.2 hover effect)., Task 8.2: four buttons plus a live preview of the top scores.

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (5): Build one level (maze, player, pac-gums, ghosts). Return success.          Calle, Reset positions after a ghost death WITHOUT rebuilding the maze.          Unlike, Advance the game one frame; return ``True`` when it should end., GhostManager, Owns all four ghosts and fans one update/draw call out to each.

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (5): pac-man.py launcher, The single ``GameState``-driven main loop for the whole game (Task 8.1).  One :c, Build and run the whole game - the entry point ``pac-man.py`` calls., run_game(), The single source of truth for which screen is currently active.  The main loop

### Community 23 - "Community 23"
Cohesion: 0.29
Nodes (4): Event, Apply any cheat key, then forward the event to the player.          The cheat ke, Map a pressed key to its cheat (toggle, one-shot, or ignore)., Jump to the next level (or win, if already on the last one).          Mirrors th

### Community 24 - "Community 24"
Cohesion: 0.33
Nodes (4): Surface, Load and scale the three mouth frames, or a circle fallback., Place Pac-Man at the maze centre with a brief invincibility window.          The, Build the player inside the maze and spawn it at the centre.

### Community 25 - "Community 25"
Cohesion: 0.50
Nodes (4): Blue Pac-Man Sprite with Cigarette, Cigarette Detail, Pac-Man Player Character, Pixel Art Sprite Style

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (3): Ghost Frightened/Vulnerable State, Pac-Man Ghost Enemy Character, Pac-Man Ghost Sprite (White Body, Blue Eyes)

### Community 27 - "Community 27"
Cohesion: 0.67
Nodes (3): Pixel-Art Cigarette Sprite, Pac-Man Collectible Item, PacMan42 Game Project

### Community 28 - "Community 28"
Cohesion: 0.67
Nodes (3): Blue Pac-Man Sprite, Cigarette Detail, Player Character

### Community 29 - "Community 29"
Cohesion: 0.67
Nodes (3): Pixel-Art Cigarette Pack Sprite, Collectible Power-Up Item Role, Super Pacgum / Power Pellet Equivalent

## Ambiguous Edges - Review These
- `Pac-Man Ghost Sprite (White Body, Blue Eyes)` → `Ghost Frightened/Vulnerable State`  [AMBIGUOUS]
  C:/Users/keidi/OneDrive/PacMan42/assets/images/Screenshot_From_2026-07-10_12-31-49-removebg-preview.png · relation: conceptually_related_to
- `Pixel-Art Cigarette Pack Sprite` → `Super Pacgum / Power Pellet Equivalent`  [AMBIGUOUS]
  C:/Users/keidi/OneDrive/PacMan42/assets/images/Screenshot_From_2026-07-10_12-32-10-removebg-preview.png · relation: conceptually_related_to

## Knowledge Gaps
- **63 isolated node(s):** `Font`, `Event`, `Color`, `Surface`, `Mouth animation frame timing` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Pac-Man Ghost Sprite (White Body, Blue Eyes)` and `Ghost Frightened/Vulnerable State`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Pixel-Art Cigarette Pack Sprite` and `Super Pacgum / Power Pellet Equivalent`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GameDemo` connect `Community 10` to `Community 5`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 12`, `Community 15`, `Community 16`, `Community 17`, `Community 20`, `Community 21`, `Community 22`, `Community 23`?**
  _High betweenness centrality (0.259) - this node is a cross-community bridge._
- **Why does `Config` connect `Community 9` to `Community 1`, `Community 2`, `Community 7`, `Community 8`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 19`, `Community 20`, `Community 22`, `Community 23`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **Why does `Player` connect `Community 15` to `Community 0`, `Community 5`, `Community 9`, `Community 10`, `Community 12`, `Community 16`, `Community 21`, `Community 23`, `Community 24`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `GameDemo` (e.g. with `App` and `Config`) actually correct?**
  _`GameDemo` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `Config` (e.g. with `App` and `Config`) actually correct?**
  _`Config` has 18 INFERRED edges - model-reasoned connections that need verification._