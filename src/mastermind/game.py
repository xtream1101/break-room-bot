import os
import uuid
import time
import json
import boto3
import mastermind.utils as mastermind_utils


class Mastermind:

    def __init__(self, player_id, player_name, team_id, channel_id, theme='classic'):
        self.player_id = player_id
        self.player_name = player_name
        self.team_id = team_id
        self.channel_id = channel_id
        self.theme = theme
        self.game_id = str(uuid.uuid4())
        self.num_holes = 4
        self.num_colors = 6
        self.num_guesses = 6

        self.s3_root_folder = f"mastermind/slack/{self.team_id}"

        self.board = mastermind_utils.gen_new_board(
            self.num_holes,
            self.num_colors,
            self.num_guesses,
        )

        self.game_history = {
            'platform': 'slack',
            'game_id': self.game_id,
            'start_time': mastermind_utils.get_ts(),
            'end_time': None,
            'theme': theme,
            'player_id': self.player_id,
            'team_id': self.team_id,
            'channel_id': self.channel_id,
            # None-game not done; 1-player won; 2-player lost
            'game_state': None,
            'num_colors': self.num_colors,
            'board': {},
        }

    def start(self):
        return self.render_board()

    def render_board(self):
        board_name = f"{self.s3_root_folder}/{self.game_id}_{time.time()}"
        board_img = mastermind_utils.render_board_str(self.board, theme=self.theme)
        return mastermind_utils.save_render(board_img, board_name)

    def parse_move(self, action):
        return int(action['actions'][0]['value'])

    def make_move(self, move):
        self.board, game_state = mastermind_utils.make_move(self.board, move)
        if game_state is not None:
            # Game over
            self.game_history['board'] = self.board
            self.game_history['game_state'] = game_state
            self.game_history['end_time'] = mastermind_utils.get_ts()
            s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
            s3.put_object(
                Body=json.dumps(self.game_history).encode('utf-8'),
                Bucket=os.environ['GAME_HISTORY_BUCKET'],
                Key=f"{self.s3_root_folder}/{self.game_id}_history.json",
                ContentType='application/json')

        return self.render_board(), game_state
