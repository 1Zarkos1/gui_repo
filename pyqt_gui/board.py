import random
import pprint


class BoardSet():

    def __init__(self, n_cols, n_rows, mine_ratio):
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.n_cells = n_cols*n_rows
        self.n_mines = int(mine_ratio * self.n_cells)
        self.make_set(self.n_cols, self.n_cells, self.n_mines)

    def make_set(self, n_cols, n_cells, n_mines):
        rand_sam = random.sample(range(n_cells), k=n_mines)
        self.flat_board = [
            '*' if i in rand_sam else '-' for i in range(n_cells)]
        self.split_board = self.make_split_board(self.flat_board)

    # split list into 2 dimensional list to represent rows
    def make_split_board(self, board_list):
        return [
            board_list[i: i+self.n_cols]
            for i in range(0, len(board_list), self.n_cols)
        ]

    # get cells directly around cell with index 'n'
    def get_adjacent_cells(self, n, whole_board):
            col = n % self.n_cols
            row = n//self.n_rows
            prev_col = col - 1 if col > 0 else 0
            next_col = col + 2
            mid = whole_board[row][prev_col:next_col]
            if row-1 < 0:
                up = []
            else:
                up = whole_board[row-1][prev_col:next_col]
            if row+1 == len(whole_board):
                bot = []
            else:
                bot = whole_board[row+1][prev_col:next_col]

            comb_list = up + mid + bot

            return comb_list

    # get and return cell value reperesenting number of mines directly adjacent
    # to chosen cell
    def get_cell_value(self, n):
        if self.flat_board[n] == '*':
            return '*'
        else:
            return str(self.get_adjacent_cells(n, self.split_board).count('*'))

    # for debugging purposes
    def get_set(self):
        open_set = list(map(self.get_cell_value, range(self.n_cells)))
        open_set = [open_set[i: i+self.n_cols]
            for i in range(0, len(open_set), self.n_cols)]
        return open_set