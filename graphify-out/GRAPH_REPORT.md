# Graph Report - .  (2026-07-14)

## Corpus Check
- 1 files · ~46,820 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 116 nodes · 164 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 90% EXTRACTED · 9% INFERRED · 1% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Design Concepts & Docs|Design Concepts & Docs]]
- [[_COMMUNITY_Maze Encoding & Loading|Maze Encoding & Loading]]
- [[_COMMUNITY_Game Loop & Menu UI|Game Loop & Menu UI]]
- [[_COMMUNITY_Maze Generation Algorithm|Maze Generation Algorithm]]
- [[_COMMUNITY_Config & Entry Point|Config & Entry Point]]
- [[_COMMUNITY_Game State Machine|Game State Machine]]
- [[_COMMUNITY_Player Entity|Player Entity]]
- [[_COMMUNITY_Shared Movement & Ghosts|Shared Movement & Ghosts]]
- [[_COMMUNITY_Power-Up Sprite Assets|Power-Up Sprite Assets]]
- [[_COMMUNITY_Player Sprite Assets|Player Sprite Assets]]
- [[_COMMUNITY_Ghost Sprite Assets|Ghost Sprite Assets]]
- [[_COMMUNITY_Player Sprite (variant)|Player Sprite (variant)]]
- [[_COMMUNITY_Player Sprite (variant 2)|Player Sprite (variant 2)]]

## God Nodes (most connected - your core abstractions)
1. `MazeGenerator` - 16 edges
2. `GameDemo` - 13 edges
3. `Player` - 13 edges
4. `GameState` - 9 edges
5. `MazeLoader` - 9 edges
6. `PacgumManager` - 9 edges
7. `run_main_menu()` - 5 edges
8. `ImageElement` - 5 edges
9. `get_layout geometry source of truth` - 5 edges
10. `Config` - 4 edges

## Surprising Connections (you probably didn't know these)
- `HowEverythingWorks build guide` --semantically_similar_to--> `get_layout geometry source of truth`  [INFERRED] [semantically similar]
  HowEverythingWorks.md → Maze_Code_Reference.md
- `ImageElement class` --references--> `Pygame dependency`  [INFERRED]
  pacman_images.py → requirements.txt
- `PacMan42 README` --cites--> `42 PacMan subject PDF`  [INFERRED]
  README.md → en.subject (2).pdf
- `MazeLoader` --uses--> `MazeGenerator`  [INFERRED]
  src/maze_loader.py → mazegenerator-00001-py3-none-any/mazegenerator/mazegenerator.py
- `HowEverythingWorks build guide` --references--> `ImageElement class`  [EXTRACTED]
  HowEverythingWorks.md → pacman_images.py

## Import Cycles
- None detected.

## Communities (14 total, 6 thin omitted)

### Community 0 - "Design Concepts & Docs"
Cohesion: 0.15
Nodes (15): 42 PacMan subject PDF, HowEverythingWorks build guide, Mouth animation frame timing, ImageElement class, main_menu_UI entry point, get_layout geometry source of truth, Cell-snapped movement, fright_until edible-ghost timer (+7 more)

### Community 1 - "Maze Encoding & Loading"
Cohesion: 0.21
Nodes (7): Wall bitmask encoding 1-2-4-8, FT_WALL hidden 42 logo, Number maze grid of ints, Tile maze WALL CORRIDOR grid, mazegenerator package top_level.txt, Unwinnable-levels pacgum-in-42 bug, MazeLoader

### Community 4 - "Config & Entry Point"
Cohesion: 0.26
Nodes (4): Config, load_path(), run_main_menu(), ImageElement

### Community 8 - "Power-Up Sprite Assets"
Cohesion: 0.40
Nodes (5): Pixel-Art Cigarette Sprite, Pac-Man Collectible Item, PacMan42 Game Project, Collectible Power-Up Item Role, Super Pacgum / Power Pellet Equivalent

### Community 9 - "Player Sprite Assets"
Cohesion: 0.50
Nodes (4): Blue Pac-Man Sprite with Cigarette, Cigarette Detail, Pac-Man Player Character, Pixel Art Sprite Style

### Community 10 - "Ghost Sprite Assets"
Cohesion: 0.67
Nodes (3): Ghost Frightened/Vulnerable State, Pac-Man Ghost Enemy Character, Pac-Man Ghost Sprite (White Body, Blue Eyes)

### Community 11 - "Player Sprite (variant)"
Cohesion: 0.67
Nodes (3): Blue Pac-Man Sprite, Cigarette Detail, Player Character

## Ambiguous Edges - Review These
- `Pixel-Art Cigarette Sprite` → `Super Pacgum / Power Pellet Equivalent`  [AMBIGUOUS]
  assets/images/Screenshot_From_2026-07-10_12-32-10-removebg-preview.png · relation: conceptually_related_to
- `Pac-Man Ghost Sprite (White Body, Blue Eyes)` → `Ghost Frightened/Vulnerable State`  [AMBIGUOUS]
  assets/images/Screenshot_From_2026-07-10_12-31-49-removebg-preview.png · relation: conceptually_related_to

## Knowledge Gaps
- **16 isolated node(s):** `Grid vs pixel coordinate systems`, `Mouth animation frame timing`, `mazegenerator package top_level.txt`, `Pac-Man Collectible Item`, `PacMan42 Game Project` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Pixel-Art Cigarette Sprite` and `Super Pacgum / Power Pellet Equivalent`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Pac-Man Ghost Sprite (White Body, Blue Eyes)` and `Ghost Frightened/Vulnerable State`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `MazeLoader` connect `Maze Encoding & Loading` to `Design Concepts & Docs`, `Game Loop & Menu UI`, `Maze Generation Algorithm`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `MazeGenerator` connect `Maze Generation Algorithm` to `Maze Encoding & Loading`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `GameDemo` connect `Game Loop & Menu UI` to `Design Concepts & Docs`, `Maze Encoding & Loading`, `Config & Entry Point`, `Player Entity`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `GameDemo` (e.g. with `MazeLoader` and `PacgumManager`) actually correct?**
  _`GameDemo` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `MazeLoader` (e.g. with `GameDemo` and `MazeGenerator`) actually correct?**
  _`MazeLoader` has 2 INFERRED edges - model-reasoned connections that need verification._