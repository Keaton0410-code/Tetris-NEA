from settings import FIELD_W, FIELD_H

def column_heights(board):
    """Return list of heights per column."""
    heights = [0] * FIELD_W
    for x in range(FIELD_W):
        for y in range(FIELD_H):
            if board[y][x]:
                heights[x] = FIELD_H - y
                break
    return heights


def aggregate_height(board):
    return sum(column_heights(board))

def complete_lines(board):
    return sum(1 for y in range(FIELD_H) if all(board[y][x] for x in range(FIELD_W)))

def holes(board):
    """Count empty cells that have at least one filled cell above in the same column."""
    count = 0
    for x in range(FIELD_W):
        seen_block = False
        for y in range(FIELD_H):
            if board[y][x]:
                seen_block = True
            elif seen_block:
                count += 1
    return count

def bumpiness(board):
    heights = column_heights(board)
    return sum(abs(heights[x] - heights[x + 1]) for x in range(FIELD_W - 1))
