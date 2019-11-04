import utils
import exceptions


class Connect4:
    def __init__(self, player1_id, player2_id):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.pieces = {
            self.player1_id: 1,
            self.player2_id: 2,
        }

        self.turn = self.player1_id

        self.board = utils.gen_new_board()

    def render_board_str(self):
        rendered_board = ''
        for row in self.board:
            for col in row:
                rendered_board += f'{col}    '
            rendered_board += '\n'
        return rendered_board

    def render_board(self, board_id):
        utils.render_board(self.board, board_id)

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
        self.board = utils.place_piece(self.board, column, self.pieces[player])

    def check_win(self, column):
        return utils.check_win(self.board, column)

    def check_tie(self):
        return utils.check_tie(self.board)
