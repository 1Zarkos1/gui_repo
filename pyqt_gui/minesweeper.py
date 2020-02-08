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
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(800, 400, 10, 10)
        self.setWindowTitle('PyQt5 minesweeper')
        self.board = BoardSet(10, 10, 0.2)

        self.initUI()

    def initUI(self):
        # initialize widgets and layouts
        self.button_colors = {
            '0': '#c7c7c7', '1': '#00ffff', '2': '#00aaff', '3': '#0072ff', 
            '4': '#0030ff', '5': '#7800ff', '6': '#04a800', '7': '#ab0081', 
            '8': '#a8002f', '9': '#ff0000'
        }
        cenWidget = QWidget(self)
        gridLayout = QGridLayout(cenWidget)
        gridLayout.setSpacing(0)
        cenWidget.setLayout(gridLayout)
        # add buttons to grid layout
        self.buttonInstances = [QPushButton() for num in range(self.board.n_cells)]
        for i, button in enumerate(self.buttonInstances):
            button.setFixedSize(20, 20)
            button.setStyleSheet('background-color: #4955ff;')
            button.clicked.connect(partial(self.open_button, button, i))
            button.installEventFilter(self)
            gridLayout.addWidget(button, i//self.board.n_cols, i%self.board.n_cols)

        self.setCentralWidget(cenWidget)

    def open_button(self, button, i):
        if button.iconSize().height() < 19 and button.isEnabled():
            butt_text = self.board.get_cell_value(i)
            if butt_text == '0':
                self.open_chain_cells(i)
            elif butt_text != '*':
                button.setText(butt_text)
                button.setEnabled(False)
                button.setStyleSheet(
                    f'background-color: #c7c7c7; color: {self.button_colors[butt_text]}')
            else:
                button.setIcon(QIcon('img/mine.png'))
                button.setIconSize(QSize(19, 19))
                self.display_end_message()
        self.check_win()

    def open_chain_cells(self, i):
        slic = self.buttonInstances[i-10-1:i-10+2] + self.buttonInstances[i-1:i+2] \
               + self.buttonInstances[i-10-1:i-10+2]
        for inst in slic:
            if inst.isEnabled():
                self.open_button(inst, self.buttonInstances.index(inst))

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
        return QObject.event(obj, event)

    def set_flag_icon(self, button):
        if button.isEnabled():
            size = button.iconSize().height()
            if size < 19:
                button.setIcon(QIcon('img/flag.png'))
                button.setIconSize(QSize(19, 19))
            else:
                button.setIcon(QIcon())
                button.setIconSize(QSize(16, 16))

    def check_win(self):
        active_boxes = [button.isEnabled() for button in self.buttonInstances]
        if sum(active_boxes) == self.board.n_mines:
            self.display_end_message(win=True)

if __name__ == '__main__':
    while True:
        app = QApplication(sys.argv)
        window = MyWindow()
        window.show()
        a = app.exec_()
        if EXIT_CODE_REBOOT != a:
            break

