import os
import json
import boto3
import falcon
import pickle
import logging
import requests
import threading
import urllib.parse

import connect4.exceptions
from utils import redis_client
from connect4.game import Connect4
import connect4.utils as connect4_utils

logger = logging.getLogger()


connect4_help = '''*_Usage_*
> This help message
> \t `/connect4 help`
> To list Themes:
> \t `/connect4 themes`
> Start a game:
> \t`/connect4 @user ThemeName`
> \t\t`@user` is who to play with
> \t\t`ThemeName` is for a custom theme, if not passed in "Classic" will be used

*_Rules_*
> Try and get 4 of your color in a row
'''

default_message_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
    {"type": "image",
     "title": {"type": "plain_text", "text": "Player Banner"},
     "image_url": "",
     "alt_text": "Player Banner"},
    {"type": "image",
     "image_url": "",
     "title": {"type": "plain_text", "text": "Game Board"},
     "alt_text": "Game Board"},
    {
        "type": "actions",
        "elements": [
            {"type": "button", "action_id": "connect4-move-1", "text": {"type": "plain_text", "text": "1"}, "value": "1"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-2", "text": {"type": "plain_text", "text": "2"}, "value": "2"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-3", "text": {"type": "plain_text", "text": "3"}, "value": "3"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-4", "text": {"type": "plain_text", "text": "4"}, "value": "4"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-5", "text": {"type": "plain_text", "text": "5"}, "value": "5"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-6", "text": {"type": "plain_text", "text": "6"}, "value": "6"},  # noqa: E501
            {"type": "button", "action_id": "connect4-move-7", "text": {"type": "plain_text", "text": "7"}, "value": "7"}  # noqa: E501
        ]
    },
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
    {"type": "context", "elements": [
        {"type": "mrkdwn", "text": ("Created by Eddy Hintze.\n"
                                    "Game code can be found here https://github.com/xtream1101/break-room-bot")}
    ]}
]


class SlackOAuth:
    def on_get(self, req, resp):
        code = req.params['code']
        r = requests.post('https://slack.com/api/oauth.access',
                          data={'code': code,
                                'client_id': os.environ['SLACKBOT_CLIENT_ID'],
                                'client_secret': os.environ['SLACKBOT_CLIENT_SECRET'],
                                })
        oauth_resp = r.json()
        try:
            # Save to s3
            s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
            s3.put_object(Body=json.dumps(oauth_resp).encode('utf-8'),
                          Bucket=os.environ['OAUTH_BUCKET'],
                          Key=f"slack/{oauth_resp['team_id']}.json",
                          ContentType='application/json')
            # Save to redis cache
            redis_client.set(oauth_resp['team_id'], oauth_resp['access_token'])

            # TODO: Create better landing page
            resp.body = json.dumps({'message': 'Break Room successfully installed'})
        except Exception:
            resp.body = json.dumps(oauth_resp)
        resp.status = falcon.HTTP_200


class SlackConnect4:
    def on_post(self, req, resp):
        data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))
        try:
            # Display a help message just to the user
            if 'text' not in data or data['text'][0].strip().lower() == 'help':
                resp.media = {
                    'replace_original': True,
                    'text': connect4_help,
                }
                return

            # Display current themes to just the user
            if data['text'][0].strip().lower() == 'themes':
                resp.media = {
                    'replace_original': True,
                    'blocks': connect4_utils.get_sample_theme_blocks(),
                }
                return
            # TODO: make a call to slack to get the display names, not the actual user names
            player1_id, player1_name = data['user_id'][0], data['user_name'][0]
            player2_id, player2_name = data['text'][0].split('@')[-1].split('>')[0].split('|')
            # Do not let the user play against themselves
            if player1_id == player2_id:
                resp.media = {
                    'replace_original': True,
                    'text': 'You cannot play against yourself',
                }
                return

            theme = 'classic'
            if len(data['text'][0].split(' ')) == 2:
                theme = data['text'][0].split(' ')[-1]

            # Theme passed in does not exist
            if theme not in connect4_utils.get_theme_list():
                resp.media = {'text': f'The theme *{theme}* is not found'}
                return

            # Set up Connect4 game
            current_game = Connect4(player1_id,
                                    player2_id,
                                    data['team_id'][0],
                                    data['channel_id'][0],
                                    theme=theme)

            player_banner_url, board_url = current_game.start(player1_name, player2_name)
            redis_client.set(current_game.game_id, pickle.dumps(current_game))

            header_message = f"<@{player1_id}> & <@{player2_id}>"
            default_message_blocks[0]['text']['text'] = header_message

            default_message_blocks[1]['image_url'] = player_banner_url
            default_message_blocks[2]['image_url'] = board_url

            default_message_blocks[0]['block_id'] = current_game.game_id
            default_message_blocks[-2]['text']['text'] = f"<@{current_game.current_player}>'s Turn"

        except Exception:
            logger.exception("Failed to start connect4 game")
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


def slack_connect4_move(action_details):
    blocks = action_details['message']['blocks']

    game_id = blocks[0]['block_id']
    current_game = pickle.loads(redis_client.get(game_id))
    try:
        column, player = current_game.parse_column_and_player(action_details)
        board_url, game_state = current_game.place_piece(column, player)
    except (connect4.exceptions.NotYourTurn, connect4.exceptions.ColumnFull):
        pass
    else:
        if game_state is not None:
            # Game is over
            # Generate recap in thread to post when ready
            t = threading.Thread(target=connect4_utils.post_recap,
                                 args=(current_game,
                                       action_details))
            t.daemon = True
            t.start()

            blocks.pop(-3)  # Remove buttons
            redis_client.delete(game_id)  # Clear from cache

        msg_state = {'win': f"<@{current_game.current_player}> WON!!!",
                     'tie': f"It's a Tie!",
                     None: f"<@{current_game.current_player}>'s Turn",
                     }
        blocks[-2]['text']['text'] = msg_state.get(game_state, 'The game got into an invalid state.')
        # Better to create a new block because the one returned has data that breaks the api if returned
        new_image = default_message_blocks[2].copy()
        new_image["image_url"] = board_url
        blocks[2] = new_image

        # Fix formating of some messages
        blocks[0]['text']['text'] = blocks[0]['text']['text'].replace('+', ' ')
        blocks[1]['title']['text'] = blocks[1]['title']['text'].replace('+', ' ')
        blocks[2]['title']['text'] = blocks[2]['title']['text'].replace('+', ' ')
        blocks[-1]['elements'][0]['text'] = blocks[-1]['elements'][0]['text'].replace('+', ' ')
        # Clean up image fields auto added by slack that cannot be posted when updating the message
        del blocks[1]['image_width']
        del blocks[1]['image_height']
        del blocks[1]['image_bytes']
        del blocks[1]['fallback']

        r = requests.post(action_details['response_url'], json=action_details['message'])
        if r.json().get('ok') is True:
            if redis_client.exists(game_id):
                # only save game status if updating slack was successful and game is still playable
                redis_client.set(game_id, pickle.dumps(current_game))
        else:
            logger.error("Updating connect4 failed",
                         extra={
                             'game_id': game_id,
                             'platform': 'slack',
                             'blocks': blocks,
                             'response': r.text,
                         })
