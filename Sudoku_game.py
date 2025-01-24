import random
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class SudokuGenerator:
    """
    A class to generate Sudoku puzzles of varying difficulty levels.
    This class handles the creation, validation, and presentation of Sudoku puzzles.
    """

    # Dictionary defining the number of clues (given numbers) for each difficulty level
    # Fewer clues = harder puzzle
    DIFFICULTY_SETTINGS = {
        "easy": {"min_clues": 36, "max_clues": 42},     # More clues for beginners
        "medium": {"min_clues": 32, "max_clues": 35},   # Balanced difficulty
        "hard": {"min_clues": 28, "max_clues": 31},     # Challenging
        "expert": {"min_clues": 24, "max_clues": 27},   # Very challenging
        "insane": {"min_clues": 22, "max_clues": 23}    # Extremely difficult
    }

    def __init__(self, difficulty: str = "medium") -> None:
        """
        Initialize the Sudoku generator with a specific difficulty level.
        
        Args:
            difficulty (str): The desired difficulty level ('easy', 'medium', 'hard', 'expert', 'insane')
        """
        # Validate the difficulty setting
        if difficulty not in self.DIFFICULTY_SETTINGS:
            raise ValueError(f"Invalid difficulty level. Choose from: {', '.join(self.DIFFICULTY_SETTINGS.keys())}")
        
        self.difficulty = difficulty
        # Initialize empty 9x9 grid
        self.grid = [[0] * 9 for _ in range(9)]
        # Will store the complete solution
        self.solution = None

    def _is_valid(self, grid, row, col, num):
        """
        Check if placing a number at the specified position is valid according to Sudoku rules.
        
        Args:
            grid (List[List[int]]): The current Sudoku grid
            row (int): Row index (0-8)
            col (int): Column index (0-8)
            num (int): Number to validate (1-9)
        
        Returns:
            bool: True if the number can be placed at the position, False otherwise
        """
        # Check row
        for i in range(9):
            # Check if number exists in row
            if grid[row][i] == num:
                return False
            # Check if number exists in column
            if grid[i][col] == num:
                return False
            # Check if number exists in 3x3 box
            if grid[row // 3 * 3 + i // 3][col // 3 * 3 + i % 3] == num:
                return False
        return True

    def _fill_grid(self, grid):
        """
        Fill the Sudoku grid using a backtracking algorithm.
        This method generates a complete, valid Sudoku solution.
        
        Args:
            grid (List[List[int]]): The grid to fill
        
        Returns:
            bool: True if the grid was successfully filled, False otherwise
        """
        for row in range(9):
            for col in range(9):
                # Find an empty cell
                if grid[row][col] == 0:
                    # Try numbers 1-9 in random order
                    random_nums = list(range(1, 10))
                    random.shuffle(random_nums)
                    for num in random_nums:
                        if self._is_valid(grid, row, col, num):
                            # Place the number if it's valid
                            grid[row][col] = num
                            # Recursively try to fill the rest
                            if self._fill_grid(grid):
                                return True
                            # If we couldn't fill the rest, backtrack
                            grid[row][col] = 0
                    return False
        return True

    def _remove_cells(self):
        """
        Remove numbers from the completed grid to create the puzzle.
        The number of cells removed depends on the difficulty level.
        """
        # Get difficulty settings
        min_clues, max_clues = self.DIFFICULTY_SETTINGS[self.difficulty].values()
        # Randomly choose how many clues to keep
        clues = random.randint(min_clues, max_clues)
        cells_to_remove = 81 - clues  # 81 is total number of cells in 9x9 grid

        # Remove random cells until we reach the target number
        while cells_to_remove > 0:
            row, col = random.randint(0, 8), random.randint(0, 8)
            if self.grid[row][col] != 0:
                self.grid[row][col] = 0
                cells_to_remove -= 1

    def generate_sudoku(self):
        """
        Generate a new Sudoku puzzle with a solution.
        This creates both the complete solution and the puzzle with removed numbers.
        """
        # Start with empty grid
        self.grid = [[0] * 9 for _ in range(9)]
        # Fill it completely
        self._fill_grid(self.grid)
        # Save the complete solution
        self.solution = [row[:] for row in self.grid]
        # Remove cells to create the puzzle
        self._remove_cells()

    def create_html_puzzle(self, port):
        """
        Create an interactive HTML page for the Sudoku puzzle.
        
        Args:
            port (int): The server port number for proper URL generation
        
        Returns:
            str: Complete HTML document as a string
        """
        # Start HTML document with styling
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sudoku Puzzle - {self.difficulty.capitalize()} Difficulty</title>
            <style>
                /* CSS styles for the page layout */
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                }}
                /* Header styling */
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                /* Control panel styling */
                .controls {{
                    margin-bottom: 20px;
                    text-align: center;
                }}
                /* Button and select styling */
                select, .btn {{
                    margin: 5px;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    border: none;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                }}
                /* Dropdown menu styling */
                select {{
                    background-color: #f0f0f0;
                    color: #333;
                }}
                /* Button styling */
                .btn {{
                    background-color: #4CAF50;
                    color: white;
                }}
                .btn:hover {{
                    background-color: #45a049;
                }}
                /* Sudoku grid styling */
                .sudoku-grid {{
                    display: grid;
                    grid-template-columns: repeat(9, 50px);
                    grid-gap: 0;
                    border: 4px solid #333;
                    background-color: #fff;
                }}
                /* Individual cell styling */
                .sudoku-cell {{
                    width: 50px;
                    height: 50px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-size: 20px;
                    font-weight: bold;
                    border: 1px solid #ccc;
                    box-sizing: border-box;
                }}
                /* Input cell styling */
                .sudoku-cell input {{
                    width: 100%;
                    height: 100%;
                    text-align: center;
                    font-size: 20px;
                    border: none;
                    outline: none;
                    background: transparent;
                    font-weight: bold;
                }}
                /* Given number cell styling */
                .sudoku-cell.given {{
                    background-color: #f0f0f0;
                    color: #000;
                }}
                /* 3x3 box border styling */
                .section-border-right {{
                    border-right: 3px solid #333;
                }}
                .section-border-bottom {{
                    border-bottom: 3px solid #333;
                }}
                /* Solution grid styling */
                .solution-container {{
                    display: none;
                    grid-template-columns: repeat(9, 50px);
                    grid-gap: 0;
                    border: 4px solid #333;
                    background-color: #fff;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Sudoku Puzzle - {self.difficulty.capitalize()} Difficulty</h1>
            <!-- Control panel -->
            <div class="controls">
                <select id="difficulty-selector">
                    <option value="easy" {"selected" if self.difficulty == "easy" else ""}>Easy</option>
                    <option value="medium" {"selected" if self.difficulty == "medium" else ""}>Medium</option>
                    <option value="hard" {"selected" if self.difficulty == "hard" else ""}>Hard</option>
                    <option value="expert" {"selected" if self.difficulty == "expert" else ""}>Expert</option>
                    <option value="insane" {"selected" if self.difficulty == "insane" else ""}>Insane</option>
                </select>
                <button class="btn" id="generate-btn">Generate New Puzzle</button>
                <button class="btn" id="show-solution-btn">Show Solution</button>
            </div>
            <!-- Main puzzle grid -->
            <div class="sudoku-grid" id="puzzle-grid">
        '''

        # Generate the puzzle grid HTML
        for i in range(9):
            for j in range(9):
                cell_class = 'sudoku-cell'
                # Add borders for 3x3 box separation
                if j in [2, 5]:
                    cell_class += ' section-border-right'
                if i in [2, 5]:
                    cell_class += ' section-border-bottom'

                # Create either a given number cell or an input cell
                if self.grid[i][j] != 0:
                    html += f'<div class="{cell_class} given">{self.grid[i][j]}</div>'
                else:
                    html += f'<div class="{cell_class}"><input type="text" maxlength="1" data-row="{i}" data-col="{j}"></div>'

        # Add solution grid (hidden by default)
        html += '''
            </div>
            <div class="solution-container" id="solution-container">
        '''

        # Generate the solution grid HTML
        for i in range(9):
            for j in range(9):
                cell_class = 'sudoku-cell'
                if j in [2, 5]:
                    cell_class += ' section-border-right'
                if i in [2, 5]:
                    cell_class += ' section-border-bottom'
                html += f'<div class="{cell_class}">{self.solution[i][j]}</div>'

        # Add JavaScript for interactivity
        html += f'''
            </div>
            <script>
                // Toggle solution visibility
                document.getElementById('show-solution-btn').addEventListener('click', () => {{
                    const solutionContainer = document.getElementById('solution-container');
                    const btn = document.getElementById('show-solution-btn');
                    if (solutionContainer.style.display === 'grid') {{
                        solutionContainer.style.display = 'none';
                        btn.textContent = 'Show Solution';
                    }} else {{
                        solutionContainer.style.display = 'grid';
                        btn.textContent = 'Hide Solution';
                    }}
                }});

                // Handle new puzzle generation
                document.getElementById('generate-btn').addEventListener('click', () => {{
                    const difficulty = document.getElementById('difficulty-selector').value;
                    window.location.href = `http://localhost:{port}/?difficulty=${{difficulty}}`;
                }});

                // Restrict input to numbers 1-9 only
                document.querySelectorAll('.sudoku-cell input').forEach(input => {{
                    input.addEventListener('input', e => {{
                        e.target.value = e.target.value.replace(/[^1-9]/g, '');
                    }});
                }});
            </script>
        </body>
        </html>
        '''
        return html

class SudokuRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the Sudoku web application.
    Handles incoming requests and generates appropriate responses.
    """
    
    def do_GET(self):
        """Handle GET requests to the server"""
        # Parse query parameters from URL
        query = parse_qs(urlparse(self.path).query)
        # Get difficulty from query params, default to 'medium'
        difficulty = query.get('difficulty', ['medium'])[0]
        
        # Create and generate new puzzle
        generator = SudokuGenerator(difficulty)
        generator.generate_sudoku()
        
        # Get server port for proper URL generation in HTML
        port = self.server.server_port
        html_content = generator.create_html_puzzle(port)
        
        # Send HTTP response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

def play(difficulty="medium", port=8000):
    """
    Start the Sudoku game server and open it in the default web browser.
    
    Args:
        difficulty (str): Initial difficulty level
        port (int): Port number for the local server
    """
    # Create and start the HTTP server
    server = HTTPServer(('localhost', port), SudokuRequestHandler)
    print(f"Server started at http://localhost:{port}")
    
    # Open the default web browser to the game
    webbrowser.open(f'http://localhost:{port}/?difficulty={difficulty}')
    
    try:
        # Run the server until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        # Handle clean shutdown on Ctrl+C
        pass
    finally:
        # Ensure server is properly closed
        server.server_close()

if __name__ == "__main__":
    # Start the game with default settings when run directly
    play(difficulty="medium")