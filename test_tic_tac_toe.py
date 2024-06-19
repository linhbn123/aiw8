import unittest
from tic_tac_toe import TicTacToe

class TestTicTacToe(unittest.TestCase):
    def setUp(self):
        self.game = TicTacToe()

    def test_initial_board(self):
        self.assertEqual(self.game.board, [' ' for _ in range(9)])

    def test_make_move(self):
        self.assertTrue(self.game.make_move(0, 'X'))
        self.assertEqual(self.game.board[0], 'X')
        self.assertFalse(self.game.make_move(0, 'O'))

    def test_winner(self):
        self.game.make_move(0, 'X')
        self.game.make_move(1, 'X')
        self.game.make_move(2, 'X')
        self.assertEqual(self.game.current_winner, 'X')

    def test_no_winner(self):
        self.game.make_move(0, 'X')
        self.game.make_move(1, 'O')
        self.game.make_move(2, 'X')
        self.assertIsNone(self.game.current_winner)

    def test_available_moves(self):
        self.game.make_move(0, 'X')
        self.assertIn(1, self.game.available_moves())
        self.assertNotIn(0, self.game.available_moves())

    def test_empty_squares(self):
        self.assertTrue(self.game.empty_squares())
        for i in range(9):
            self.game.make_move(i, 'X')
        self.assertFalse(self.game.empty_squares())

if __name__ == '__main__':
    unittest.main()