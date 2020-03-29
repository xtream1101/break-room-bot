import utils as core_utils
import mastermind.utils as mastermind_utils


# Only use a few rows, otherwise the sample preview does not display well
sample_board = {
    'private': [1, 5, 2, 0],
    'public': [
        [[3, 1, 4, 5], [['w', 'w', None, None], 1]],
        [[1, 4, 0, 2], [['b', 'w', 'w', None], 1]],
        [[1, 3, None, None], [[None, None, None, None], 0]],
        [[None, None, None, None], [[None, None, None, None], 0]],
        [[None, None, None, None], [[None, None, None, None], 0]],
    ]
}

# Render Samples
themes = mastermind_utils.get_theme_list()
for theme in themes:
    board_img = mastermind_utils.render_board(sample_board, theme=theme)
    # board_img = mastermind_utils.add_lastest_move_overlay(board_img, latest_move, theme=theme)
    # board_img = mastermind_utils.add_won_overlay(board_img, winning_moves, theme=theme)
    board_name = f"mastermind/themes/sample-{theme}"
    print(core_utils.save_render(board_img, board_name))
