import sys
from functools import partial
from pprint import pprint
import random

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QLineEdit, QShortcut, QAction,
                             QMessageBox, QHBoxLayout, QComboBox, QCheckBox)
from PyQt5.QtGui import QKeySequence, QIntValidator, QIcon
from PyQt5.QtCore import QLocale, Qt, QEvent, QObject, QSize


class MyWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(1000, 400, 4, 4)
        self.setWindowTitle('Sudoku solver')
        self.dimension = 9
        self.setWindowIcon(QIcon('../img/sudoIcon.png'))

        self.generateSudoku()
        self.initUI()

    def initUI(self):
        # defines central widget and vertical layout for it
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        # defines grid widget and main field as group of buttons, styles them
        # and adds to layout
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        gridLayout.setSpacing(0)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridWidget.setLayout(gridLayout)
        textFiledCss = """
            border: 1px solid black;
            height: 50px;
            width: 50px;
            font-size: 40px;
            font-family: Arial;
            color: red;
        """
        self.textFields = [[QLineEdit() for col in range(self.dimension)]
                                for row in range(self.dimension)]
        for i, row in enumerate(self.textFields):
            for j, cell in enumerate(row):
                if self.initialSudoku[i][j]:
                    cell.setText(self.initialSudoku[i][j])
                    cell.setReadOnly(True)
                    cell.setStyleSheet(textFiledCss+'background-color: #ddd')
                else:
                    cell.setStyleSheet(textFiledCss+'color: #00f')
                cell.setValidator(QIntValidator())
                cell.setAlignment(Qt.AlignCenter)
                cell.setMaxLength(1)

                gridLayout.addWidget(cell, i, j)
        
        mainVertLayout.addWidget(gridWidget)
        mainVertLayout.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setAlignment(Qt.AlignLeft)

        checkBWidg = QWidget()
        checkBLayout = QHBoxLayout(checkBWidg)
        checkBLabel = QLabel('Show solving process:')
        self.checkBox = QCheckBox()
        checkBLayout.addWidget(checkBLabel)
        checkBLayout.addWidget(self.checkBox)
        checkBWidg.setLayout(checkBLayout)
        mainVertLayout.addWidget(checkBWidg)

        funcButtonsWidg = QWidget(cenWidget)
        funcButtonsLayout = QHBoxLayout()
        checkBut = QPushButton("Check fields")
        checkBut.clicked.connect(self.checkBoard)
        clearBut = QPushButton("Clear")
        clearBut.clicked.connect(self.clearBoard)
        solveBut = QPushButton("Solve")
        solveBut.clicked.connect(partial(self.solveBoard, 0, 0))
        newSudoBut = QPushButton("New")
        newSudoBut.clicked.connect(self.generateSudoku)
        exitBut = QPushButton("Exit")
        exitBut.clicked.connect(lambda x: sys.exit())
        funcButtonsLayout.addWidget(checkBut)
        funcButtonsLayout.addWidget(clearBut)
        funcButtonsLayout.addWidget(solveBut)
        funcButtonsLayout.addWidget(newSudoBut)
        funcButtonsLayout.addWidget(exitBut)
        funcButtonsWidg.setLayout(funcButtonsLayout)
        mainVertLayout.addWidget(funcButtonsWidg)

        self.setCentralWidget(cenWidget)


    def generateSudoku(self):
        with open('sudokus.txt') as f:
            sudokusList = f.read().splitlines()
        sud_list = [
            '' if i == '.' else i for i in sudokusList[random.randint(0, 724)]
        ]
        self.initialSudoku = [sud_list[i:i+9] for i in range(0,81,9)]
        self.initialValues = [
            (i//self.dimension, i%self.dimension) for i, value 
            in enumerate(sud_list) if value != ''
        ]
        
        self.initUI()
    
    def checkBoard(self):
        for i in range(9):
            for j in range(9):
                if (not self.checkRow(i) or not self.checkColumn(j) 
                        or not self.checkSubgrid(i, j) or not self.rowCompleted(i)):
                    result = False
                    break
                else:
                    result = True
        
        message = QMessageBox()
        
        if result:
            message.information(self, 'You won', 'Congratulation!', 
                                        QMessageBox.Ok)
        else:
            message.information(self, 'Wrong board', 'Try again!', 
                                        QMessageBox.Ok)

    def solveBoard(self, row, col):
        print(row, col)
        if col == 9:
            col = 0
            row += 1
        if row == 9:
            return True
        print(row, col)
        if (row, col) in self.initialValues:
            return self.solveBoard(row,col+1)
        else:
            for val in range(1,10):
                self.textFields[row][col].setText(str(val))
                if self.checkBox.isChecked():
                    self.update()
                    QApplication.processEvents()
                if (self.checkRow(row) and self.checkColumn(col) 
                        and self.checkSubgrid(row, col)):
                    print(val)
                    if self.solveBoard(row,col+1):
                        return True
                    else:
                        self.textFields[row][col].setText('')
                        continue
                self.textFields[row][col].setText('')
            return False

    def clearBoard(self):
        self.initUI()

    def rowCompleted(self, row):
        row_list = [cell.text() for cell in self.textFields[row]]
        if '' in row_list:
            return False
        else:
            return True

    def checkRow(self, row):
        row_list = [
            cell.text() for cell in self.textFields[row] if cell.text() != ''
        ]
        if len(set(row_list)) != len(row_list):
            return False
        return True

    def checkColumn(self, col):
        col_list = [
            self.textFields[row][col].text() for row in range(9) 
                if self.textFields[row][col].text() != ''
        ]
        if len(set(col_list)) != len(col_list):
            return False
        return True

    def checkSubgrid(self, row, col):
        col = self.setRowCol(col)
        row = self.setRowCol(row)
        grid = []
        for i in range(3):
            grid.extend([
                cell.text() for cell in self.textFields[row+i][col:col+3]
            ])
        grid = [cell for cell in grid if cell != '']
        if len(set(grid)) != len(grid):
            return False
        return True

    def setRowCol(self, i):
        if i < 3:
            return 0
        elif i >= 3 and i < 6:
            return 3
        else:
            return 6


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    a = app.exec_()