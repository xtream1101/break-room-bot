import os.path
import exceptions
from PIL import Image


def gen_new_board(rows=6, cols=7):
    return [[0] * cols for i in range(rows)]


def place_piece(board, column, player):
    column_idx = column - 1
    for i in range(1, len(board) + 1):
        # Find the next open spot to play
        if board[-i][column_idx] == 0:
            board[-i][column_idx] = player
            # Player placed a piece, move is over
            break
    else:
        raise exceptions.ColumnFull
    return board


def check_tie(board):
    """Must only check after check_win

    Only have to see if there are any free spaces in the top row

    Args:
        board (list of list): Board as a list of lists
    """
    return not 0 in board[0]

def check_win(board, col_played):
    # TODO: Return all wins with the cells they won in
    col_played_idx = col_played - 1

    for row_idx in range(len(board)):
        if board[row_idx][col_played_idx] != 0:
            # Found the last move played
            last_move = {'r': row_idx, 'c': col_played_idx}
            break

    player = board[last_move['r']][last_move['c']]

    ###
    # Check horizontal
    ###
    horizontal_check = [
        range(col_played_idx - 1, -1, -1),  # Left
        range(col_played_idx + 1, len(board[0])),  # Right
    ]
    count = 0
    for direction in horizontal_check:
        for col_idx in direction:
            if board[last_move['r']][col_idx] == player:
                count += 1
                continue
            break

    # Check if win
    if count >= 3:
        return True

    ###
    # Check vertical
    ###
    count = 0
    # Only need to check down
    for row_idx in range(last_move['r'] + 1, len(board)):
        if board[row_idx][last_move['c']] == player:
            count += 1
            continue
        break

    # Check if win
    if count >= 3:
        return True

    ###
    # Check diagonals
    ###
    angles = [
        [  # Check /
            (1, -1),  # down-left
            (-1, 1),  # up-right
        ],
        [  # Check \
            (-1, -1),  # up-left
            (1, 1),  # down-right
        ],
    ]
    for slash in angles:
        count = 0
        for slash_direction in slash:
            for i in range(1, 4):  # Only need to check the next 3 spots
                row = last_move['r'] + (i * slash_direction[0])
                col = last_move['c'] + (i * slash_direction[1])
                try:
                    if board[row][col] == player:
                        count += 1
                        continue
                except IndexError:
                    break
                break
        # Check if win
        if count >= 3:
            return True

    return False


def render_board(board, board_name):
    piece_d = 50
    piece_space = 10
    board_img = Image.open("assets/board.png")
    _, height = board_img.size
    player1_piece = Image.open("assets/piece_red.png")
    player2_piece = Image.open("assets/piece_yellow.png")
    for row_idx, row in enumerate(board):
        for col_idx, piece in enumerate(row):
            if piece != 0:
                x = (piece_d*col_idx)+((col_idx+1)*piece_space)
                adjust_header = height-((50*6)+(10*(6+1)))
                y = (piece_d*row_idx)+((row_idx+1)*piece_space) + adjust_header
                player_piece = player1_piece if piece == 1 else player2_piece
                board_img.paste(player_piece, (x, y), player_piece)

    if not os.path.exists(os.environ['RENDERED_IMAGES']):
        os.makedirs(os.environ['RENDERED_IMAGES'])
    save_path = os.path.join(os.environ['RENDERED_IMAGES'], board_name + '.png')
    # board_img = board_img.convert('RGB')
    # board_img.save(save_path, quality=10)
    board_img.save(save_path)
