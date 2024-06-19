
import unittest
from tic_tac_toe import TicTacToe

class TestTicTacToe(unittest.TestCase):

    def test_initial_board(self):
        game = TicTacToe()
        expected_board = [' ' for _ in range(9)]
        self.assertEqual(game.board, expected_board)
        self.assertIsNone(game.current_winner)

    def test_make_move(self):
        game = TicTacToe()
        self.assertTrue(game.make_move(0, 'X'))
        self.assertEqual(game.board[0], 'X')
        self.assertFalse(game.make_move(0, 'O'))  # Invalid move
        self.assertEqual(game.board[0], 'X')

    def test_winner_row(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        game.make_move(1, 'X')
        game.make_move(2, 'X')
        self.assertEqual(game.current_winner, 'X')

    def test_winner_column(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        game.make_move(3, 'X')
        game.make_move(6, 'X')
        self.assertEqual(game.current_winner, 'X')

    def test_winner_diagonal(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        game.make_move(4, 'X')
        game.make_move(8, 'X')
        self.assertEqual(game.current_winner, 'X')

    def test_no_winner(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        game.make_move(1, 'O')
        game.make_move(2, 'X')
        self.assertIsNone(game.current_winner)

    def test_available_moves(self):
        game = TicTacToe()
        expected_moves = list(range(9))
        self.assertEqual(game.available_moves(), expected_moves)
        game.make_move(0, 'X')
        expected_moves.remove(0)
        self.assertEqual(game.available_moves(), expected_moves)

    def test_empty_squares(self):
        game = TicTacToe()
        self.assertTrue(game.empty_squares())
        for i in range(9):
            game.make_move(i, 'X')
        self.assertFalse(game.empty_squares())

    def test_num_empty_squares(self):
        game = TicTacToe()
        self.assertEqual(game.num_empty_squares(), 9)
        game.make_move(0, 'X')
        self.assertEqual(game.num_empty_squares(), 8)

if __name__ == '__main__':
    unittest.main()
