import uuid
import json
import falcon
import requests
import exceptions
import urllib.parse
from pprint import pprint
from game import Connect4


message_content = [
	{
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": ""
		}
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


current_games = {}  # Track current games. TODO: Move to proper storage

class SlackConnect4:
    def on_post(self, req, resp):
        data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))
        new_game_id = str(uuid.uuid4())
        player1 = data['user_id'][0]
        player2 = data['text'][0].split('|')[0].split('@')[-1]  # TODO: validate this is a user (at least the format)
        # TODO: Make sure you are not playing with yourself
        current_games[new_game_id] = Connect4(player1, player2)
        message_content[0]['text']['text'] = current_games[new_game_id].render_board()

        message_content[-1]['elements'][0]['text'] = f"<@{current_games[new_game_id].turn}>'s Turn"
        message_content[0]['block_id'] = new_game_id
        game = {'response_type': 'in_channel',
                "blocks": message_content,
            }
        resp.media = game


class SlackConnect4Button:
    def on_post(self, req, resp):
        data = urllib.parse.unquote(req.stream.read().decode('utf-8'))
        action_details = json.loads(data.replace('payload=', ''))

        current_game = current_games[action_details['message']['blocks'][0]['block_id']]
        try:
            column, player = current_game.get_column_and_player(action_details)
            current_game.place_piece(column, player)
        except exceptions.NotYourTurn:
            pass
        else:
            # TODO: also check for tie
            pprint(current_game.board)
            action_details['message']['blocks'][0]['text']['text'] = current_game.render_board()
            if current_game.check_win(column):
                # The current player won, disable buttons and make it known
                action_details['message']['blocks'].pop(1)
                action_details['message']['blocks'][-1]['elements'][0]['text'] = f"<@{current_game.turn}> WON!!!"
            else:
                current_game.toggle_player()
                action_details['message']['blocks'][-1]['elements'][0]['text'] = f"<@{current_game.turn}>'s Turn"
            r = requests.post(action_details['response_url'], json=action_details['message'])



api = falcon.API()
api.add_route('/slack/connect4', SlackConnect4())
api.add_route('/slack/connect4/button', SlackConnect4Button())

