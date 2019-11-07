import os
import uuid
import time
import json
import boto3
import redis
import falcon
import pickle
import requests
import exceptions
import urllib.parse
from game import Connect4


r_connect4 = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'),
                         password=os.getenv('REDIS_PASSWORD', ''))

default_message_blocks = [
    {"type": "section", "text": {"type": "mrkdwn", "text": ""}},
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
    {"type": "context", "elements": [{"type": "mrkdwn", "text": "This slackbot was created by Eddy Hintze"}]}
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

        default_message_blocks[0]['text']['text'] = f"Connect4 game between <@{player1}> (red) & <@{player2}> (yellow)"

        board_url = current_game.render_board(board_id)
        print(board_url)
        default_message_blocks[1]['image_url'] = board_url

        default_message_blocks[0]['block_id'] = board_id
        default_message_blocks[-2]['text']['text'] = f"<@{current_game.turn}>'s Turn"

        resp.media = {'response_type': 'in_channel', 'blocks': default_message_blocks}


class SlackConnect4Button:
    def on_post(self, req, resp):
        data = urllib.parse.unquote(req.stream.read().decode('utf-8'))
        action_details = json.loads(data.replace('payload=', ''))
        blocks = action_details['message']['blocks']

        board_id = blocks[0]['block_id']
        current_game = pickle.loads(r_connect4.get(board_id))
        try:
            column, player = current_game.get_column_and_player(action_details)
            current_game.place_piece(column, player)
        except exceptions.NotYourTurn:
            pass
        else:
            winning_moves = current_game.check_win(column)
            if winning_moves:
                # The current player won, disable buttons and make it known
                blocks.pop(2)
                blocks[-2]['text']['text'] = f"<@{current_game.turn}> WON!!!"
                r_connect4.delete(board_id)
            elif current_game.check_tie():
                blocks.pop(2)
                blocks[-2]['text']['text'] = f"It's a Tie!"
                r_connect4.delete(board_id)
            else:
                current_game.toggle_player()
                blocks[-2]['text']['text'] = f"<@{current_game.turn}>'s Turn"

            board_name = f"{board_id}-{time.time()}"
            board_url = current_game.render_board(board_name, winning_moves=winning_moves)

            # Better to create a new block because the one returned has data that breaks the api if returned
            old_game_board_img = blocks[1]['image_url'].split('/')[-1]
            new_image = default_message_blocks[1].copy()
            new_image["image_url"] = board_url
            blocks[1] = new_image

            # Fix formating of some messages
            blocks[0]['text']['text'] = blocks[0]['text']['text'].replace('+', ' ')
            blocks[-1]['elements'][0]['text'] = blocks[-1]['elements'][0]['text'].replace('+', ' ')
            r = requests.post(action_details['response_url'], json=action_details['message'])

            if r.json().get('ok') is True:
                if r_connect4.exists(board_id):
                    # only save game status if updating slack was successful and game is still playable
                    r_connect4.set(board_id, pickle.dumps(current_game))
                try:
                    s3 = boto3.resource('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
                    s3.Object(os.environ['RENDERED_IMAGES_BUCKET'], old_game_board_img.split('/')[-1]).delete()
                    # os.remove(os.path.join(os.environ['RENDERED_IMAGES'], old_game_board_img))
                except Exception as e:
                    print(str(e))
                    pass
            else:
                print(json.dumps(blocks))
                print(r.text)


class Healthcheck:
    def on_get(self, req, resp):
        resp.media = {'success': True}


api = falcon.API()
api.add_route('/healthcheck', Healthcheck())
api.add_route('/slack/connect4', SlackConnect4())
api.add_route('/slack/connect4/button', SlackConnect4Button())
