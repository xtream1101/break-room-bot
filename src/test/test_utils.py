import pytest
from deepdiff import DeepDiff

import connect4.utils
import connect4.exceptions


def test_gen_new_board():
    board = connect4.utils.gen_new_board(rows=3, cols=4)

    test_board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    assert board == test_board


def test_place_piece__first_move():
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board, latest_move = connect4.utils.place_piece(board, 2, 1)
    test_board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ]
    test_latest_move = (2, 1)
    assert board == test_board
    assert latest_move == test_latest_move


def test_place_piece__second_move_on_first():
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ]
    board, latest_move = connect4.utils.place_piece(board, 2, 2)
    test_board = [
        [0, 0, 0, 0],
        [0, 2, 0, 0],
        [0, 1, 0, 0],
    ]
    test_latest_move = (1, 1)
    assert board == test_board
    assert latest_move == test_latest_move


def test_place_piece__column_full():
    board = [
        [0, 1, 0, 0],
        [0, 2, 0, 0],
        [0, 1, 0, 0],
    ]
    with pytest.raises(connect4.exceptions.ColumnFull):
        board, _ = connect4.utils.place_piece(board, 2, 2)


def test_check_win__bug_with_vertical():
    """The last move was the far right of the win
    Actual board that said player 1 won
    Issue: the diagonal was wraping around the top and comming up on the bottom
    """
    board = [
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 2, 2, 0],
        [0, 1, 2, 2, 1, 1, 0],
        [0, 1, 1, 1, 2, 2, 2],
        [0, 2, 1, 2, 1, 2, 1],
    ]
    assert connect4.utils.check_win(board, 2) == []


def test_check_win__horizontal_far_right():
    """The last move was the far right of the win
    """
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 2, 0],
        [0, 0, 2, 1, 1, 1, 1],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 7),
                    [[(5, 3), (5, 4), (5, 5), (5, 6)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__horizontal_far_left():
    """The last move was the far left of the win
    """
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 2, 0],
        [0, 0, 2, 1, 1, 1, 1],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 4),
                    [[(5, 3), (5, 4), (5, 5), (5, 6)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__horizontal_middle():
    """The last move was in the middle of the win
    """
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 2, 0],
        [0, 0, 2, 1, 1, 1, 1],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 5),
                    [[(5, 3), (5, 4), (5, 5), (5, 6)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__vertical():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 2, 0, 0, 0],
        [0, 1, 2, 2, 0, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 2),
                    [[(5, 1), (4, 1), (3, 1), (2, 1)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__lose_count_reset():
    """If count is not reset, then this will be a false win
    """
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0],
        [1, 1, 0, 2, 0, 0, 0],
        [2, 1, 2, 2, 2, 0, 0],
    ]
    assert connect4.utils.check_win(board, 2) == []


def test_check_win__diagonal_fwd_slash_far_right():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 5),
                    [[(5, 1), (4, 2), (3, 3), (2, 4)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__diagonal_fwd_slash_far_left():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 2),
                    [[(5, 1), (4, 2), (3, 3), (2, 4)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__diagonal_fwd_slash_middle():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 4),
                    [[(5, 1), (4, 2), (3, 3), (2, 4)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__diagonal_back_slash_far_right():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 5),
                    [[(1, 1), (2, 2), (3, 3), (4, 4)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__diagonal_back_slash_far_left():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 2),
                    [[(1, 1), (2, 2), (3, 3), (4, 4)]],
                    ignore_order=True)
    assert diff == {}


def test_check_win__diagonal_back_slash_middle():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    diff = DeepDiff(connect4.utils.check_win(board, 3),
                    [[(1, 1), (2, 2), (3, 3), (4, 4)]],
                    ignore_order=True)
    assert diff == {}
