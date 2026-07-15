from mazegenerator.mazegenerator import MazeGenerator
import pygame  
class MazeLoader:


    def generate(self, width, height, seed) -> list[list[str]] | None:
        extended_maze = [["WALL" for _ in range(width*2+1)]for _ in range(height*2+1)]

        try:
            maze= MazeGenerator(size=(width, height), perfect=False, entry_cell=(0, 0), exit_cell=(-1, -1), seed=seed)
        except Exception as e:
            print(f"Error generating maze: {e}")
            return None

        # The generator hides a "42" in the middle of every maze: those
        # cells keep the value 15 (walled on ALL four sides) and are never
        # visited, so 15 is a unique marker for "this cell is part of the
        # 42". They become their own wall type, FT_WALL:
        #   - drawn in a different colour than normal walls,
        #   - still solid for the player (anything != CORRIDOR blocks),
        #   - and NOT corridors. This also fixes a real bug: before, their
        #     centres were marked CORRIDOR, so pacgums were placed inside
        #     the sealed "42" where pacman could never eat them - which
        #     made every level impossible to finish.
        cells = maze.maze
        for i, row in enumerate(cells):
            for j, cell in enumerate(row):
                if cell == 15:
                    extended_maze[i*2+1][j*2+1] = "FT_WALL"
                    # Also paint the edge cell between two neighbouring
                    # "42" cells, so the digits show as connected strokes
                    # instead of a grid of separate dots.
                    if j + 1 < len(row) and row[j + 1] == 15:
                        extended_maze[i*2+1][j*2+2] = "FT_WALL"
                    if i + 1 < len(cells) and cells[i + 1][j] == 15:
                        extended_maze[i*2+2][j*2+1] = "FT_WALL"
                    continue
                extended_maze[i*2+1][j*2+1] = "CORRIDOR"
                if cell & 1 == 0:
                    extended_maze[i*2][j*2+1] = "CORRIDOR"
                if cell & 2 ==0:
                    extended_maze[i*2+1][j*2+2] = "CORRIDOR"
                if cell & 4== 0:
                    extended_maze[i*2+2][j*2+1] = "CORRIDOR"
                if cell & 8 == 0:
                    extended_maze[i*2+1][j*2] = "CORRIDOR"
        return extended_maze




    WALL_COLOR = (33, 33, 255)
    FT_COLOR = (255, 0, 255)  # magenta for the "42" hidden in the maze
    BG_COLOR = (0, 0, 0)

    # NEW (Phase 4): the cell size and letterbox offsets used to be locals
    # inside draw(). Now that the player and the pacgums also need to know
    # exactly where each cell sits on screen, the math lives in ONE method
    # everybody calls - so the drawing and the collision logic can never
    # disagree about the geometry.
    def get_layout(self, screen, grid):
        rows = len(grid)
        cols = len(grid[0])
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Square cells so the maze isn't stretched, centred with a letterbox.
        cell = min(screen_width // cols, screen_height // rows)
        offset_x = (screen_width - cell * cols) // 2
        offset_y = (screen_height - cell * rows) // 2
        return cell, offset_x, offset_y

    def draw(self, screen, grid):
        rows = len(grid)
        cols = len(grid[0])
        cell, offset_x, offset_y = self.get_layout(screen, grid)

        # Thickness of the blue "tube" outline. Thinner walls => wider corridors.
        border = max(2, cell // 4)

        screen.fill(self.BG_COLOR)

        def is_wall(r, c):
            return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "WALL"

        # Pass 1: fill every wall cell solid blue - and the "42" cells
        # solid magenta. FT_WALL is deliberately NOT hollowed out by pass 2
        # below, so the 42 stays a bold filled shape that stands out from
        # the outlined blue walls around it.
        for r in range(rows):
            for c in range(cols):
                x = offset_x + c * cell
                y = offset_y + r * cell
                if grid[r][c] == "FT_WALL":
                    pygame.draw.rect(screen, self.FT_COLOR, (x, y, cell, cell))
                elif grid[r][c] == "WALL":
                    pygame.draw.rect(screen, self.WALL_COLOR, (x, y, cell, cell))

        # Pass 2: carve a black channel through the middle of each wall cell,
        # extended toward any neighbouring wall so the channels join up. What's
        # left is a thin, continuous blue outline: the classic Pac-Man look.
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != "WALL":
                    continue
                x = offset_x + c * cell
                y = offset_y + r * cell
                ix, iy = x + border, y + border
                iw = ih = cell - 2 * border
                if is_wall(r, c - 1):
                    ix -= border
                    iw += border
                if is_wall(r, c + 1):
                    iw += border
                if is_wall(r - 1, c):
                    iy -= border
                    ih += border
                if is_wall(r + 1, c):
                    ih += border
                if iw > 0 and ih > 0:
                    pygame.draw.rect(screen, self.BG_COLOR, (ix, iy, iw, ih))
    
