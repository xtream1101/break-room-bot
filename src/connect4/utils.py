import os
import io
import json
import boto3
import os.path
import datetime
import tempfile
import requests
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from pygifsicle import optimize

import connect4.exceptions
from utils import redis_client

PIECE_D = 50
PIECE_SPACE = 10


def get_ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def get_theme_list():
    return list(os.walk('connect4/assets'))[0][1]


def post_recap(game, action_details):
    recap_url = game.game_over()
    team_access_token = get_access_token(action_details['team']['id'])
    r = requests.post(
        'https://slack.com/api/chat.postMessage',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {team_access_token}",
        },
        json={
            'text': 'Game Recap',
            'blocks': [{"type": "image",
                        "image_url": recap_url,
                        "alt_text": "Game Recap"}],
            'channel': action_details['channel']['id'],
            'thread_ts': action_details['message']['ts'],
        })
    if r.json().get('ok') is False:
        print("Failed sending the recap", r.text)


def get_access_token(team_id):
    try:
        access_token = redis_client.get(team_id).decode('utf-8')
    except AttributeError:
        # Load in from s3 and save into redis cache
        s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
        file_content = s3.get_object(Bucket=os.environ['OAUTH_BUCKET'],
                                     Key=f"slack/{team_id}.json")['Body'].read().decode('utf-8')
        access_token = json.loads(file_content)['access_token']
        redis_client.set(team_id, access_token)

    return access_token


def generate_recap(frame_urls, recap_name):
    def gen_frame(url):
        # Source: https://stackoverflow.com/a/51219787
        im = Image.open(io.BytesIO(requests.get(url).content))
        alpha = im.getchannel('A')
        # Convert the image into P mode but only use 255 colors in the palette out of 256
        im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
        # Set all pixel values below 128 to 255 , and the rest to 0
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        # Paste the color of index 255 and use alpha as a mask
        im.paste(255, mask)
        # The transparency index is 255
        im.info['transparency'] = 255
        return im

    # Something is weird with the empty board png
    # So start 1 move in so all frames are transparent
    recap_gif = gen_frame(frame_urls[1])
    other_frames = []
    for frame_url in frame_urls[2:]:
        other_frames.append(gen_frame(frame_url))

    s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        filename = os.path.join(tmp_dir_name, 'recap.gif')
        recap_gif.save(filename,
                       format='gif',
                       save_all=True,
                       append_images=other_frames,
                       loop=0,
                       disposal=2,
                       duration=500)
        optimize(filename)
        s3.upload_file(filename,
                       os.environ['RENDERED_IMAGES_BUCKET'],
                       recap_name,
                       ExtraArgs={'ContentType': 'image/gif'})

    return f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/{recap_name}"


def get_sample_theme_blocks():
    samples = []
    for theme in get_theme_list():
        try:
            with open(os.path.join('connect4', 'assets', theme, 'about.txt'), 'r') as f:
                theme_about_text = f.read().strip()
        except FileNotFoundError:
            theme_about_text = ''

        samples.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Theme: *{theme}*\n{theme_about_text[:200]}"
            },
            "accessory": {
                "type": "image",
                "image_url": f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/connect4/themes/sample-{theme}.png",  # noqa:E501
                "alt_text": theme
            }
        })
    return samples


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
        raise connect4.exceptions.ColumnFull
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
    template = Image.open("connect4/assets/player_banner.png")
    player1_piece = Image.open(f"connect4/assets/{theme}/player1.png")
    player2_piece = Image.open(f"connect4/assets/{theme}/player2.png")

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
        try:
            lastest_move_img = Image.open(f"connect4/assets/{theme}/latest_move.png")
        except FileNotFoundError:
            return board_img

        latest_move_w, latest_move_h = lastest_move_img.size

        # Add latest move if the game was not won
        _, board_height = board_img.size
        latest_move_x = get_overlay_x(latest_move[0], latest_move[1], latest_move_w)
        latest_move_y = get_overlay_y(latest_move[0], latest_move[1], latest_move_h, board_height)
        board_img.paste(lastest_move_img, (latest_move_x, latest_move_y), lastest_move_img)

    return board_img


def add_won_overlay(board_img, winning_moves, theme='classic'):
    # If the game is won, then mark each spot
    if winning_moves:
        try:
            won_img = Image.open(f"connect4/assets/{theme}/won.png")
        except FileNotFoundError:
            return board_img

        _, board_height = board_img.size
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
    board_img = Image.open(f"connect4/assets/{theme}/board.png")
    _, board_height = board_img.size
    player1_piece = Image.open(f"connect4/assets/{theme}/player1.png")
    player2_piece = Image.open(f"connect4/assets/{theme}/player2.png")

    for row_idx, row in enumerate(board):
        for col_idx, piece in enumerate(row):
            if piece != 0:
                piece_x = get_piece_x(row_idx, col_idx)
                piece_y = get_piece_y(row_idx, col_idx, board_height)
                # Add players piece
                player_piece = player1_piece if piece == 1 else player2_piece
                board_img.paste(player_piece, (piece_x, piece_y), player_piece)

    return board_img


def save_render(board_img, board_name, ext='png'):
    # TODO: Auto get content type using lib
    content_type = {
        'png': 'image/png',
        'gif': 'image/gif',
    }
    file_key = f"{board_name}.{ext}"
    s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
    with tempfile.NamedTemporaryFile() as tmp:
        # TODO: Need to make this dynamic in order to support multiple formats
        board_img.save(tmp.name, format=ext)
        s3.upload_file(tmp.name,
                       os.environ['RENDERED_IMAGES_BUCKET'],
                       file_key,
                       ExtraArgs={'ContentType': content_type[ext]})

    return f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/{file_key}"
