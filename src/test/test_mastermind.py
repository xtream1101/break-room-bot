import pytest
import mastermind.utils
import mastermind.exceptions


def test_gen_new_board():
    board = mastermind.utils.gen_new_board(holes=4, colors=6, guesses=3)
    public_board = [
        [[None, None, None, None], [[None, None, None, None], 0]],
        [[None, None, None, None], [[None, None, None, None], 0]],
        [[None, None, None, None], [[None, None, None, None], 0]],
    ]
    assert len(board['private']) == 4
    assert board['public'] == public_board


@pytest.mark.parametrize('current_public_board, expected', [
    ({'public': [[[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]}, 0),
    ({'public': [[[2, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]}, 0),
    ({'public': [[[2, 3], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]}, 0),
    ({'public': [[[2, 3], [[None, None], 1]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]}, 1),
    ({'public': [[[2, 3], [[None, None], 1]],
                 [[3, 3], [[None, None], 1]],
                 [[1, 2], [[0, None], 1]]]}, None),
])
def test_find_guess_index(current_public_board, expected):
    assert mastermind.utils._find_guess_index(current_public_board) == expected


@pytest.mark.parametrize('current_public_board, color, expected_public_board, expected_game_state', [
    ({'private': [1, 2],
      'public': [[[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     3,
     {'private': [1, 2],
      'public': [[[3, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     None),
    ({'private': [1, 2],
      'public': [[[0, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     3,
     {'private': [1, 2],
      'public': [[[0, 3], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     None),
    ({'private': [1, 2],
      'public': [[[0, 4], [[None, None], 1]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     3,
     {'private': [1, 2],
      'public': [[[0, 4], [[None, None], 1]],
                 [[3, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     None),
    ({'private': [1, 2],
      'public': [[[0, 3], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     -1,
     {'private': [1, 2],
      'public': [[[0, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     None),
    ({'private': [1, 2],
      'public': [[[1, 2], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     -2,
     {'private': [1, 2],
      'public': [[[1, 2], [['b', 'b'], 1]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     1),
])
def test_making_valid_move(current_public_board, color, expected_public_board, expected_game_state):
    new_board, game_state = mastermind.utils.make_move(current_public_board, color)
    assert new_board == expected_public_board
    assert game_state == expected_game_state


@pytest.mark.parametrize('current_public_board, color, expected_exception', [
    ({'public': [[[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     -1, mastermind.exceptions.NothingToUndo),
    # ~~~~~~
    ({'public': [[[3, 2], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     0, mastermind.exceptions.MustSubmitGuess),
    # ~~~~~~
    ({'public': [[[3, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]],
                 [[None, None], [[None, None], 0]]]},
     -2, mastermind.exceptions.MustCompleteCode),
])
def test_making_invalid_move(current_public_board, color, expected_exception):
    with pytest.raises(expected_exception):
        mastermind.utils.make_move(current_public_board, color)


@pytest.mark.parametrize('key, code, expected_feedback', [
    ([1, 2, 3, 4], [1, 1, 2, 2], ['b', 'w', None, None]),
    ([1, 2, 2, 4], [1, 1, 2, 2], ['b', 'b', 'w', None]),
    ([1, 2, 2, 4], [1, 2, 3, 4], ['b', 'b', 'b', None]),
    ([1, 2, 3, 4], [1, 2, 3, 4], ['b', 'b', 'b', 'b']),
    ([1, 1, 2, 2], [3, 3, 4, 4], [None, None, None, None]),
])
def test_check_code(key, code, expected_feedback):
    feedback = mastermind.utils._check_code(key, code)
    assert feedback == expected_feedback
