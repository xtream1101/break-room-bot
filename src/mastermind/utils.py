import os
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import mastermind.exceptions


def get_theme_list():
    return list(os.walk('mastermind/assets'))[0][1]


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


def get_sample_theme_blocks():
    samples = []
    for theme in get_theme_list():
        try:
            with open(os.path.join('mastermind', 'assets', theme, 'about.txt'), 'r') as f:
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
                "image_url": f"{os.getenv('S3_ENDPOINT', 'https://s3.amazonaws.com')}/{os.environ['RENDERED_IMAGES_BUCKET']}/mastermind/themes/sample-{theme}.png",  # noqa:E501
                "alt_text": theme
            }
        })
    return samples


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


def render_board(board, theme='classic'):
    # TODO: Make dynamic. Currently only works with 4 holes, 6 colors, and 10 guesses
    # TODO: Make more efficient. Currently has to re render the full board each time
    #       (use last board and just add/remove whats needed?)
    hole_img = Image.open(f"mastermind/assets/{theme}/hole.png")
    hole_width, hole_height = hole_img.size

    # Create a 2 x 2 key image
    empty_feedback_img = Image.new("RGBA", (hole_width, hole_height), (255, 255, 255))
    small_hole_width = int(hole_width / 2)
    small_hole_height = int(hole_height / 2)
    small_hole_img = hole_img.resize((small_hole_width, small_hole_height), Image.ANTIALIAS)
    empty_feedback_img.paste(small_hole_img, (0, 0), small_hole_img)
    empty_feedback_img.paste(small_hole_img, (0, small_hole_height), small_hole_img)
    empty_feedback_img.paste(small_hole_img, (small_hole_width, 0), small_hole_img)
    empty_feedback_img.paste(small_hole_img, (small_hole_width, small_hole_height), small_hole_img)

    # Create row with 1 key and 4 holes
    empty_row_img = Image.new("RGBA", (hole_width * 5, hole_height), (255, 255, 255))
    empty_row_img.paste(empty_feedback_img, (0, 0), empty_feedback_img)
    empty_row_img.paste(hole_img, (hole_width * 1, 0), hole_img)
    empty_row_img.paste(hole_img, (hole_width * 2, 0), hole_img)
    empty_row_img.paste(hole_img, (hole_width * 3, 0), hole_img)
    empty_row_img.paste(hole_img, (hole_width * 4, 0), hole_img)

    # Create full empty game board
    row_sep_img = Image.open(f"mastermind/assets/{theme}/row_sep.png")
    sep_height = row_sep_img.size[1]
    row_width, row_height = empty_row_img.size
    board_height = (row_height * len(board['public'])) + (sep_height * (len(board['public']) - 1))
    empty_board_img = Image.new("RGBA", (row_width, board_height), (255, 255, 255))
    for i in range(0, len(board['public'])):
        paste_y = (row_height * i) + (sep_height * i)
        if i != 0:
            # Do not do on the last one
            for j in range(0, len(board['public'][0][0]) + 1):
                empty_board_img.paste(
                    row_sep_img,
                    (hole_width * j, paste_y - 2)
                )
        empty_board_img.paste(
            empty_row_img,
            (0, paste_y),
            empty_row_img
        )

    feedback_img = {
        'w': Image.open(f"mastermind/assets/{theme}/peg-w.png").resize((small_hole_width, small_hole_height), Image.ANTIALIAS),  # noqa: E501
        'b': Image.open(f"mastermind/assets/{theme}/peg-b.png").resize((small_hole_width, small_hole_height), Image.ANTIALIAS),  # noqa: E501
    }
    peg_img = {
        0: Image.open(f"mastermind/assets/{theme}/peg-0.png"),
        1: Image.open(f"mastermind/assets/{theme}/peg-1.png"),
        2: Image.open(f"mastermind/assets/{theme}/peg-2.png"),
        3: Image.open(f"mastermind/assets/{theme}/peg-3.png"),
        4: Image.open(f"mastermind/assets/{theme}/peg-4.png"),
        5: Image.open(f"mastermind/assets/{theme}/peg-5.png"),
    }
    fb_rel_location = [
        (0, 0),
        (0, small_hole_height),
        (small_hole_width, 0),
        (small_hole_width, small_hole_height),
    ]
    # Add pegs to board, row by row
    for row_idx, row in enumerate(board['public'][::-1]):
        # Add feedback
        row_y = (row_height * row_idx) + (sep_height * row_idx)
        for fb_idx, fb in enumerate(row[1][0]):
            if fb is not None:
                empty_board_img.paste(
                    feedback_img[fb],
                    (fb_rel_location[fb_idx][0], fb_rel_location[fb_idx][1] + row_y),
                    feedback_img[fb]
                )

        # Add players guess
        for peg_idx, peg in enumerate(row[0], start=1):
            if peg is not None:
                empty_board_img.paste(
                    peg_img[peg],
                    (peg_idx * hole_width, row_y),
                    peg_img[peg]
                )

    return empty_board_img
