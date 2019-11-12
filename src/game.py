import utils
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
        self.win = False

        self.board = utils.gen_new_board()

    def render_board_str(self):
        # Not used in prod, but useful for testing in terminal
        rendered_board = ''
        for row in self.board:
            for col in row:
                rendered_board += f'{col}    '
            rendered_board += '\n'
        return rendered_board

    def render_board(self, board_name, winning_moves=None):
        board_img = utils.render_board(self.board, theme=self.theme)
        # Only render the last more OR the winning pieces
        if winning_moves is None:
            board_img = utils.add_lastest_move_overlay(board_img, self.latest_move, theme=self.theme)
        else:
            board_img = utils.add_won_overlay(board_img, winning_moves, theme=self.theme)
        return utils.save_render(board_img, board_name)

    def render_player_banner(self, player1_name, player2_name, board_id):
        return utils.render_player_banner(player1_name,
                                          player2_name,
                                          board_id,
                                          theme=self.theme)

    def toggle_player(self):
        self.turn = self.player1_id if self.turn == self.player2_id else self.player2_id

    def get_column_and_player(self, action):
        column = int(action['actions'][0]['value'])
        player = action['user']['id']

        # Is it that users turn
        if player != self.turn:
            raise exceptions.NotYourTurn

        return column, player

    def place_piece(self, column, player):
        self.board, self.latest_move = utils.place_piece(self.board, column, self.pieces[player])

    def check_win(self, column):
        self.win = utils.check_win(self.board, column)
        return self.win

    def check_tie(self):
        return utils.check_tie(self.board)
