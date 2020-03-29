import uuid
import time
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
        return self.render_board(), game_state
