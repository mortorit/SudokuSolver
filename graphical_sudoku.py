import tkinter as tk
from tkinter import messagebox
import numpy as np

# ====================================================================================
# == SOLVER LOGIC ==
# ====================================================================================

def is_valid_solution(grid: np.ndarray) -> bool:
    """
    Checks if a completed 9x9 Sudoku grid respects all the rules.

    Args:
        grid: A 9x9 numpy array representing the Sudoku board.

    Returns:
        True if the solution is valid, False otherwise.
    """
    # The set of numbers that should be in each row, column, and block
    valid_set = set(range(1, 10))

    # 1. Check all rows
    for i in range(9):
        if set(grid[i, :]) != valid_set:
            return False

    # 2. Check all columns
    for i in range(9):
        if set(grid[:, i]) != valid_set:
            return False

    # 3. Check all 3x3 subgrids
    for r_block in range(0, 9, 3):
        for c_block in range(0, 9, 3):
            subgrid = grid[r_block:r_block+3, c_block:c_block+3]
            if set(subgrid.flatten()) != valid_set:
                return False

    # If all checks pass, the solution is valid
    return True

def get_possible_values(grid: np.array, possible_values:np.array, i:int, j:int, s:int):
    # first identify block
    block_x = 0 if j < 3 else 1 if j < 6 else 2
    block_y = 0 if i < 3 else 1 if i < 6 else 2

    all_values = np.copy(possible_values[i,j]) # Use copy to avoid modifying original during calc

    to_delete = set()

    for c in range(9):
        if grid[i,c] != -1:
            to_delete.add(int(grid[i,c]))
    for r in range(9):
        if grid[r,j] != -1:
            to_delete.add(int(grid[r,j]))

    for c in range(block_x*3, block_x*3+3):
        for r in range(block_y*3, block_y*3+3):
            if grid[r,c] != -1:
                to_delete.add(int(grid[r,c]))
    
    for v in to_delete:
        all_values[v-1] = 0

    return all_values


def check_only_value_possible(grid:np.array, possible_values:np.array, s:int):
    changed = False
    
    # Check for cells where only one number is possible
    for r in range(s):
        for c in range(s):
            if grid[r,c] == -1 and possible_values[r,c].sum() == 1:
                n = np.where(possible_values[r,c] == 1)[0][0]
                val = n + 1
                grid[r,c] = val
                possible_values[r,c] = 0 # This cell is now solved
                changed = True
                print(f"Naked single: setting ({r},{c}) to {val}")

    # Check for hidden singles in rows, cols, and blocks
    # This logic is complex and your original version had a bug.
    # For simplicity in this example, I'm focusing on the "naked single" above.
    # The full check_only_value_possible from your original code is kept below, bug-fixed.

    # Go through each row,column and grid and check if there is some forced value
    cols = possible_values.sum(axis=0)
    rows = possible_values.sum(axis=1)

    for c_block in range(3):
        for r_block in range(3):
            sgrid_start_x = 3*c_block
            sgrid_start_y = 3*r_block
            sgrid_end_x = sgrid_start_x + 3 
            sgrid_end_y = sgrid_start_y + 3

            sgrid = possible_values[sgrid_start_y:sgrid_end_y, sgrid_start_x:sgrid_end_x]
            sgrid_sum = sgrid.sum(axis=(0,1))

            for n in range(9):
                if sgrid_sum[n] == 1:
                    # Find where this single possibility is
                    found = False
                    for i_loc in range(3):
                        for j_loc in range(3):
                            if sgrid[i_loc,j_loc,n] == 1:
                                r, c = sgrid_start_y+i_loc, sgrid_start_x+j_loc
                                if grid[r,c] == -1: # Ensure we don't overwrite
                                    print(f"Hidden single in block: changing {r},{c} to {n+1}")
                                    grid[r,c] = n + 1
                                    possible_values[r,c] = 0
                                    changed = True
                                found = True
                                break
                        if found: break
    
    # Now seach if there is some value that is unique in a column
    for c in range(9):
        for n in range(9):
            if cols[c,n] == 1:
                for r in range(9):
                    if possible_values[r,c,n] == 1 and grid[r,c] == -1:
                        grid[r,c] = n + 1
                        possible_values[r,c] = 0
                        changed = True
                        print(f"Hidden single in col: changing {r},{c} to {n+1}")
                        break
    
    # Now seach if there is some value that is unique in a row
    for r in range(9):
        for n in range(9):
            if rows[r,n] == 1:
                for c in range(9):
                    if possible_values[r,c,n] == 1 and grid[r,c] == -1:
                        grid[r,c] = n + 1
                        possible_values[r,c] = 0
                        changed = True
                        print(f"Hidden single in row: changing {r},{c} to {n+1}")
                        break
    
    return grid, possible_values, changed


def iterative_simplify(grid:np.array, possible_values:np.array, s:int):
    while True:
        # First, update all possible values based on the current grid state
        for i in range(s):
            for j in range(s):
                if grid[i,j] == -1:
                    possible_values[i,j] = get_possible_values(grid, possible_values, i, j, s)

        # Then, try to find forced moves
        grid, possible_values, changed = check_only_value_possible(grid, possible_values, s)
        
        # If a full pass makes no changes, the grid is as simple as it can get with logic alone
        if not changed:
            break
            
    return grid, possible_values

def check_solved(grid, s):
    return -1 not in grid

def check_impossible(grid, possible_values, s):
    for i in range(s):
        for j in range(s):
            if grid[i,j] == -1 and possible_values[i,j].sum() == 0:
                return True
    return False

def get_fewest_options_idx(grid, possible_values, s):
    min_vals = 10
    idxs = ()
    for r in range(s):
        for c in range(s):
            if grid[r,c] == -1:
                vals = possible_values[r,c].sum()
                if vals < min_vals:
                    min_vals = vals
                    idxs = (r,c)
    return idxs if idxs else (-1, -1) # Return (-1,-1) if solved

# REFACTORED RECURSIVE SOLVER FOR BETTER STABILITY WITH A GUI
# This version returns the solved grid on success and None on failure.
def solve_sudoku_recursive(grid: np.array, s:int):
    # First, simplify the grid with logic
    possible_values = np.ones((s, s, s), dtype=np.int32)
    grid, possible_values = iterative_simplify(grid, possible_values, s)
    
    if check_solved(grid, s):
        return grid

    if check_impossible(grid, possible_values, s):
        return None

    # Find the best cell to start guessing
    r, c = get_fewest_options_idx(grid, possible_values, s)
    if r == -1: # Should be caught by check_solved, but as a safeguard
        return grid

    # Try each possible number for this cell
    options = np.where(possible_values[r, c] == 1)[0]
    for n_idx in options:
        guess = n_idx + 1
        print(f"Trying with {r},{c}={guess}")
        
        grid_copy = np.copy(grid)
        grid_copy[r, c] = guess
        
        result = solve_sudoku_recursive(grid_copy, s)
        
        if result is not None:
            return result # Solution found, pass it up

    return None # No option worked, backtrack


# ====================================================================================
# == NEW GRAPHICAL USER INTERFACE (GUI) CODE                                        ==
# ====================================================================================

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.geometry("500x550")
        self.cells = {}
        self.create_grid()
        self.create_buttons()
        self.create_status_bar()

    def create_grid(self):
        main_frame = tk.Frame(self.root, bg='black', bd=3)
        main_frame.pack(pady=10, padx=10)

        # Create 3x3 frames for the subgrids
        self.subgrid_frames = []
        for r_block in range(3):
            row_frames = []
            for c_block in range(3):
                frame = tk.Frame(main_frame, bg='black', bd=2)
                frame.grid(row=r_block, column=c_block)
                row_frames.append(frame)
            self.subgrid_frames.append(row_frames)

        # Create entry widgets inside the subgrid frames
        for r in range(9):
            for c in range(9):
                r_block, c_block = r // 3, c // 3
                validate_cmd = self.root.register(self.validate_input)
                
                cell = tk.Entry(
                    self.subgrid_frames[r_block][c_block],
                    width=2,
                    font=('Arial', 24, 'bold'),
                    justify='center',
                    bd=1,
                    validate='key',
                    validatecommand=(validate_cmd, '%P')
                )
                cell.grid(row=r % 3, column=c % 3, padx=1, pady=1)
                self.cells[(r, c)] = cell

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        solve_button = tk.Button(button_frame, text="Solve", font=('Arial', 14), command=self.solve_puzzle)
        solve_button.pack(side='left', padx=10)

        clear_button = tk.Button(button_frame, text="Clear", font=('Arial', 14), command=self.clear_grid)
        clear_button.pack(side='left', padx=10)
    
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Enter a puzzle and click 'Solve'")
        status_label = tk.Label(self.root, textvariable=self.status_var, font=('Arial', 12), bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def validate_input(self, value_if_allowed):
        """Allows only empty string or a single digit from 1-9."""
        if value_if_allowed == "" or (value_if_allowed.isdigit() and len(value_if_allowed) == 1 and value_if_allowed != '0'):
            return True
        return False

    def solve_puzzle(self):
        # 1. Get the grid from the GUI
        s = 9
        initial_grid = np.full((s, s), -1, dtype=np.int32)
        initial_clues = []
        try:
            for r in range(s):
                for c in range(s):
                    val = self.cells[(r, c)].get()
                    if val.isdigit():
                        initial_grid[r, c] = int(val)
                        initial_clues.append((r,c))
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter only digits 1-9.")
            return

        self.status_var.set("Solving...")
        self.root.update_idletasks() # Force GUI update

        # 2. Call the solver logic
        # Using the improved recursive function for better GUI interaction
        solution = solve_sudoku_recursive(np.copy(initial_grid), s)
        
        # 3. Display the result
        if solution is not None:
            for r in range(s):
                for c in range(s):
                    # Clear previous value
                    self.cells[(r,c)].delete(0, tk.END)
                    # Insert new value
                    self.cells[(r,c)].insert(0, str(solution[r,c]))
                    # Color the original clues black and the solved numbers blue
                    if (r,c) in initial_clues:
                        self.cells[(r,c)].config(fg='black')
                    else:
                        self.cells[(r,c)].config(fg='blue')
            self.status_var.set("Solved successfully!")
        else:
            self.status_var.set("This puzzle is impossible or has no unique solution.")
            messagebox.showinfo("Solver Result", "Could not find a solution for this puzzle.")

    def clear_grid(self):
        for r in range(9):
            for c in range(9):
                self.cells[(r, c)].delete(0, tk.END)
                self.cells[(r, c)].config(fg='black')
        self.status_var.set("Grid cleared. Ready for a new puzzle.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()