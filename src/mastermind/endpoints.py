import pickle
import logging
import requests
import urllib.parse

import mastermind.exceptions
from utils import redis_client
from mastermind.game import Mastermind
import mastermind.utils as mastermind_utils

logger = logging.getLogger()


mastermind_help = '''*Usage:*
To list Themes:
\t `/mastermind themes`
Start a game:
\t`/mastermind [ThemeName]`
\t\t`ThemeName` is for a custom theme, if not passed in "Classic" will be used
'''

default_message_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
    {"type": "image",
     "image_url": "",
     "title": {"type": "plain_text", "text": "Game Board"},
     "alt_text": "Game Board"},
    {
        "type": "actions",
        "elements": []  # Will fill with buttons based on the number of colors you are playing with
    },
    {"type": "context", "elements": [
        {"type": "mrkdwn", "text": ("Created by Eddy Hintze.\n"
                                    "Game code can be found here https://github.com/xtream1101/break-room-bot")}
    ]}
]


class SlackMastermind:
    def on_post(self, req, resp):
        data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))
        try:
            # Display a help message just to the user
            if 'text' in data and data['text'][0].strip().lower() == 'help':
                resp.media = {
                    'replace_original': True,
                    'text': mastermind_help,
                }
                return

            # TODO: make a call to slack to get the display names, not the actual user names
            player_id, player_name = data['user_id'][0], data['user_name'][0]
            theme = 'classic'
            if 'text' in data and len(data['text'][0].split(' ')) == 2:
                theme = data['text'][0].split(' ')[-1]

            # Theme passed in does not exist
            if theme not in mastermind_utils.get_theme_list():
                resp.media = {'text': f'The theme *{theme}* is not found'}
                return

            # Set up Connect4 game
            current_game = Mastermind(
                player_id,
                player_name,
                data['team_id'][0],
                data['channel_id'][0],
                theme=theme)

            board_url = current_game.start()
            redis_client.set(current_game.game_id, pickle.dumps(current_game))

            header_message = f"<@{player_id}>'s game"
            default_message_blocks[0]['text']['text'] = header_message
            default_message_blocks[1]['image_url'] = board_url

            default_message_blocks[0]['block_id'] = current_game.game_id

            # Add undo button
            default_message_blocks[2]['elements'].append(
                {"type": "button", "action_id": f"mastermind-move-undo", "text": {"type": "plain_text", "text": "Undo"}, "value": "-1"}  # noqa: E501
            )
            # Add color buttons
            for idx in range(current_game.num_colors):
                default_message_blocks[2]['elements'].append(
                    {"type": "button", "action_id": f"mastermind-move-{idx}", "text": {"type": "plain_text", "text": f"{idx}"}, "value": f"{idx}"}  # noqa: E501
                )
            # Add submit button
            default_message_blocks[2]['elements'].append(
                {"type": "button", "action_id": f"mastermind-move-submit", "text": {"type": "plain_text", "text": "Submit"}, "value": "-2"}  # noqa: E501
            )

        except Exception:
            logger.exception("Failed to start Mastermind game")
            resp.media = {
                'replace_original': True,
                'text': ('Something went wrong on our end, '
                         'if this keeps happening please create an issue in github'),
            }
        else:
            # Post the new game
            resp.media = {
                # 'replace_original': True,  # Does this even  work when using in_channel?
                'response_type': 'in_channel',
                'blocks': default_message_blocks,
            }


def slack_mastermind_move(action_details):
    blocks = action_details['message']['blocks']

    game_id = blocks[0]['block_id']
    current_game = pickle.loads(redis_client.get(game_id))
    color = current_game.parse_move(action_details)

    # Clear any warning messages from previous turns
    blocks[-1]['elements'] = [blocks[-1]['elements'][-1]]
    game_state = None
    try:
        board_url, game_state = current_game.make_move(color)
    except (mastermind.exceptions.MustSubmitGuess,
            mastermind.exceptions.NothingToUndo,
            mastermind.exceptions.MustCompleteCode) as e:
        blocks[-1]['elements'].insert(
            0,
            {"type": "mrkdwn", "text": f":red_circle: *{e}* :red_circle:"}
        )
        # Clean up image fields auto added by slack that cannot be posted when updating the message
        del blocks[1]['image_width']
        del blocks[1]['image_height']
        del blocks[1]['image_bytes']
        del blocks[1]['fallback']
    else:
        # Better to create a new block because the one returned has data that breaks the api if returned
        new_image = default_message_blocks[1].copy()
        new_image["image_url"] = board_url
        blocks[1] = new_image

    # TODO: Have these game state messages post the key as an image
    if game_state is not None:
        game_key = ', '.join(str(x) for x in current_game.board['private'])
        game_states = {
            0: f":disappointed: *You failed to guess the code of {game_key}!* :skull_and_crossbones:",
            1: f":tada: *You WON!!* :confetti_ball:"
        }
        # Remove buttons
        blocks.pop(2)
        # Display end game message
        blocks[-1]['elements'].insert(
            0,
            {"type": "mrkdwn", "text": game_states[game_state]}
        )

    # Fix formating of some messages
    blocks[0]['text']['text'] = blocks[0]['text']['text'].replace('+', ' ')
    blocks[1]['title']['text'] = blocks[1]['title']['text'].replace('+', ' ')
    for element in blocks[-1]['elements']:
        element['text'] = element['text'].replace('+', ' ')

    r = requests.post(action_details['response_url'], json=action_details['message'])
    if r.json().get('ok') is True:
        if redis_client.exists(game_id):
            # only save game status if updating slack was successful and game is still playable
            redis_client.set(game_id, pickle.dumps(current_game))
    else:
        logger.error("Updating mastermind failed",
                     extra={'game_id': game_id,
                            'platform': 'slack',
                            'blocks': blocks,
                            'response': r.text})
