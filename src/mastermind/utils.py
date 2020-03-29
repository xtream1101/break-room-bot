import os
import boto3
import random
import os.path
import tempfile
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import mastermind.exceptions


def gen_new_board(holes=4, colors=6, guesses=10):
    colors = list(range(6))
    random.shuffle(colors)
    game_board = {
        'private': colors[:holes],
        # First set of holes is the players guess
        # Second set of holes is the feedback, and if the feedback is complete
        # feedback complete is needed because the player could have no feedback
        'public':  [[[None] * holes, [[None] * holes, 0]] for i in range(guesses)]
    }
    return game_board


def make_move(board, move):
    """Player picks a color/action

    if color is -1, then remove last move, as long as guess has not been submitted
    if color is -2, then submit code for feedback

    Args:
        board (dict): Mastermind game board data
        color (int): an int of the color chosen

    Returns:
        dict: Mastermind game board data
    """
    game_state = None
    guess_idx = _find_guess_index(board)
    if move == -1:
        # Undo last move
        try:
            last_played_idx = board['public'][guess_idx][0].index(None) - 1
        except ValueError:
            last_played_idx = len(board['public'][guess_idx][0]) - 1
        if last_played_idx < 0:
            raise mastermind.exceptions.NothingToUndo("Nothing to undo in the current code")
        board['public'][guess_idx][0][last_played_idx] = None

    elif move == -2:
        # Submit code for feedback
        if None in board['public'][guess_idx][0]:
            raise mastermind.exceptions.MustCompleteCode("Complete code before submitting")

        feedback = _check_code(board['private'], board['public'][guess_idx][0])
        board['public'][guess_idx][1][0] = feedback
        board['public'][guess_idx][1][1] = 1

        # Check game state
        if set(feedback) == set('b'):
            # Code matches, Game has been won
            game_state = 1
        elif guess_idx + 1 == len(board['public']):
            # Game lost, no more guesses left
            game_state = 0

    else:
        try:
            empty_hole_idx = board['public'][guess_idx][0].index(None)
        except ValueError:
            raise mastermind.exceptions.MustSubmitGuess("No more holes to play in. Submit your guess")
        board['public'][guess_idx][0][empty_hole_idx] = move

    return board, game_state


def _check_code(key, code):
    feedback = []
    modified_key = key.copy()
    modified_code = code.copy()
    # Check right color, right postion (black)
    for idx, val in enumerate(zip(key.copy(), code.copy())):
        if val[0] == val[1]:
            modified_key.remove(val[0])
            modified_code.remove(val[0])
            feedback.append('b')

    # Check for right color wrong spot (white)
    for c in modified_key:
        if c in modified_code:
            feedback.append('w')
            modified_code.remove(c)

    # Fill rest of feedback with None
    feedback += [None] * (len(code) - len(feedback))

    return feedback


def _find_guess_index(board):
    for idx, row in enumerate(board['public']):
        if row[1][1] == 0:
            return idx


def render_board_str(board, theme='classic'):
    image = Image.new("RGBA", (600, 400), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Lato-Bold.ttf", 16)

    plays = ''
    for play in board['public']:
        plays += ', '.join(str(x) for x in play[0])
        plays += '    -    '
        plays += ', '.join(str(x) for x in play[1][0])
        plays += '\n'

    board_str = f"""
Game Board
{', '.join(str(x) for x in board['private'])}

{plays}
"""
    draw.text((10, 0), board_str, (0, 0, 0), font=font)

    return image


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


def get_theme_list():
    # TODO: place holder until we implement themes
    return ['classic']
