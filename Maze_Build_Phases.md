# How the Maze Gets Built — The Simple Version

There are **two mazes** in this game, and the whole trick is converting one into the other:

1. **The small number maze** — made by the `mazegenerator` library. It's tiny (15×15) and each square holds just a *number*.
2. **The big tile maze** — made by our `MazeLoader` (`src/maze_loader.py`). It's bigger (31×31) and each square holds a *word*: `"WALL"` or `"CORRIDOR"` (or `"FT_WALL"` for the 42).

The game only ever plays on the big one. The small one is just the recipe.

To keep every example small enough to check by eye, this whole document uses a
**3×3** maze (`seed=2`) instead of 15×15. The real game does *exactly* the same
thing, just with more cells. All grids below are real output from this
project's code.

---

## Part 1 — What the numbers mean (the "bitmask")

Forget the word bitmask for a second. Picture one square room. A room can have
a wall on each of its 4 sides. Each side has a price tag:

```
          North = 1
        ┌─────────┐
        │         │
West =8 │  room   │ East = 2
        │         │
        └─────────┘
          South = 4
```

**The number stored in a cell is just the prices of its walls added up.**

- A room with a North wall and a West wall stores `1 + 8 = 9`
- A room with walls on all four sides stores `1 + 2 + 4 + 8 = 15`
- A room with no walls at all stores `0`

Why 1, 2, 4, 8 and not 1, 2, 3, 4? Because with 1/2/4/8 every total is
**unique** — there is only one way to make 9 (it must be 8+1, so it must be
West+North). With 1/2/3/4 the total 4 could mean "South wall" or "North+East",
and you couldn't tell them apart.

Going backwards (number → walls) is the same trick as making change with coins
of 8, 4, 2, 1:

```
value 13:  13 - 8 = 5   → has a West wall
            5 - 4 = 1   → has a South wall
            1 - 1 = 0   → has a North wall     (no 2 left → East is OPEN)
```

That's all "bitmask" means: one number that packs 4 yes/no answers.
In code, "does the number contain the 4?" is written `cell & 4 != 0` —
same question, computer notation.

## Part 2 — The small number maze

Ask the library for a 3×3 maze with seed 2 and it hands back 9 numbers:

```
 9  5  3
12  1  2
13  4  6
```

How it made them (inside `mazegenerator.py`):

1. **Start**: all inner cells are `0` (no walls); the outer ring starts with
   its outside-facing walls already priced in — top-left is `9` (North+West),
   the top edge is `1` (North), and so on. So at first the maze is one big
   open room with a fence around it.
2. **Carve**: a random walk (driven by your seed — same seed, same maze every
   time) wanders from cell to cell *adding* interior walls in a way that
   leaves winding corridors. When it decides two neighbours are separated, it
   adds the matching price on *both* sides: the left cell gets `+2` (East
   wall), the right cell gets `+8` (West wall). That's why neighbours never
   disagree about the wall between them.
3. *(15×15 only)* Before carving, it stamps a "42" of value-`15` cells into
   the middle — more on that in Part 5. A 3×3 is too small, so here it's
   skipped.

Now read our 9 numbers like price tags:

```
 9 = 8+1    walls: N W      open: E S
 5 = 4+1    walls: N S      open: E W
 3 = 2+1    walls: N E      open: S W
12 = 8+4    walls: S W      open: N E
 1 = 1      walls: N        open: E S W
 2 = 2      walls: E        open: N S W
13 = 8+4+1  walls: N S W    open: E
 4 = 4      walls: S        open: N E W
 6 = 4+2    walls: E S      open: N W
```

Notice the problem: these walls are **lines between rooms — they have no
thickness**. Pac-Man can't bump into a line, and you can't draw a line as a
blue block. We need walls that are squares of their own. That's the conversion.

## Part 3 — The multiplication: 3×3 → 7×7 (literally where `*2+1` happens)

The fix: give every wall its own square. Between any two rooms, insert one
extra square that will be either solid (wall there) or open (no wall there).
Then wrap a border of solid squares around everything.

Count along one row and you see where the sizes come from:

```
   border  room  gap  room  gap  room  border
     #      c0    ?    c1    ?    c2     #
     0      1     2    3     4    5      6      ← tile index
```

3 rooms + 2 gaps between them + 2 border squares = **7**. In general:
`n` rooms → `2n + 1` tiles. That is this single line, `src/maze_loader.py:7`:

```python
extended_maze = [["WALL" for _ in range(width*2+1)] for _ in range(height*2+1)]
```

This is the only "multiplication" in the whole conversion — it just allocates
the bigger grid. And look at the tile indices above: room `j` landed on tile
`2j+1` (room 0 → tile 1, room 1 → tile 3, room 2 → tile 5). The `*2` is
"skip a gap square per room", the `+1` is "skip the border square at the
start". Same for rows. So:

> **room (i, j) lives at tile (2i+1, 2j+1), and its four neighbours-gaps are
> the tiles directly above/below/left/right of that.**

One more thing this buys us for free: room tiles always have **odd** indices,
gap tiles have one odd + one even index, and tiles with two even indices
(the corner posts where 4 rooms meet) belong to nobody.

## Part 4 — Filling in the big grid, cell by cell

Rules (the loop at `src/maze_loader.py:26-46`):

- The big grid **starts 100% `"WALL"`**. We never add walls — we only punch
  holes. Anything we don't touch stays a wall.
- For each room: open its own tile (rooms are always walkable).
- For each side whose price is *missing* from the number: also open the gap
  tile on that side.
- Sides whose price *is* in the number: do nothing (the gap stays a wall).

(The `#` and `.` below are just how we print it — the grid really contains
the strings `"WALL"` and `"CORRIDOR"`.)

**Start** — 7×7, all wall:

```
#######
#######
#######
#######
#######
#######
#######
```

**Room (0,0), number 9 = 8+1** → walls N,W / open E,S. Its tile is
(2·0+1, 2·0+1) = (1,1).

```
#######      opened (1,1)  its own tile
#..####      opened (1,2)  gap to the East  (no 2 in the number)
#.#####      opened (2,1)  gap to the South (no 4 in the number)
#######      NOT (0,1)/(1,0): North & West gaps stay walls (1 and 8 present)
#######
#######
#######
```

**Room (0,1), number 5 = 4+1** → walls N,S / open E,W. Tile (1,3).

```
#######
#.....#   ← opened (1,3) itself, (1,4) East gap, (1,2) West gap
#.#####     (1,2) was ALREADY open — room (0,0) opened it from its side.
#######     Both rooms agree (the generator guarantees it), so no conflict.
#######
#######
#######
```

**Room (0,2), number 3 = 2+1** → walls N,E / open S,W. Tile (1,5). Opens
itself, its West gap (already open) and its South gap (2,5):

```
#######
#.....#
#.###.#
#######
#######
#######
#######
```

**Row 1 of rooms.** Room (1,0)=12 → open N,E: opens (3,1), the North gap
(2,1) (already open!), East gap (3,2). Room (1,1)=1 → open E,S,W: opens
(3,3), (3,4), (4,3), (3,2)(already). Room (1,2)=2 → open N,S,W: opens (3,5),
(2,5)(already), (4,5), (3,4)(already):

```
#######
#.....#
#.###.#
#.....#
###.#.#
#######
#######
```

Notice how a vertical passage forms: room (0,0) opened gap (2,1) "from
above" (its South side) and room (1,0) opened the same tile "from below"
(its North side). One shared gap tile, reachable from both formulas.

**Row 2 of rooms.** (2,0)=13 → open E only: opens (5,1),(5,2).
(2,1)=4 → open N,E,W: opens (5,3),(4,3)(already),(5,4),(5,2)(already).
(2,2)=6 → open N,W: opens (5,5),(4,5)(already),(5,4)(already). **Done:**

```
#######
#.....#
#.###.#
#.....#
###.#.#
#.....#
#######
```

Check what stayed `#` and why:

- the outer ring — the border rooms all had their outside prices set, so no
  hole was ever punched outward;
- (2,2), (2,4), (4,2), (4,4) — the corner posts (both indices even): **no
  formula can even produce those coordinates**, so they can never be opened;
- (2,3) — the gap between rooms (0,1) and (1,1): room (0,1) has the 4
  (South wall) and room (1,1) has the 1 (North wall), so neither side
  punched it.

That's the entire conversion. 9 numbers in, 49 words out, and every `#` is
either "a price said wall", "border", or "corner post nobody can touch".

## Part 5 — The real game: same thing, ×25 bigger, plus the "42"

The game requests 15×15 (`MAZE_WIDTH`/`MAZE_HEIGHT`, `src/GameDemo.py:16-17`)
→ tile grid 2·15+1 = **31×31**. Identical rules, plus **one** extra:

In a 15×15 there's room for the library to stamp a "42" into the middle
before carving: those cells get the number **15** — walled on all four sides,
so the random walk can never enter them, so they still say 15 when we get
them. Our loader treats 15 as a special marker (`src/maze_loader.py:28-37`):
instead of a corridor, the room tile becomes `"FT_WALL"` (drawn magenta, not
blue), and the gap between two neighbouring 15-cells becomes `"FT_WALL"` too,
so the digits are connected strokes instead of dotted. They block movement
just like walls (this also fixed a bug where pacgums used to spawn inside the
sealed 42, making levels unwinnable).

The result for seed 42 (`4` = `FT_WALL`):

```
###############################
#.#.....#...#...............#.#
#.#.###.#.#.#.#############.#.#
#.....#.......#.........#.....#
#.#.#.#.#.###.#.#.#.#.#.#.###.#
#.#.......#...#.....#...#.....#
#.#.#####.#.#.###.#.#.#.#####.#
#.#.........#...#...#.#.....#.#
#.###.###.#####.###.#.###.#.#.#
#.........#.....#.........#.#.#
###.###.###.#.#.#######.#.#.#.#
#...#...#4#.#...#44444#.#.#...#
#.#.#.###4#.#.#.#####4#.#.#.#.#
#.#.#...#4#...#.....#4#...#...#
#.#.#.#.#4#####.#####4###.#.###
#.#...#.#44444#.#44444#.#.....#
#.#.#.#.#####4#.#4#####.#.###.#
#.#.....#...#4#.#4#.....#.....#
#.#.###.#.#.#4#.#4#####.#####.#
#.....#.#.#.#4#.#44444#.......#
#.###.#.#.#.###.#######.#.###.#
#...#.#.........#.....#.......#
#.#.#########.#.###.#.#######.#
#...#.........#.....#.#.....#.#
#.###.###.###.#.#.#.###.###.#.#
#...#...#.....#...#.#.......#.#
#.#.###.###.#.#.#.#.#.###.#.#.#
#.#...#.......#.#...#...#.#.#.#
#.#.#####.#######.#.#.#.#.#.#.#
#.#...............#.....#.....#
###############################
```

This grid is `self.grid` in `GameDemo` and is the single source of truth from
here on: moving is allowed only onto `"CORRIDOR"` tiles, `PacgumManager` drops
a pacgum on every `"CORRIDOR"` tile, and `MazeLoader.draw` paints `"WALL"`
blue and `"FT_WALL"` magenta (then carves thin outlines out of the blue for
the classic Pac-Man look — drawing only, the grid never changes).

---

### Try it yourself

```python
from mazegenerator.mazegenerator import MazeGenerator
from src.maze_loader import MazeLoader

print(MazeGenerator(size=(3, 3), perfect=False, seed=2).maze)  # the 9 numbers
grid = MazeLoader().generate(3, 3, 2)                          # the 7x7 words
for row in grid:
    print(''.join('.' if t == 'CORRIDOR' else '#' for t in row))
```
