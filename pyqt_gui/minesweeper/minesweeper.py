import operator
import sys, os
import random
from functools import partial
from board import BoardSet

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QLineEdit, QShortcut, QAction,
                             QMessageBox)
from PyQt5.QtGui import QKeySequence, QDoubleValidator, QIcon
from PyQt5.QtCore import QLocale, Qt, QEvent, QObject, QSize

EXIT_CODE_REBOOT = -123


class MyWindow(QMainWindow):
    EXIT_CODE_REBOOT = -123
    def __init__(self, cols=10, rows=10, mine_ratio=0.1, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(800, 400, 10, 10)
        self.setWindowTitle('PyQt5 minesweeper')
        # initialize game board in the form of array depending on number of rows
        # columns abd mines ratio provided
        try:
            self.board = BoardSet(int(cols), int(rows), float(mine_ratio))
        except ValueError:
            print('Please provide correct arguments for the game. (Number of '\
                  'columns and rows as integers and percent of mines as '\
                  'decimal value)')
            sys.exit()
        self.n_mines_left = self.board.n_mines
        
        self.initUI()

    def initUI(self):
        # add colors for different cell values
        self.button_colors = {
            '0': '#c7c7c7', '1': '#00ffff', '2': '#00aaff', '3': '#0072ff', 
            '4': '#0030ff', '5': '#7800ff', '6': '#04a800', '7': '#ab0081', 
            '8': '#a8002f', '9': '#ff0000'
        }
        cenWidget = QWidget(self)
        gridLayout = QGridLayout(cenWidget)
        gridLayout.setSpacing(0)
        cenWidget.setLayout(gridLayout)
        # create and add buttons to grid layout
        self.buttonInstances = [QPushButton() for num in range(self.board.n_cells)]
        for i, button in enumerate(self.buttonInstances):
            button.setFixedSize(20, 20)
            button.setStyleSheet('background-color: #4955ff;')
            button.clicked.connect(partial(self.open_button, button, i))
            button.installEventFilter(self)
            gridLayout.addWidget(button, i//self.board.n_cols, i%self.board.n_cols)

        self.minesCounter = QLabel(f'<h3>Mines left: {self.n_mines_left}</h3>')
        gridLayout.addWidget(self.minesCounter, self.board.n_cols, 0, 2, self.board.n_cols)
        
        self.setCentralWidget(cenWidget)

    # set value to chosen button and deactivate it
    def open_button(self, button, i):
        if button.iconSize().height() < 19 and button.isEnabled():
            butt_text = self.board.get_cell_value(i)
            if butt_text != '*':
                button.setText(butt_text)
                button.setEnabled(False)
                button.setStyleSheet(
                    f'background-color: #c7c7c7; color: {self.button_colors[butt_text]}')
                if butt_text == '0':
                    self.open_chain_cells(i)
            else:
                for i, button in enumerate(self.buttonInstances):
                    if self.board.flat_board[i] == '*':
                        button.setIcon(QIcon('../img/mine.png'))
                        button.setIconSize(QSize(19, 19))
                self.display_end_message()
        self.check_win()

    # opens button directly adjacent to button 'i'
    def open_chain_cells(self, i):
        adjacent_cells = self.board.get_adjacent_cells(
            i, self.board.make_split_board(self.buttonInstances))
        for inst in adjacent_cells:
            if inst.isEnabled():
                self.open_button(inst, self.buttonInstances.index(inst))

    # display message depending on result
    def display_end_message(self, win=False):
        result = 'won' if win else 'lost'
        reply = QMessageBox.question(self, 
            'Your game has ended', f"You {result}.\nDo you want to play again?")
        if reply == QMessageBox.Yes:
            QApplication.exit(MyWindow.EXIT_CODE_REBOOT)
        else:
            QApplication.exit(1)
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                self.set_flag_icon(obj)
            elif event.button() == Qt.MiddleButton:
                if not obj.isEnabled() :
                    i = self.buttonInstances.index(obj)
                    adj_cells = self.board.get_adjacent_cells(
                        i, self.board.make_split_board(self.buttonInstances))
                    flag_count = [
                        1 for button in adj_cells 
                        if button.iconSize().height() == 19
                    ]
                    if sum(flag_count) == int(obj.text()):
                        self.open_chain_cells(self.buttonInstances.index(obj))
        return QObject.event(obj, event)

    # allows to mark and unmark buttons with supposed mines under it
    def set_flag_icon(self, button):
        if button.isEnabled():
            size = button.iconSize().height()
            if size < 19:
                button.setIcon(QIcon('../img/flag.png'))
                button.setIconSize(QSize(19, 19))
                self.n_mines_left -= 1
                self.minesCounter.setText((f'<h3>Mines left: {self.n_mines_left}</h3>'))
            else:
                button.setIcon(QIcon())
                button.setIconSize(QSize(16, 16))
                self.n_mines_left += 1
                self.minesCounter.setText((f'<h3>Mines left: {self.n_mines_left}</h3>'))

    # check if number of active buttons left = number of mines
    def check_win(self):
        active_boxes = [button.isEnabled() for button in self.buttonInstances]
        if sum(active_boxes) == self.board.n_mines:
            self.display_end_message(win=True)

if __name__ == '__main__':
    while True:
        app = QApplication(sys.argv)
        try:
            cmd_arg = sys.argv[1:]
        except IndexError:
            cmd_arg = []
        window = MyWindow(*cmd_arg)
        window.show()
        a = app.exec_()
        if EXIT_CODE_REBOOT != a:
            break