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




    def draw(self, screen, grid):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        cell_width = screen_width // len(grid[0])
        cell_height = screen_height // len(grid)

        screen.fill((0, 0, 0))

        for row_index, row in enumerate(grid):
            for col_index, cell in enumerate(row):
                x = col_index * cell_width
                y = row_index * cell_height
                if cell == "WALL":
                    pygame.draw.rect(screen, (33, 33, 255), (x, y, cell_width, cell_height))
                elif cell == "CORRIDOR":
                    pygame.draw.rect(screen, (0, 0, 40), (x, y, cell_width, cell_height))
    
