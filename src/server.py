import json
import falcon
import urllib.parse

from connect4.endpoints import (
    SlackOAuth,
    SlackConnect4,
    slack_connect4_move,
    connect4_help
)

from mastermind.endpoints import (
    SlackMastermind,
    slack_mastermind_move,
    mastermind_help
)


class SlackInteractive:
    def on_post(self, req, resp):
        data = urllib.parse.unquote(req.stream.read().decode('utf-8'))
        action_details = json.loads(data.replace('payload=', ''))
        if action_details['actions'][0]['action_id'].startswith('connect4-move'):
            slack_connect4_move(action_details)
        elif action_details['actions'][0]['action_id'].startswith('mastermind-move'):
            slack_mastermind_move(action_details)


class BreakRoom:
    def on_post(self, req, resp):
        # data = urllib.parse.parse_qs(req.stream.read().decode('utf-8'))

        resp.media = {
            'replace_original': True,
            'text': f"""Welcome to the Break Room! Take a break and play a game in slack.
*Connect 4*
{connect4_help}

*Mastermind*
{mastermind_help}
""",
        }


class Healthcheck:
    def on_get(self, req, resp):
        resp.media = {'success': True}


api = falcon.API()
api.add_route('/healthcheck', Healthcheck())

api.add_route('/slack/breakroom', BreakRoom())
api.add_route('/slack/oauth', SlackOAuth())
api.add_route('/slack/interactive', SlackInteractive())
api.add_route('/slack/connect4', SlackConnect4())
api.add_route('/slack/mastermind', SlackMastermind())
