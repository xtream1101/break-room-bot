import uuid
import utils
import datetime
import exceptions


class Connect4:
    def __init__(self, player1_id, player2_id, theme='classic'):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.pieces = {
            self.player1_id: 1,
            self.player2_id: 2,
        }
        self.theme = theme

        self.latest_move = (None, None)
        self.turn = self.player1_id
        self.game_id = str(uuid.uuid4())
        self.board = utils.gen_new_board()
        self.winning_moves = None

    def render_board_str(self):
        # Not used in prod, but useful for testing in terminal
        rendered_board = ''
        for row in self.board:
            for col in row:
                rendered_board += f'{col}    '
            rendered_board += '\n'
        return rendered_board

    def render_board(self, board_name):
        board_img = utils.render_board(self.board, theme=self.theme)
        # Only render the last more OR the winning pieces
        if self.winning_moves is None:
            board_img = utils.add_lastest_move_overlay(board_img, self.latest_move, theme=self.theme)
        else:
            board_img = utils.add_won_overlay(board_img, self.winning_moves, theme=self.theme)
        return utils.save_render(board_img, board_name)

    def render_player_banner(self, player1_name, player2_name):
        return utils.render_player_banner(player1_name,
                                          player2_name,
                                          self.game_id,
                                          theme=self.theme)

    def toggle_player(self):
        self.turn = self.player1_id if self.turn == self.player2_id else self.player2_id

    def parse_column_and_player(self, action):
        column = int(action['actions'][0]['value'])
        player = action['user']['id']

        # Is it that users turn
        if player != self.turn:
            raise exceptions.NotYourTurn

        return column, player

    def place_piece(self, column, player):
        self.board, self.latest_move = utils.place_piece(self.board, column, self.pieces[player])

        game_end = None
        self.winning_moves = utils.check_win(self.board, column)
        if self.winning_moves:
            game_end = 'win'
        elif utils.check_tie(self.board):
            game_end = 'tie'
        else:
            # Only toggle the play if game has not ended
            self.toggle_player()

        # If game_end is not None, generate the gif and post

        return self.board, game_end

    def check_win(self, column):
        is_win = utils.check_win(self.board, column)
        return is_win

    def check_tie(self):
        is_tie = utils.check_tie(self.board)
        return is_tie
