import utils

themes = utils.get_theme_list()

sample_board = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 0, 0],
    [0, 2, 1, 2, 1, 0, 0],
    [0, 2, 2, 1, 1, 1, 2],
    [0, 1, 2, 1, 1, 2, 1],
    [0, 1, 2, 2, 2, 1, 1],
]
latest_move = (2, 2)
winning_moves = [
    [(2, 2), (3, 3,), (4, 4), (5, 5)]
]

# Render Samples
for theme in themes:
    board_img = utils.render_board(sample_board, theme=theme)
    board_img = utils.add_lastest_move_overlay(board_img, latest_move, theme=theme)
    board_img = utils.add_won_overlay(board_img, winning_moves, theme=theme)
    board_name = f"sample-{theme}"
    utils.save_render(board_img, board_name)
