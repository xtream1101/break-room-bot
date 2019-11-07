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
        rendered_board = ''
        for row in self.board:
            for col in row:
                rendered_board += f'{col}    '
            rendered_board += '\n'
        return rendered_board

    def render_board(self, board_id, winning_moves=None):
        return utils.render_board(self.board, board_id,
                                  theme=self.theme,
                                  latest_move=self.latest_move,
                                  winning_moves=winning_moves)

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
