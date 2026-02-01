from settings import FIELD_W, FIELD_H

def column_heights(board):
    """Returns a list with the height of the tallest block in each column."""
    heights = [0] * FIELD_W
    for x in range(FIELD_W):
        for y in range(FIELD_H):
            if board[y][x]:
                # Height measured from the bottom of the grid
                heights[x] = FIELD_H - y
                break   # First filled cell from the top 
    return heights

def aggregate_height(board):
    """Sum of every column's height penalises tall stacks."""
    return sum(column_heights(board))

def complete_lines(board):
    """Counts how many rows are completely filled."""
    return sum(1 for y in range(FIELD_H) if all(board[y][x] for x in range(FIELD_W)))

def holes(board):
    """Counts empty cells that have at least one filled cell above them in the same column."""
    count = 0
    for x in range(FIELD_W):
        seen_block = False
        for y in range(FIELD_H):
            if board[y][x]:
                seen_block = True
            elif seen_block:
                # Empty cell with something above it = hole
                count += 1
    return count

def bumpiness(board):
    """Sum of the absolute height differences between every adjacent column."""
    heights = column_heights(board)
    return sum(abs(heights[x] - heights[x + 1]) for x in range(FIELD_W - 1))