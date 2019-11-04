import os
import uuid
import time
import json
import redis
import falcon
import pickle
import requests
import exceptions
import urllib.parse
from pprint import pprint
from game import Connect4


r_connect4 = redis.Redis(host=os.environ['REDIS_HOST'],
                         password=os.environ['REDIS_PASSWORD'])
BASE_URL = os.environ['BASE_URL']

message_content = [
    {
        "type": "image",
        "image_url": "",
        "alt_text": "Game Board"
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "1"
                },
                "value": "1"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "2"
                },
                "value": "2"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "3"
                },
                "value": "3"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "4"
                },
                "value": "4"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "5"
                },
                "value": "5"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "6"
                },
                "value": "6"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "7"
                },
                "value": "7"
            }
        ]
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ""
            }
        ]
    }
]


class SlackConnect4:
    def on_post(self, req, resp):
        data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))
        board_id = str(uuid.uuid4())
        player1 = data['user_id'][0]
        player2 = data['text'][0].split('|')[0].split('@')[-1]  # TODO: validate this is a user (at least the format)
        # TODO: Make sure you are not playing with yourself
        current_game = Connect4(player1, player2)
        r_connect4.set(board_id, pickle.dumps(current_game))
        current_game.render_board(board_id)
        message_content[0]['image_url'] = f"{BASE_URL}/slack/connect4/board/{board_id}.png"

        message_content[1]['block_id'] = board_id
        message_content[-1]['elements'][0]['text'] = f"<@{current_game.turn}>'s Turn"
        game = {'response_type': 'in_channel',
                'blocks': message_content,
            }
        resp.media = game


class SlackConnect4Button:
    def on_post(self, req, resp):
        data = urllib.parse.unquote(req.stream.read().decode('utf-8'))
        action_details = json.loads(data.replace('payload=', ''))

        board_id = action_details['message']['blocks'][1]['block_id']
        current_game = pickle.loads(r_connect4.get(board_id))
        try:
            column, player = current_game.get_column_and_player(action_details)
            current_game.place_piece(column, player)
        except exceptions.NotYourTurn:
            pass
        else:
            # TODO: also check for tie
            if current_game.check_win(column):
                # The current player won, disable buttons and make it known
                action_details['message']['blocks'].pop(1)
                action_details['message']['blocks'][-1]['elements'][0]['text'] = f"<@{current_game.turn}> WON!!!"
            else:
                current_game.toggle_player()
                action_details['message']['blocks'][-1]['elements'][0]['text'] = f"<@{current_game.turn}>'s Turn"

            board_name = f"{board_id}-{time.time()}"
            current_game.render_board(board_name)
            new_image = {
                "type": "image",
                "image_url": f"{BASE_URL}/slack/connect4/board/{board_name}.png",
                "alt_text": "Game Board",
            }
            action_details['message']['blocks'][0] = new_image
            r_connect4.set(board_id, pickle.dumps(current_game))
            r = requests.post(action_details['response_url'], json=action_details['message'])
            print(r.text)


class Ping:
    def on_get(self, req, resp):
        resp.media = {'response': 'pong2'}

api = falcon.API()
api.add_route('/ping', Ping())
api.add_route('/slack/connect4', SlackConnect4())
api.add_route('/slack/connect4/button', SlackConnect4Button())
api.add_static_route('/slack/connect4/board', '/src/board_img_cache')  # TODO: make path dynamic
