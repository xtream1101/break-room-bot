import boto3
import os.path
import tempfile
import exceptions
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


PIECE_D = 50
PIECE_SPACE = 11


def gen_new_board(rows=6, cols=7):
    return [[0] * cols for i in range(rows)]


def place_piece(board, column, player):
    column_idx = column - 1
    for i in range(1, len(board) + 1):
        # Find the next open spot to play
        row_idx = -i + len(board)
        if board[row_idx][column_idx] == 0:
            board[row_idx][column_idx] = player
            latest_move = (row_idx, column_idx)
            # Player placed a piece, move is over
            break
    else:
        raise exceptions.ColumnFull
    return board, latest_move


def check_tie(board):
    """Must only check after check_win

    Only have to see if there are any free spaces in the top row

    Args:
        board (list of list): Board as a list of lists
    """
    return 0 not in board[0]


def check_win(board, col_played):
    wins = []
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
    win = [(last_move['r'], last_move['c'])]
    for direction in horizontal_check:
        for col_idx in direction:
            if board[last_move['r']][col_idx] == player:
                win.append((last_move['r'], col_idx))
                continue
            break

    # Check if win
    if len(win) >= 4:
        wins.append(win)

    ###
    # Check vertical
    ###
    win = [(last_move['r'], last_move['c'])]
    # Only need to check down
    for row_idx in range(last_move['r'] + 1, len(board)):
        if board[row_idx][last_move['c']] == player:
            win.append((row_idx, last_move['c']))
            continue
        break

    # Check if win
    if len(win) >= 4:
        wins.append(win)

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
        win = [(last_move['r'], last_move['c'])]
        for slash_direction in slash:
            for i in range(1, 4):  # Only need to check the next 3 spots
                row = last_move['r'] + (i * slash_direction[0])
                col = last_move['c'] + (i * slash_direction[1])
                if row < 0 or col < 0:
                    # Prevent wraping around the board
                    break
                try:
                    if board[row][col] == player:
                        win.append((row, col))
                        continue
                except IndexError:
                    break
                break

        # Check if win
        if len(win) >= 4:
            wins.append(win)

    return wins


def render_player_banner(player1_name, player2_name, board_name, theme='classic'):
    template = Image.open("assets/player_banner.png")
    player1_piece = Image.open(f"assets/{theme}/player1.png")
    player2_piece = Image.open(f"assets/{theme}/player2.png")

    template.paste(player1_piece, (2, 2), player1_piece)
    template.paste(player2_piece, (219, 2), player2_piece)
    draw = ImageDraw.Draw(template)
    font = ImageFont.truetype("Lato-Bold.ttf", 16)
    draw.text((58, 20), player1_name[:20], (66, 135, 245), font=font)
    draw.text((278, 20), player2_name[:20], (66, 135, 245), font=font)

    s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
    file_key = board_name + '_player_banner.png'
    with tempfile.NamedTemporaryFile() as tmp:
        template.save(tmp.name, format='png')
        s3.upload_file(tmp.name,
                       os.environ['RENDERED_IMAGES_BUCKET'],
                       file_key,
                       ExtraArgs={'ContentType': 'image/png'})

    return f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/{file_key}"


def get_piece_x(row_idx, col_idx):
    return (PIECE_D * col_idx) + ((col_idx + 1) * PIECE_SPACE)


def get_piece_y(row_idx, col_idx, board_height):
    adjust_header = board_height - ((PIECE_D * 6) + (PIECE_SPACE * (6 + 1)))
    return (PIECE_D * row_idx) + ((row_idx + 1) * PIECE_SPACE) + adjust_header


def get_overlay_x(row_idx, col_idx, piece_width):
    return round(get_piece_x(row_idx, col_idx) + ((PIECE_D / 2) - (piece_width / 2)))


def get_overlay_y(row_idx, col_idx, piece_height, board_height):
    return round(get_piece_y(row_idx, col_idx, board_height) + ((PIECE_D / 2) - (piece_height / 2)))


def add_lastest_move_overlay(board_img, latest_move=(None, None), theme='classic'):
    if latest_move != (None, None):
        lastest_move_img = Image.open(f"assets/{theme}/latest_move.png")
        latest_move_w, latest_move_h = lastest_move_img.size

        # Add latest move if the game was not won
        _, board_height = board_img.size
        latest_move_x = get_overlay_x(latest_move[0], latest_move[1], latest_move_w)
        latest_move_y = get_overlay_y(latest_move[0], latest_move[1], latest_move_h, board_height)
        board_img.paste(lastest_move_img, (latest_move_x, latest_move_y), lastest_move_img)

    return board_img


def add_won_overlay(board_img, winning_moves, theme='classic'):
    # Add latest move if the game was not won
    if winning_moves:
        _, board_height = board_img.size
        # If the game is won, then mark each spot
        won_img = Image.open(f"assets/{theme}/won.png")
        # Get unique winning cells
        unique_winning_moves = set()
        for win in winning_moves:
            for cell in win:
                unique_winning_moves.add(cell)

        for move in unique_winning_moves:
            won_x = get_overlay_x(move[0], move[1], won_img.size[0])
            won_y = get_overlay_y(move[0], move[1], won_img.size[1], board_height)
            board_img.paste(won_img, (won_x, won_y), won_img)

    return board_img


def render_board(board, theme='classic'):
    board_img = Image.open(f"assets/{theme}/board.png")
    _, board_height = board_img.size
    player1_piece = Image.open(f"assets/{theme}/player1.png")
    player2_piece = Image.open(f"assets/{theme}/player2.png")

    for row_idx, row in enumerate(board):
        for col_idx, piece in enumerate(row):
            if piece != 0:
                piece_x = get_piece_x(row_idx, col_idx)
                piece_y = get_piece_y(row_idx, col_idx, board_height)
                # Add players piece
                player_piece = player1_piece if piece == 1 else player2_piece
                board_img.paste(player_piece, (piece_x, piece_y), player_piece)

    return board_img


def save_render(board_img, board_name):
    file_key = f"{board_name}.png"
    s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
    with tempfile.NamedTemporaryFile() as tmp:
        board_img.save(tmp.name, format='png')
        s3.upload_file(tmp.name,
                       os.environ['RENDERED_IMAGES_BUCKET'],
                       file_key,
                       ExtraArgs={'ContentType': 'image/png'})

    return f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/{file_key}"
