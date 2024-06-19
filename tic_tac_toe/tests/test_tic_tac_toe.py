import unittest
from tic_tac_toe import TicTacToe

class TestTicTacToe(unittest.TestCase):

    def test_valid_move(self):
        game = TicTacToe()
        self.assertTrue(game.make_move(0, 'X'))
        self.assertEqual(game.board[0], 'X')

    def test_invalid_move(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        self.assertFalse(game.make_move(0, 'O'))

    def test_win_condition(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        game.make_move(1, 'X')
        game.make_move(2, 'X')
        self.assertEqual(game.current_winner, 'X')

    def test_draw_condition(self):
        game = TicTacToe()
        moves = [0, 1, 2, 4, 3, 5, 7, 6, 8]
        for index, move in enumerate(moves):
            game.make_move(move, 'X' if index % 2 == 0 else 'O')
        self.assertFalse(game.current_winner)
        self.assertFalse(game.empty_squares())

    def test_move_placement(self):
        game = TicTacToe()
        game.make_move(0, 'X')
        self.assertEqual(game.board[0], 'X')
        game.make_move(8, 'O')
        self.assertEqual(game.board[8], 'O')


if __name__ == '__main__':
    unittest.main()