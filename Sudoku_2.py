import random
import time
import sys
import copy


def symbol_frequencies(board, symbol_set):
    d = {symbol: board.count(symbol) for symbol in symbol_set}
    for symbol in sorted(d):
        print(symbol, d[symbol])
    print(". {}".format(board.count(".")))


def display_board(board):
    for row in range(board_size):
        if row % subblock_height == 0:
            print("-" * (2 * board_size + 1))
        board_row = board[board_size * row: board_size * (row + 1)]
        br_format = "|"
        for subblock in range(board_size // subblock_width):
            br_format += ' '.join(board_row[subblock_width * subblock: subblock_width * (subblock + 1)])
            br_format += "|"
        print(br_format)
    print("-" * (2 * board_size + 1))


# Finds the var that doesn't have a definite value yet with
# the most constraints. Most constraints = least possible positions
# A var has a definite value if it only have one possible position
def most_constrained_var(board):
    min_possible_n = None
    min_possible_l = []

    for row, col in board:
        possible = len(board[row, col])
        if possible <= 1:
            continue
        if min_possible_n is None or possible < min_possible_n:
            min_possible_n = possible
            min_possible_l = []

        if possible == min_possible_n:
            min_possible_l.append((row, col))

    return random.choice(min_possible_l)


def get_sorted_values(board, row, col):

    block_neighbors = neighbors[row, col]
	
    added_constraints = {}  # dict[key] = # of neighbors that this restricts

    for value in symbol_set:  # tests all possible values
        added_constraints[value] = 0
        for n_row, n_col in block_neighbors:
            neighbor_values = board[n_row, n_col]

            if value in neighbor_values:
                # neighbor is solved, and equals this value, so we can't use this value
                if len(neighbor_values) == 1:
                    del added_constraints[value]
                    break
                # neighbor is not solved, so we say this value adds more constraints
                else:
                    added_constraints[value] += 1

    return sorted(added_constraints.keys(), key=lambda x: -added_constraints[x])


# Board structure:
# Dictionary[row, col] = "Possible values"
# During an assignment, Dictionary[row, col] = Assignment
# And any Dictionary[] that are affected remove the possible value of Assignment
def assign(board, row, col, value):
    new_board = copy.copy(board)

    new_board[row, col] = value

    return new_board


def forward_looking(board):
    new_board = copy.copy(board)
    solved_indices = [square for square in board if len(board[square]) == 1]
    while solved_indices:
        row, col = solved_indices.pop()

        value = new_board[row, col]

        for n_row, n_col in neighbors[row, col]:
            # Make sure we don't check against the square itself
            if n_row == row and n_col == col:
                continue

            neighbor_value = new_board[n_row, n_col]
            if value in neighbor_value:
                new_board[n_row, n_col] = neighbor_value.replace(value, '')
                new_len = len(new_board[n_row, n_col])
                if new_len == 0:  # we removed the only possible neighbor_value
                    # print('\t\t', new_board)
                    # print('\t\t\t', value, (row, col), (n_row, n_col))
                    return None
                elif new_len == 1:
                    solved_indices.append((n_row, n_col))
    return new_board


def constraint_prop(board):
    overall_change_made = False
    run_once = False

    constraints = [constraint_rows, constraint_columns, constraint_blocks]

    # Keep doing constraint propagation until no more changes are made
    while not run_once or overall_change_made:
        run_once = True

        # We run forward looking each time for optimization
        board = forward_looking(board)

        if board is None:  # If this board fails the forward-looking, return a failure
            return None

        # No changes have been made yet this pass-through
        # If a change is made, keep looping through
        overall_change_made = False

        # Loop over each constraint set
        for constraint_set in constraints:

            # Subset = row, col, block
            for subset in constraint_set:

                # Go value-by-value, checking if only one square has that value
                for possible_value in symbol_set:
                    squares_with_value = []
                    for square in constraint_set[subset]:
                        if possible_value in board[square]:
                            squares_with_value.append(square)

                    # Only one square has this possible value, so consider it solved
                    if len(squares_with_value) == 1:
                        square = squares_with_value[0]

                        # Make sure we don't say "changed" if the square was already solved
                        if len(board[square]) > 1:
                            board[square] = possible_value

                            overall_change_made = True

                    # Impossible situation: none of the squares have that possible value
                    elif len(squares_with_value) == 0:
                        return None  # Return a failure
    return board


# Since each square in the board is a representation of possible values,
# if each square only has one possible value, we know we've solved the board.
def goal_test(board):
    found_longer = False
    for possibility in board.values():
        if len(possibility) > 1:
            found_longer = True
    return not found_longer


def csp_backtrack_fl(board):
    if goal_test(board):
        return board

    row, col = most_constrained_var(board)

    sorted_values = get_sorted_values(board, row, col)

    for value in sorted_values:

        # Placing [value] in var
        new_board = assign(board, row, col, value)

        # Updates neighbors accordingly
        # Returns None if any neighbor has no more possibilities after this placement
        checked_board = constraint_prop(new_board)
        # print('\t', checked_board)

        # This board state is possible
        if checked_board is not None:
            result = csp_backtrack_fl(checked_board)
            if result is not None:
                return result
    return None


alphabet = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def preprocess(size):
    global symbol_set, subblock_width, subblock_height, board_size, constraint_columns, constraint_blocks, constraint_rows, neighbors, possibilities

    board_size = size
    symbol_set = alphabet[:board_size]

    max_block_height = int(board_size ** 0.5)

    subblock_width, subblock_height = board_size, 1

    for subblock_height in range(max_block_height, 0, -1):
        div, mod = divmod(board_size, subblock_height)
        if mod == 0:
            subblock_width = div
            break

    sb_wc = board_size // subblock_width
    sb_hc = board_size // subblock_height

    constraint_columns = {column: {(row, column) for row in range(board_size)} for column in range(board_size)}
    constraint_rows = {row: {(row, column) for column in range(board_size)} for row in range(board_size)}
    constraint_blocks = {}

    for row in range(board_size):
        for col in range(board_size):
            block = row // subblock_height, col // subblock_width
            if block not in constraint_blocks:
                constraint_blocks[block] = set()
            constraint_blocks[block].add((row, col))

    neighbors = {}
    for row in range(board_size):
        for col in range(board_size):
            square = row, col
            block_row, block_col = row // subblock_height, col // subblock_width
            neighbors[square] = \
                constraint_rows[row] \
                .union(constraint_columns[col]) \
                .union(constraint_blocks[block_row, block_col])


def data_structure(board_str):
    possible = {}
    for index in range(len(board_str)):
        row, col = divmod(index, board_size)

        # If this spot is empty, then we can add all spaces as possibilities
        # Otherwise, just one possibility: whatever the spot's value is
        if board_str[index] == '.':
            possible[row, col] = symbol_set
        else:
            possible[row, col] = board_str[index]

    return possible


def unpack_data_structure(data_structure):
    if data_structure is None:
        return ""

    board_str = ""
    for square in sorted(data_structure):
        if len(data_structure[square]) == 1:
            board_str += data_structure[square]
        else:
            board_str += "."

    return board_str

last_size = 0

def solve(board):
    global last_size
    
    if len(board) != last_size:
        last_size = int(len(board) ** 0.5)
        preprocess(last_size)

    board_ds = data_structure(board)
    board_ds = forward_looking(board_ds)

    result = csp_backtrack_fl(board_ds)

    solved_board = unpack_data_structure(result)

    return solved_board