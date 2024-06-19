
class TicTacToe:
    def __init__(self):
        """
        Initializes the TicTacToe board and sets the current winner to None.
        """
        self.board = [' ' for _ in range(9)]
        self.current_winner = None

    def print_board(self):
        """
        Prints the current board state.
        """
        for row in [self.board[i * 3:(i + 1) * 3] for i in range(3)]:
            print('| ' + ' | '.join(row) + ' |')

    @staticmethod
    def print_board_nums():
        """
        Prints the board with numbers indicating each position.
        """
        number_board = [[str(i) for i in range(j * 3, (j + 1) * 3)] for j in range(3)]
        for row in number_board:
            print('| ' + ' | '.join(row) + ' |')

    def available_moves(self):
        """
        Returns a list of available moves (indices of empty spots on the board).
        """
        return [i for i, spot in enumerate(self.board) if spot == ' ']

    def empty_squares(self):
        """
        Returns True if there are empty squares on the board, False otherwise.
        """
        return ' ' in self.board

    def num_empty_squares(self):
        """
        Returns the number of empty squares on the board.
        """
        return self.board.count(' ')

    def make_move(self, square, letter):
        """
        Places a letter ('X' or 'O') on the board at the specified square if valid.
        
        Args:
            square (int): The board position where the letter should be placed.
            letter (str): The letter to be placed ('X' or 'O').

        Returns:
            bool: True if the move is valid and was made, False otherwise.
        """
        if self.board[square] == ' ':
            self.board[square] = letter
            if self.winner(square, letter):
                self.current_winner = letter
            return True
        return False

    def winner(self, square, letter):
        """
        Checks if the current move leads to a win.

        Args:
            square (int): The board position where the letter was placed.
            letter (str): The letter placed ('X' or 'O').

        Returns:
            bool: True if the letter has won the game, False otherwise.
        """
        # Check the row
        row_ind = square // 3
        row = self.board[row_ind * 3:(row_ind + 1) * 3]
        if all([s == letter for s in row]):
            return True
        # Check column
        col_ind = square % 3
        column = [self.board[col_ind + i * 3] for i in range(3)]
        if all([s == letter for s in column]):
            return True
        # Check diagonals
        if square % 2 == 0:
            diagonal1 = [self.board[i] for i in [0, 4, 8]]
            if all([s == letter for s in diagonal1]):
                return True
            diagonal2 = [self.board[i] for i in [2, 4, 6]]
            if all([s == letter for s in diagonal2]):
                return True
        return False
