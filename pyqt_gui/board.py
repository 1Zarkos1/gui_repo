import random
import pprint

class BoardSet():

    def __init__(self, n_cols, n_rows, n_fact):
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.n_cells = n_cols*n_rows
        self.n_mines = int(n_fact * self.n_cells)
        self.make_set()

    def make_set(self):
        rand_sam = random.sample(range(self.n_cells), k=self.n_mines)
        self.flat_set = ['*' if i in rand_sam else '-' for i in range(self.n_cells)]
        self.lists_set = [
            self.flat_set[i : i+self.n_cols] for i in range(0,len(self.flat_set),self.n_cols)
        ]

    def get_cell_value(self, n):
        if self.flat_set[n] is '*':
            return '*'
        else:  
            col = n%self.n_cols
            row = n//self.n_rows
            prev_col = col - 1 if col > 0 else 0
            next_col = col + 2
            mid = self.lists_set[row][prev_col:next_col]
            if row-1 < 0:
                up = []
            else:
                up = self.lists_set[row-1][prev_col:next_col]
            if row+1 == len(self.lists_set):
                bot = []
            else:
                bot = self.lists_set[row+1][prev_col:next_col]
            
            comb_list = up + mid + bot

            return str(comb_list.count('*'))

    def get_set(self):
        open_set = list(map(self.get_cell_value, range(self.n_cells)))
        open_set = [open_set[i : i+self.n_cols] for i in range(0,len(open_set),self.n_cols)]
        return open_set    