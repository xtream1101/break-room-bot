import utils
import pytest
import exceptions


def test_gen_new_board():
    board = utils.gen_new_board(rows=3, cols=4)

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
    board = utils.place_piece(board, 2, 1)
    test_board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ]
    assert board == test_board


def test_place_piece__second_move_on_first():
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ]
    board = utils.place_piece(board, 2, 2)
    test_board = [
        [0, 0, 0, 0],
        [0, 2, 0, 0],
        [0, 1, 0, 0],
    ]
    assert board == test_board


def test_place_piece__column_full():
    board = [
        [0, 1, 0, 0],
        [0, 2, 0, 0],
        [0, 1, 0, 0],
    ]
    with pytest.raises(exceptions.ColumnFull):
        board = utils.place_piece(board, 2, 2)
        print(board)


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
    assert utils.check_win(board, 7) is True


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
    assert utils.check_win(board, 4) is True


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
    assert utils.check_win(board, 5) is True


def test_check_win__vertical():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 0, 2, 0, 0, 0],
        [0, 1, 2, 2, 0, 0, 0],
    ]
    assert utils.check_win(board, 2) is True


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
    assert utils.check_win(board, 2) is False


def test_check_win__diagonal_fwd_slash_far_right():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    assert utils.check_win(board, 5) is True


def test_check_win__diagonal_fwd_slash_far_left():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    assert utils.check_win(board, 2) is True


def test_check_win__diagonal_fwd_slash_middle():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 2, 1, 1, 0, 0],
        [0, 0, 1, 1, 2, 0, 0],
        [0, 1, 2, 2, 2, 0, 0],
    ]
    assert utils.check_win(board, 4) is True


def test_check_win__diagonal_back_slash_far_right():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    assert utils.check_win(board, 5) is True


def test_check_win__diagonal_back_slash_far_left():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    assert utils.check_win(board, 2) is True


def test_check_win__diagonal_back_slash_middle():
    board = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 2, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 2, 2, 1, 1, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
    ]
    assert utils.check_win(board, 3) is True
