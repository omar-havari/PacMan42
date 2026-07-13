# The Maze, Line by Line — Full Code Reference

This document walks every file, class, function and line involved in building
the maze, in the order they actually run, and says exactly what each one
contributes. Three files are involved:

| File | Role |
|---|---|
| `venv/Lib/site-packages/mazegenerator/mazegenerator.py` | 3rd-party library. Produces the small **number** maze. |
| `src/maze_loader.py` | Our code. Converts numbers → the big **tile** maze, and draws it. |
| `src/GameDemo.py` | Our code. Decides *when* to build a maze and hands the result to the player/pacgums. |

Everything is triggered from one line, so start there.

---

## 1. The trigger — `src/GameDemo.py`

### Lines 16–17 — how big the maze is
```python
MAZE_WIDTH = 15
MAZE_HEIGHT = 15
```
Contribution: these two constants are the **only** place the maze's size is
decided. Change them and every downstream grid resizes automatically, because
nothing else hardcodes 15.

### Class `GameDemo`, `__init__` (line 24)
This class owns one level of the game: the maze, the player, the pacgums, the
score. Line 28 creates the tool that will build mazes:
```python
self.maze = MazeLoader()
```
It doesn't build anything yet — `MazeLoader` is just instantiated, empty.
Line 47 is what actually kicks off the first maze:
```python
self.failed = not self._start_level()
```

### Method `_start_level` (line 59) — "build one level"
This is the method that actually calls the maze pipeline. Line by line:

```python
if self.level == 1:
    seed = self.config.seed          # line 63: level 1 uses the FIXED seed
else:
    seed = random.randrange(1_000_000)  # line 65: later levels get a random seed
```
Contribution: decides *which* maze you get. The seed is the only source of
randomness for the whole maze — same seed, same maze, always. Level 1 is
reproducible on purpose (per the project's spec); every level after that is
different each time you play.

```python
self.grid = self.maze.generate(MAZE_WIDTH, MAZE_HEIGHT, seed)   # line 67
```
Contribution: **this is the call that builds the entire maze.** Everything in
sections 2 and 3 below runs because of this one line. The return value —
the finished 31×31 tile grid — is stored as `self.grid`, which every other
system (drawing, movement, pacgum placement) reads from now on.

```python
if self.grid is None:                # line 68
    print("Error: could not generate the maze, returning to menu.")
    return False
```
Contribution: safety net. `MazeLoader.generate` returns `None` if the library
throws (see section 2), so the game can bail out to the menu instead of
crashing.

```python
cell, offset_x, offset_y = self.maze.get_layout(self.screen, self.grid)  # line 73
```
Contribution: now that the grid exists, figure out how large one tile should
be drawn and where the grid should sit on screen (see section 3.2). This
doesn't touch the grid's contents — only how it will be rendered/positioned.

```python
self.player = Player(self.screen, lives, self.grid, cell, offset_x, offset_y)   # line 82
self.pacgums = PacgumManager(
    self.grid, self.player.current_cell(), cell, offset_x, offset_y
)                                                                                 # line 83-85
```
Contribution: the finished grid is handed to the player (for collision — it
can only move onto `"CORRIDOR"` tiles) and to the pacgum manager (which scans
the grid and drops a dot on every `"CORRIDOR"` tile). Neither of these
*builds* the maze; they just consume the grid `_start_level` already built.

### `draw` (line 130), specifically line 144
```python
self.maze.draw(self.screen, self.grid)
```
Contribution: every frame, ask `MazeLoader` to paint the current grid. This
does not rebuild anything — `self.grid` only changes when `_start_level` runs
again (i.e. a new level starts).

---

## 2. The number maze — `mazegenerator.py`

### Class `MazeGenerator` (line 6)
Represents one generated maze as a grid of numbers, stored in `self._maze`.

### `__init__` (line 8)
```python
self._width = size[0]; self._height = size[1]         # lines 12-13
self._entryx, self._entryy = ...                        # lines 16-19: where carving starts
self._exitx, self._exity = ...                          # lines 20-23: where the exit is
self._maze: list[list[int]] = []                        # line 24: will hold the numbers
self.generate(self._seed)                                # line 27: build it right away
```
Contribution: `MazeLoader.generate` (section 3) calls `MazeGenerator(size=(width,height), seed=seed)` — this constructor stores the settings and *immediately* builds the maze by calling `self.generate()`. By the time the constructor returns, `self._maze` is already the finished number grid.

### `maze` property (line 30-32)
```python
@property
def maze(self) -> list[list[int]]:
    return self._maze
```
Contribution: this is how `MazeLoader` reads the result out — `maze.maze` in
`src/maze_loader.py:25`.

### `generate` (line 46) — the 4-step recipe
```python
def generate(self, seed: int = 0) -> None:
    random.seed(seed) if seed > 0 else random.seed()   # line 47
    self._create_empty_maze()                            # line 49  → step A
    self._add_42_to_maze()                                # line 50  → step B
    self._generate_maze(self._entryx, self._entryy, 0)    # line 51  → step C
    self._find_short_path()                               # line 52  → step D (unused by us)
```
Contribution: `random.seed(seed)` (line 47) is what makes the "randomness"
repeatable — every call to `random.shuffle`/`random.randint` later in the
pipeline draws from this seeded sequence, so the same seed always reproduces
the same maze bit-for-bit. The four calls below it are the whole build,
each explained next. (Step D, `_find_short_path`, computes a solver path the
game never uses — irrelevant to how the maze looks.)

### Step A — `_create_empty_maze` (line 56)
```python
self._maze = [[8] + [0] * (self._width-2) + [2] for _ in range(self._height-2)]  # line 57-58
self._maze.insert(0, [9] + [1] * (self._width-2) + [3])                          # line 59
self._maze.append([12] + [4] * (self._width-2) + [6])                            # line 60
self._path = [[0] * self._width for _ in range(self._height)]                    # line 61
```
Contribution: builds the starting grid before any carving happens.
- Line 57-58: every **inner row** — left cell gets `8` (West wall, since it's
  the leftmost column), right cell gets `2` (East wall), everything between
  is `0` (fully open, no walls yet).
- Line 59: the **top row** is inserted — its left/right corners get `9`
  (North+West) and `3` (North+East), the cells between get `1` (North wall).
- Line 60: the **bottom row** is appended — corners `12` (South+West) and `6`
  (South+East), the rest `4` (South wall).
- Line 61: `_path` is a separate same-size grid of all `0`s — this is a
  "have I visited this cell yet" tracker, not part of the maze's walls.

Net effect: a completely open room whose only walls are the outer fence.
Every non-zero number you'll see later got added on top of this by steps B/C.

### Step B — `_add_42_to_maze` (line 63)
```python
ft_small = [[1,0,0,0,1,1,1], [1,0,0,0,0,0,1], ...]     # lines 64-69: the "42" pixel art (5 rows x 7 cols)

if len(ft_small)*2 > self._height or len(ft_small[0])*2 > self._width:  # line 70
    print("MazeGenerator Warning: maze is too small to add '42' in it")
    return                                                               # line 72
```
Contribution: `ft_small` is a hand-drawn bitmap — a `1` means "this pixel is
part of the 42". Line 70 is a size guard: it needs at least 10 rows and 14
columns of breathing room, otherwise it gives up entirely (this is why our
earlier 3×3/5×5 examples never had a 42 — they printed this exact warning).

```python
posy = int((self._height - len(ft_small)) / 2)     # line 73
posx = int((self._width - len(ft_small[0])) / 2)    # line 74
for y in range(len(ft_small)):
    for x in range(len(ft_small[0])):
        if ft_small[y][x] == 1:                      # line 77
            self._maze[posy+y][posx+x] = 15           # line 78
            self._maze[posy+y][posx+x-1] |= 2          # line 79
            self._maze[posy+y][posx+x+1] |= 8          # line 80
            self._maze[posy+y-1][posx+x] |= 4          # line 81
            self._maze[posy+y+1][posx+x] |= 1          # line 82
            self._path[posy+y][posx+x] = 1              # line 83
```
Contribution: `posy`/`posx` (lines 73-74) centre the 5×7 bitmap in the maze.
For every pixel that's a `1`:
- line 78: that cell's number is **overwritten** to `15` — walled on all 4
  sides, unconditionally, regardless of what it was before.
- lines 79-82: the four **neighbouring** cells each get one wall bit
  OR'd in (`|=`) toward the 42-cell — so a normal corridor cell sitting next
  to the 42 gets sealed on that one side, even though it's a regular cell
  everywhere else. This is what makes the 42 unreachable rather than just
  present.
- line 83: marks the cell as "already visited" in `_path`, so step C's random
  walk will never step into it and undo the sealing.

### Step C — `_generate_maze` (line 114) — the actual carving
```python
def _generate_maze(self, x, y, from_code):
    self._path[y][x] = 1                          # line 115: mark visited
    non_mutable = self._maze[y][x]                 # line 116: remember original walls
    self._maze[y][x] = 15 & ~from_code              # line 117: seal all 4 sides, except the one we entered through
    for nx, ny, code, opp_code in self._get_neighbors(x, y):   # line 118
        if code & non_mutable:                      # line 119: was this side an outer-border wall?
            continue                                 # line 120: never carve through the border
        self._maze[y][x] = self._maze[y][x] & (~code)   # line 121: open this side of the current cell
        self._generate_maze(nx, ny, opp_code)             # line 122: recurse into the neighbour
```
Contribution: this is a **recursive random walk** starting at the entry
cell (`self._entryx, self._entryy`, from `GameDemo`'s `entry_cell=(0,0)`
passed into `MazeGenerator`). Each call: seals the current cell on all sides
(line 117) except the direction it just arrived from, then asks
`_get_neighbors` (below) for a randomized list of directions to try, and for
each one that's carve-able, knocks the wall down on **both** the current cell
and the neighbour (line 121, and the neighbour's own wall is cleared when
its own recursive call runs line 117/121), then recurses into it.
`non_mutable` (line 116) protects the maze's outer fence — a side that was
already a border wall before this cell was touched is never carved through.

### `_get_neighbors` (line 93) — picking directions
```python
directions = [(1,0,2,8), (-1,0,8,2), (0,1,4,1), (0,-1,1,4)]   # line 95: (dx,dy,wall-code,opposite-code)
random.shuffle(directions)                                      # line 96: THIS is the "randomness" in random maze
for dw, dh, code, opp_code in directions:
    nx, ny = x + dw, y + dh
    if self._is_available(nx, ny):                              # line 99: unvisited & in bounds?
        yield nx, ny, code, opp_code                              # line 100: offer it as a normal path
    else:
        if (self._perfect is False and random.randint(0,5) == 0   # lines 102-105
            and 0 <= ny < self._height and 0 <= nx < self._width):
            if (self._maze[ny][nx] != 15 and ...):                 # lines 106-110: guard against the 42 & border
                self._maze[y][x] = self._maze[y][x] & (~code)       # line 111
                self._maze[ny][nx] = self._maze[ny][nx] & (~opp_code)  # line 112
```
Contribution: line 96 (`random.shuffle`) is *the* single line that makes each
seed produce a different-looking maze — it randomizes the order the walk
explores North/South/East/West. Lines 99-100 hand back cells that haven't
been visited yet, which is how the main spanning-tree corridors get carved by
`_generate_maze`. Lines 102-112 are a bonus: a `perfect=False` maze (which is
what `MazeLoader` always requests, line 10 of `maze_loader.py`) has a 1-in-6
chance of also knocking down a wall toward an **already-visited** neighbour
— this is what creates loops/multiple paths instead of one single dead-end
labyrinth. Line 107 (`!= 15`) is another guard that refuses to punch a loop
wall into a 42-cell.

### `_find_short_path` (line 124)
Solves the maze from entry to exit with a breadth-first search and stores the
solution string. **Not used anywhere in `MazeLoader` or `GameDemo`** — dead
weight for our purposes, included only because it's part of the library. It
does not affect what the maze looks like.

---

## 3. The tile maze — `src/maze_loader.py`

### Class `MazeLoader` (line 3)
Owns two jobs, one per public method: **build** the tile grid (`generate`)
and **draw** it (`draw`, using `get_layout` for positioning).

### `generate` (line 6) — building the tile grid

```python
def generate(self, width, height, seed) -> list[list[str]] | None:
    extended_maze = [["WALL" for _ in range(width*2+1)] for _ in range(height*2+1)]  # line 7
```
Contribution: allocates the **entire output grid up front**, `(2·width+1) ×
(2·height+1)` tiles, every single one initialized to `"WALL"`. This is why
"filling in `#`" later is really "everything is already `#`; some tiles get
overwritten to `.`". The `*2+1` is explained in full in
`Maze_Build_Phases.md` Part 3 — short version: 1 tile per cell + 1 gap tile
between each pair of cells + 1 border tile, per axis.

```python
    try:
        maze = MazeGenerator(size=(width, height), perfect=False,
                              entry_cell=(0, 0), exit_cell=(-1, -1), seed=seed)  # line 10
    except Exception as e:
        print(f"Error generating maze: {e}")   # line 12
        return None                              # line 13
```
Contribution: calls into section 2 to get the number maze. `perfect=False` is
what turns on the loop-carving behaviour described above (`_get_neighbors`
lines 102-112) — without it the maze would be a "perfect" maze (exactly one
path between any two points, no loops). The `try/except` means if the
library ever throws, `MazeLoader.generate` returns `None` instead of
crashing — which is exactly the `None` that `GameDemo._start_level` line 68
checks for.

```python
    cells = maze.maze                       # line 25
    for i, row in enumerate(cells):          # line 26: i = which row of NUMBERS
        for j, cell in enumerate(row):       # line 27: j = which column, cell = the number itself
```
Contribution: pulls the finished number grid out via the `maze` property
(section 2) and starts walking it one cell at a time. `i`/`j` here are
**small-grid** coordinates — everything below converts them to **big-grid**
coordinates.

```python
            if cell == 15:                                             # line 28
                extended_maze[i*2+1][j*2+1] = "FT_WALL"                # line 29
                if j + 1 < len(row) and row[j + 1] == 15:               # line 33
                    extended_maze[i*2+1][j*2+2] = "FT_WALL"              # line 34
                if i + 1 < len(cells) and cells[i + 1][j] == 15:         # line 35
                    extended_maze[i*2+2][j*2+1] = "FT_WALL"              # line 36
                continue                                                  # line 37
```
Contribution: the special case for the "42" (built in section 2, step B).
Line 28 catches any cell that's still `15` (never opened by the carving, per
the sealing in `_add_42_to_maze`). Line 29 marks its own tile `FT_WALL`
instead of `CORRIDOR`. Lines 33-36 check the cell **immediately to the right**
and **immediately below** — if either is *also* `15`, the gap tile between
them is painted `FT_WALL` too, so two adjacent 42-cells render as one
connected magenta stroke instead of two separate dots. Line 37 (`continue`)
skips the normal corridor logic below entirely for these cells — a 42-cell
never becomes walkable.

```python
            extended_maze[i*2+1][j*2+1] = "CORRIDOR"    # line 38: open the room itself
            if cell & 1 == 0:                              # line 39: no North wall?
                extended_maze[i*2][j*2+1] = "CORRIDOR"      # line 40: open the gap above
            if cell & 2 == 0:                              # line 41: no East wall?
                extended_maze[i*2+1][j*2+2] = "CORRIDOR"     # line 42: open the gap to the right
            if cell & 4 == 0:                              # line 43: no South wall?
                extended_maze[i*2+2][j*2+1] = "CORRIDOR"     # line 44: open the gap below
            if cell & 8 == 0:                              # line 45: no West wall?
                extended_maze[i*2+1][j*2] = "CORRIDOR"       # line 46: open the gap to the left
    return extended_maze                                    # line 47
```
Contribution: this is the whole "fill it in" step. Line 38 always opens the
room's own tile — a normal cell is always walkable at its centre. Lines
39-46 are four independent checks, one per compass direction: `cell & 1`
etc. reads one bit out of the packed number (see `Maze_Build_Phases.md` Part
1 for the bit math); if that wall is **absent**, the one gap tile on that
side is opened too. If the bit is present, nothing happens and that tile
keeps the `"WALL"` it was given on line 7. Line 47 hands the finished 31×31
(for a 15×15 input) grid of strings back to `GameDemo._start_level` (line 67
above), where it becomes `self.grid`.

### `get_layout` (line 61) — where the grid sits on screen
```python
def get_layout(self, screen, grid):
    rows = len(grid); cols = len(grid[0])                      # lines 62-63
    screen_width = screen.get_width(); screen_height = screen.get_height()  # lines 64-65
    cell = min(screen_width // cols, screen_height // rows)     # line 68
    offset_x = (screen_width - cell * cols) // 2                # line 69
    offset_y = (screen_height - cell * rows) // 2                # line 70
    return cell, offset_x, offset_y                               # line 71
```
Contribution: does **not** change the grid's contents at all — purely a
pixel-geometry calculation. Line 68 picks one square `cell` size that fits
both width and height of the window (whichever is tighter), so tiles are
never stretched. Lines 69-70 compute the leftover space and split it evenly
on both sides so the maze is centred (a "letterbox"). This single method is
called by `GameDemo`, `Player`, and `PacgumManager` alike, which is exactly
why the maze, the walls Pac-Man collides with, and the dots he eats can never
drift out of alignment with each other.

### `draw` (line 73) — turning the grid into pixels
```python
def draw(self, screen, grid):
    rows = len(grid); cols = len(grid[0])                # lines 74-75
    cell, offset_x, offset_y = self.get_layout(screen, grid)   # line 76
    border = max(2, cell // 4)                              # line 79: thickness of the blue outline
    screen.fill(self.BG_COLOR)                               # line 81: black background first

    def is_wall(r, c):                                        # line 83
        return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "WALL"
```
Contribution: no grid mutation happens anywhere in `draw` — it only *reads*
`grid`. `is_wall` (line 83-84) is a small helper used below to check a
neighbour safely (returns `False` for anything off the edge of the grid).

**Pass 1 — solid fill (lines 90-97):**
```python
for r in range(rows):
    for c in range(cols):
        x = offset_x + c * cell; y = offset_y + r * cell   # lines 92-93: pixel position of this tile
        if grid[r][c] == "FT_WALL":
            pygame.draw.rect(screen, self.FT_COLOR, (x, y, cell, cell))   # line 95: solid magenta square
        elif grid[r][c] == "WALL":
            pygame.draw.rect(screen, self.WALL_COLOR, (x, y, cell, cell))  # line 97: solid blue square
```
Contribution: every `WALL` tile becomes a solid blue square, every `FT_WALL`
a solid magenta square. `CORRIDOR` tiles are not drawn at all — the black
fill from line 81 shows through, which is the corridor colour.

**Pass 2 — carve the outline (lines 102-121):**
```python
for r in range(rows):
    for c in range(cols):
        if grid[r][c] != "WALL":
            continue                                          # line 105: only re-touch WALL tiles (not FT_WALL)
        x = offset_x + c * cell; y = offset_y + r * cell
        ix, iy = x + border, y + border                        # line 108: shrink the black cut-out inward by `border`
        iw = ih = cell - 2 * border                              # line 109
        if is_wall(r, c - 1): ix -= border; iw += border           # lines 110-112: extend left if that neighbour is a wall too
        if is_wall(r, c + 1): iw += border                          # lines 113-114: extend right
        if is_wall(r - 1, c): iy -= border; ih += border            # lines 115-117: extend up
        if is_wall(r + 1, c): ih += border                          # lines 118-119: extend down
        if iw > 0 and ih > 0:
            pygame.draw.rect(screen, self.BG_COLOR, (ix, iy, iw, ih))  # line 121: cut a black rectangle out of the middle
```
Contribution: takes each solid blue square from pass 1 and cuts a black
rectangle out of its middle, leaving only a thin border of blue around the
edge — the classic Pac-Man "tube" look, rather than a chunky blue brick.
Lines 110-119 are what make adjacent wall tiles' black cut-outs *join up*
into one continuous channel instead of leaving a blue seam between every
pair of neighbouring wall tiles. `FT_WALL` tiles are skipped entirely (line
105 only matches `"WALL"`), which is why the "42" renders as a solid filled
shape instead of an outline.

---

## 4. Downstream consumers (build on top, don't build the maze)

These don't construct the maze, but show why the tile-vs-number split from
section 3 matters — everything after `generate()` returns only ever reads
`self.grid`, never the original numbers.

- **`Player`** (`src/Player.py`) checks `grid[row][col] == "CORRIDOR"` before
  letting Pac-Man move into a tile — same string comparison as `draw`'s
  wall check, just used for collision instead of colour.
- **`PacgumManager.__init__`** (`src/pacgums.py:30-33`) loops over every
  `(r, c)` in the grid and drops a `"PACGUM"` on each `"CORRIDOR"` tile
  (skipping the player's starting cell), then overwrites four known corner
  cells to `"SUPER"` (`src/pacgums.py:39-47`) — corners it can find without
  searching, because section 3 guarantees room-centre tiles always sit at odd
  row/column indices.

---

## Summary: one call, three layers

```
GameDemo._start_level()                         line 67
        │  self.maze.generate(15, 15, seed)
        ▼
MazeLoader.generate()                            maze_loader.py:6
        │  MazeGenerator(size=(15,15), seed=seed)
        ▼
MazeGenerator.__init__() → .generate()            mazegenerator.py:8,46
        │  _create_empty_maze() → _add_42_to_maze() → _generate_maze()
        ▼
   15x15 grid of NUMBERS  (walls packed as bits)
        │
        │  (back up to MazeLoader.generate, lines 25-46)
        ▼
   31x31 grid of WORDS  ("WALL" / "CORRIDOR" / "FT_WALL")
        │
        ├─► GameDemo.draw() → MazeLoader.draw()      paints pixels
        ├─► Player                                    collision checks
        └─► PacgumManager                              dot placement
```
