from mazegenerator.mazegenerator import MazeGenerator
import pygame  
class MazeLoader:


    def generate(self, width, height, seed) -> list[list[str]] | None:
        i=0
        j=0
        
        extended_maze = [["WALL" for _ in range(width*2+1)]for _ in range(height*2+1)]

        try:
            maze= MazeGenerator(size=(width, height), perfect=False, entry_cell=(0, 0), exit_cell=(-1, -1), seed=seed)
        except Exception as e:
            print(f"Error generating maze: {e}")
            return None

        for row in maze.maze:
            for cell in row:
                extended_maze[i*2+1][j*2+1] = "CORRIDOR"
                if cell & 1 == 0:
                    extended_maze[i*2][j*2+1] = "CORRIDOR"
                if cell & 2 ==0:
                    extended_maze[i*2+1][j*2+2] = "CORRIDOR"
                if cell & 4== 0:
                    extended_maze[i*2+2][j*2+1] = "CORRIDOR"
                if cell & 8 == 0:
                    extended_maze[i*2+1][j*2] = "CORRIDOR"
                j+=1
            j=0
            i+=1
        return extended_maze




    WALL_COLOR = (33, 33, 255)
    BG_COLOR = (0, 0, 0)

    def draw(self, screen, grid):
        rows = len(grid)
        cols = len(grid[0])
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Square cells so the maze isn't stretched, centred with a letterbox.
        cell = min(screen_width // cols, screen_height // rows)
        offset_x = (screen_width - cell * cols) // 2
        offset_y = (screen_height - cell * rows) // 2

        # Thickness of the blue "tube" outline. Thinner walls => wider corridors.
        border = max(2, cell // 4)

        screen.fill(self.BG_COLOR)

        def is_wall(r, c):
            return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "WALL"

        # Pass 1: fill every wall cell solid blue.
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != "WALL":
                    continue
                x = offset_x + c * cell
                y = offset_y + r * cell
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
    
