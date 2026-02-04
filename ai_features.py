from settings import FIELD_W, FIELD_H


def column_heights(board):
    heights = [0] * FIELD_W
    for column_index in range(FIELD_W):
        for row_index in range(FIELD_H):
            if board[row_index][column_index]:
                heights[column_index] = FIELD_H - row_index
                break
    return heights


def aggregate_height(board):
    return sum(column_heights(board))


def complete_lines(board):
    return sum(1 for row_index in range(FIELD_H) if all(board[row_index][col] for col in range(FIELD_W)))


def holes(board):
    hole_count = 0
    for column_index in range(FIELD_W):
        seen_block = False
        for row_index in range(FIELD_H):
            if board[row_index][column_index]:
                seen_block = True
            elif seen_block:
                hole_count += 1
    return hole_count


def bumpiness(board):
    heights = column_heights(board)
    return sum(abs(heights[i] - heights[i + 1]) for i in range(FIELD_W - 1))
