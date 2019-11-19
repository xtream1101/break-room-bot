import os
import json
import boto3
import redis
import utils
import falcon
import pickle
import requests
import threading
import exceptions
import urllib.parse
from game import Connect4


BASE_URL = os.environ['BASE_URL']
r_connect4 = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'),
                         password=os.getenv('REDIS_PASSWORD', ''))

default_message_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
    {"type": "image",
     "title": {"type": "plain_text", "text": "Player Banner"},
     "image_url": "", "alt_text": "Player Banner"},
    {"type": "image", "image_url": "", "alt_text": "Game Board"},
    {
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "1"}, "value": "1"},
            {"type": "button", "text": {"type": "plain_text", "text": "2"}, "value": "2"},
            {"type": "button", "text": {"type": "plain_text", "text": "3"}, "value": "3"},
            {"type": "button", "text": {"type": "plain_text", "text": "4"}, "value": "4"},
            {"type": "button", "text": {"type": "plain_text", "text": "5"}, "value": "5"},
            {"type": "button", "text": {"type": "plain_text", "text": "6"}, "value": "6"},
            {"type": "button", "text": {"type": "plain_text", "text": "7"}, "value": "7"}
        ]
    },
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
    {"type": "context", "elements": [
        {"type": "mrkdwn", "text": ("Created by Eddy Hintze.\n"
                                    "Game code can be found here https://github.com/xtream1101/connect4-slack")}
    ]}
]


class SlackConnect4OAuth:
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
                          Key=f"{oauth_resp['team_id']}.json",
                          ContentType='application/json')
            # Save to redis cache
            r_connect4.set(oauth_resp['team_id'], oauth_resp['access_token'])

            # TODO: Create better landing page
            resp.body = json.dumps({'message': 'Connect4 successfully installed'})
        except Exception:
            resp.body = json.dumps(oauth_resp)
        resp.status = falcon.HTTP_200


class SlackConnect4:
    def on_post(self, req, resp):
        data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))
        try:
            if data['text'][0].strip().lower() == 'themes':
                resp.media = {'response_type': 'in_channel', 'blocks': utils.get_sample_theme_blocks()}
                return

            # TODO: make a call to slack to get the display names, not the actual user names
            player1_id = data['user_id'][0]
            player1_name = data['user_name'][0]
            # TODO: validate this is a user (at least the format)
            player2_id, player2_name = data['text'][0].split('@')[-1].split('>')[0].split('|')
            # TODO: Allow you to play with yourself, current does not switch player correctly
            theme = 'classic'
            if len(data['text'][0].split(' ')) == 2:
                theme = data['text'][0].split(' ')[-1]

            if theme not in utils.get_theme_list():
                resp.media = {'text': f'The theme *{theme}* is not found'}
                return

            current_game = Connect4(player1_id, player2_id, theme=theme)
            r_connect4.set(current_game.game_id, pickle.dumps(current_game))

            header_message = f"<@{player1_id}> & <@{player2_id}>"
            default_message_blocks[0]['text']['text'] = header_message

            player_banner_url, board_url = current_game.start(player1_name, player2_name)
            default_message_blocks[1]['image_url'] = player_banner_url
            default_message_blocks[2]['image_url'] = board_url

            default_message_blocks[0]['block_id'] = current_game.game_id
            default_message_blocks[-2]['text']['text'] = f"<@{current_game.current_player}>'s Turn"
        except Exception as e:
            print(str(e))
            resp.media = {'text': '''*Usage:*
To list Themes:
\t `/connect4 themes`
Start a game:
\t`/connect4 @user ThemeName`
\t\t`@user` is who to play with
\t\t`ThemeName` is for a custom theme, if not passed in "Classic" will be used
            '''}
        else:
            resp.media = {'response_type': 'in_channel', 'blocks': default_message_blocks}


class SlackConnect4Button:
    def on_post(self, req, resp):
        data = urllib.parse.unquote(req.stream.read().decode('utf-8'))
        action_details = json.loads(data.replace('payload=', ''))
        blocks = action_details['message']['blocks']

        game_id = blocks[0]['block_id']
        current_game = pickle.loads(r_connect4.get(game_id))
        try:
            column, player = current_game.parse_column_and_player(action_details)
            board_url, game_state = current_game.place_piece(column, player)
        except (exceptions.NotYourTurn, exceptions.ColumnFull):
            pass
        else:
            if game_state is not None:
                # Game is over
                # Generate recap in thread to post when ready
                t = threading.Thread(target=generate_recap,
                                     args=(current_game,
                                           action_details))
                t.daemon = True
                t.start()

                blocks.pop(-3)  # Remove buttons
                r_connect4.delete(game_id)  # Clear from cache

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
            blocks[-1]['elements'][0]['text'] = blocks[-1]['elements'][0]['text'].replace('+', ' ')
            # Clean up image fields auto added by slack that cannot be posted when updating the message
            del blocks[1]['image_width']
            del blocks[1]['image_height']
            del blocks[1]['image_bytes']
            del blocks[1]['fallback']

            r = requests.post(action_details['response_url'], json=action_details['message'])
            if r.json().get('ok') is True:
                if r_connect4.exists(game_id):
                    # only save game status if updating slack was successful and game is still playable
                    r_connect4.set(game_id, pickle.dumps(current_game))
            else:
                print(json.dumps(blocks))
                print(r.text)


class Healthcheck:
    def on_get(self, req, resp):
        resp.media = {'success': True}


def get_access_token(team_id):
    try:
        access_token = r_connect4.get(team_id).decode('utf-8')
    except AttributeError:
        # Load in from s3 and save into redis cache
        s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
        file_content = s3.get_object(Bucket=os.environ['OAUTH_BUCKET'],
                                     Key=f"{team_id}.json")['Body'].read().decode('utf-8')
        access_token = json.loads(file_content)['access_token']
        r_connect4.set(team_id, access_token)

    return access_token


def generate_recap(game, action_details):
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


api = falcon.API()
api.add_route('/healthcheck', Healthcheck())
api.add_route('/slack/connect4', SlackConnect4())
api.add_route('/slack/oauth', SlackConnect4OAuth())
api.add_route('/slack/connect4/button', SlackConnect4Button())
asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
api.add_static_route('/slack/connect4/assets', asset_path)
