import os
import copy
import time
import json
import uuid
import boto3

import utils as core_utils
import connect4.exceptions
import connect4.utils as connect4_utils


class Connect4:

    def __init__(self, player1_id, player2_id, team_id, channel_id, theme='classic'):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.team_id = team_id
        self.channel_id = channel_id
        self.pieces = {
            self.player1_id: 1,
            self.player2_id: 2,
        }
        self.theme = theme
        self.game_id = str(uuid.uuid4())
        self.game_history = {
            'platform': 'slack',
            'game_id': self.game_id,
            'start_time': core_utils.get_ts(),
            'end_time': None,
            'theme': theme,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'team_id': self.team_id,
            'channel_id': self.channel_id,
            # Url to the finial rendered gif of all moves played
            'recap_url': None,
            # None-game not done; 0-tie; 1-player 1 won; 2-player2 won
            'game_state': None,
            'moves': [
                # Example of whats in a move
                # {
                #     'player': 1,
                #     'latest_move': (6, 2),
                #     'board': [[0, 0, 0],[0, 0, 0],[0, 0, 0]] ...,
                #     'rendered_board_url': 'https://...',
                #     'timestamp': '...',
                # }
            ],
        }

        self.s3_root_folder = f"connect4/slack/{self.team_id}"

        self.latest_move = (None, None)
        self.current_player = self.player1_id
        self.board = connect4_utils.gen_new_board()
        self.winning_moves = None

    def start(self, player1_name, player2_name):
        banner_url = self.render_player_banner(player1_name, player2_name)
        board_url = self.render_board()
        self.game_history['moves'].append(
            {
                'player': 0,
                'piece_played': (None, None),
                'board': copy.deepcopy(self.board),
                'rendered_board_url': board_url,
                'timestamp': core_utils.get_ts(),
            }
        )
        return banner_url, board_url

    def render_board_str(self):
        # Not used in prod, but useful for testing in terminal
        rendered_board = ''
        for row in self.board:
            for col in row:
                rendered_board += f'{col}    '
            rendered_board += '\n'
        return rendered_board

    def render_board(self):
        board_name = f"{self.s3_root_folder}/{self.game_id}_{time.time()}"
        board_img = connect4_utils.render_board(self.board, theme=self.theme)
        # Only render the last more OR the winning pieces
        if not self.winning_moves:
            board_img = connect4_utils.add_lastest_move_overlay(board_img, self.latest_move, theme=self.theme)
        else:
            board_img = connect4_utils.add_won_overlay(board_img, self.winning_moves, theme=self.theme)
        return core_utils.save_render(board_img, board_name)

    def render_player_banner(self, player1_name, player2_name):
        name_prefix = f"{self.s3_root_folder}/{self.game_id}"
        return connect4_utils.render_player_banner(player1_name,
                                                   player2_name,
                                                   name_prefix,
                                                   theme=self.theme)

    def toggle_player(self):
        self.current_player = self.player1_id if self.current_player == self.player2_id else self.player2_id

    def parse_column_and_player(self, action):
        column = int(action['actions'][0]['value'])
        player = action['user']['id']

        # Is it that users turn
        if player != self.current_player:
            raise connect4.exceptions.NotYourTurn

        return column, player

    def place_piece(self, column, player):
        self.board, self.latest_move = connect4_utils.place_piece(self.board, column, self.pieces[player])

        game_end = None
        self.winning_moves = connect4_utils.check_win(self.board, column)
        if self.winning_moves:
            game_end = 'win'
            self.game_history['game_state'] = self.pieces[self.current_player]

        elif connect4_utils.check_tie(self.board):
            game_end = 'tie'
            self.game_history['game_state'] = 0

        board_url = self.render_board()
        # Save the players move before game_over gets called and the player is toggled
        self.game_history['moves'].append(
            {
                'player': self.pieces[self.current_player],
                'piece_played': self.latest_move,
                'board': copy.deepcopy(self.board),
                'rendered_board_url': board_url,
                'timestamp': core_utils.get_ts(),
            }
        )

        if game_end is None:
            # Only toggle the player if game has not ended
            self.toggle_player()

        return board_url, game_end

    def _generate_recap(self, moves):
        s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
        frame_urls = []
        for idx, move in enumerate(moves, start=1):
            frame_urls.append(move['rendered_board_url'])

        recap_name = f"{self.s3_root_folder}/{self.game_id}_recap.gif"
        recap_url = connect4_utils.generate_recap(frame_urls, recap_name)

        # Remove un-needed boards from s3
        # Do not delete the very last image
        for frame_url in frame_urls[:-1]:
            s3.delete_object(Bucket=os.environ['RENDERED_IMAGES_BUCKET'],
                             Key=f"{self.s3_root_folder}/{frame_url.split('/')[-1]}")

        return recap_url

    def game_over(self):
        self.game_history['end_time'] = core_utils.get_ts()

        recap_url = self._generate_recap(self.game_history['moves'])

        self.game_history['recap_url'] = recap_url
        s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT', None))
        s3.put_object(Body=json.dumps(self.game_history).encode('utf-8'),
                      Bucket=os.environ['GAME_HISTORY_BUCKET'],
                      Key=f"{self.s3_root_folder}/{self.game_id}_history.json",
                      ContentType='application/json')

        return recap_url
