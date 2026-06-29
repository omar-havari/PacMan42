from mazegenerator.mazegenerator import MazeGenerator
import pygame  
class MazeLoader:


    def generate(self, width, height, seed) -> list[list[str]] | None:
        i=0
        j=0

        cells = [[0 for _ in range(width)] for _ in range(height)]
        try:
            maze= MazeGenerator(size=(width, height), perfect=False, entry_cell=(0, 0), exit_cell=(-1, -1), seed=seed)
        except Exception as e:
            print(f"Error generating maze: {e}")
            return None

        for row in maze.maze:
            for cell in row:
                if cell != 15:
                    cells[i][j] = "CORRIDOR"
                else:
                    cells[i][j] = "WALL"
                j+=1
            j=0
            i+=1
        return cells




    def draw(self, screen, grid):
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        cell_width = screen_width // len(grid[0])
        cell_height = screen_height // len(grid)

        

        for row_index, row in enumerate(grid):
            for col_index,cell in enumerate(row):
                if cell == "WALL":
                    pygame.draw.rect(screen, (0,0,255) , (col_index * cell_width, row_index * cell_height, cell_width, cell_height))
                if cell == "CORRIDOR":
                    pygame.draw.rect(screen, (0,0,0), (col_index * cell_width, row_index * cell_height, cell_width, cell_height))
    
