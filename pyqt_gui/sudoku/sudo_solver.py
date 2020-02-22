import sys
from functools import partial
import random

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QShortcut, QAction, QMessageBox, 
                             QHBoxLayout, QComboBox, QCheckBox)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent


class MyWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(1000, 400, 4, 4)
        self.setWindowTitle('Sudoku solver')
        self.dimension = 9
        self.setWindowIcon(QIcon('../img/sudoIcon.png'))
        self.setStyleSheet(open('stylesheet.css').read())
        # flag for creating own sudokus
        self.createOwn = False

        self.generateSudoku()
        self.initUI()

    def initUI(self):
        # defines central widget and vertical layout for it
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        # defines grid widget and main field as group of LineEdits, styles them
        # and adds to layout
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        gridLayout.setSpacing(0)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridWidget.setLayout(gridLayout)
        self.textFieldCss = """
            border: 1px solid black;
            height: 50px;
            width: 50px;
            font-size: 40px;
            font-family: Arial;
            color: red;
        """
        # self.selectTypeColor = QComboBox()
        self.textFields = [[QLineEdit() for col in range(self.dimension)]
                                for row in range(self.dimension)]
        for i, row in enumerate(self.textFields):
            for j, cell in enumerate(row):
                if self.initialSudoku[i][j]:
                    cell.setText(self.initialSudoku[i][j])
                    cell.setReadOnly(True)
                    cell.setStyleSheet(self.textFieldCss+'background-color: #ddd')
                else:
                    cell.setStyleSheet(self.textFieldCss+'color: #00f')
                    # cell.textChanged.connect(self.changeTypingColor)
                cell.installEventFilter(self)
                cell.setValidator(QIntValidator())
                cell.setAlignment(Qt.AlignCenter)
                cell.setMaxLength(1)

                gridLayout.addWidget(cell, i, j)
        
        mainVertLayout.addWidget(gridWidget)
        mainVertLayout.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setAlignment(Qt.AlignLeft)

        # add button for creating own sudokus and checkbox for viewing solving 
        # process
        checkBWidg = QWidget()
        checkBLayout = QHBoxLayout(checkBWidg)
        checkBLabel = QLabel('Show solving process:')
        self.checkBox = QCheckBox()
        self.ownSudokuBut = QPushButton('Create sudoku')
        self.ownSudokuBut.clicked.connect(self.createOwnSudoku)
        self.ownSudokuBut.setObjectName('ownSudoku')
        # some template for future improvement (changing typing color)
        # colorLabel = QLabel('Number color:')
        # self.selectTypeColor = QComboBox()
        # self.selectTypeColor.addItems(['Blue', 'Green', 'Black', 'Magenta'])
        # self.selectTypeColor.currentIndexChanged.connect(self.changeTypingColor)
        checkBLayout.addWidget(self.ownSudokuBut)
        # checkBLayout.addWidget(colorLabel)
        # checkBLayout.addWidget(self.selectTypeColor)
        checkBLayout.addWidget(checkBLabel)
        checkBLayout.addWidget(self.checkBox)
        checkBWidg.setLayout(checkBLayout)
        mainVertLayout.addWidget(checkBWidg)

        # main functional buttons
        funcButtonsWidg = QWidget(cenWidget)
        funcButtonsLayout = QHBoxLayout()
        checkBut = QPushButton("Check fields")
        checkBut.clicked.connect(self.checkBoard)
        clearBut = QPushButton("Clear")
        clearBut.clicked.connect(self.clearBoard)
        solveBut = QPushButton("Solve")
        solveBut.clicked.connect(partial(self.solveBoard, 0, 0))
        self.newSudoBut = QPushButton("New")
        self.newSudoBut.clicked.connect(self.generateSudoku)
        exitBut = QPushButton("Exit")
        exitBut.clicked.connect(lambda x: sys.exit())
        funcButtonsLayout.addWidget(checkBut)
        funcButtonsLayout.addWidget(clearBut)
        funcButtonsLayout.addWidget(solveBut)
        funcButtonsLayout.addWidget(self.newSudoBut)
        funcButtonsLayout.addWidget(exitBut)
        funcButtonsWidg.setLayout(funcButtonsLayout)
        mainVertLayout.addWidget(funcButtonsWidg)

        self.setCentralWidget(cenWidget)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            for i, row in enumerate(self.textFields):
                for k, cell in enumerate(row):
                    if cell.hasFocus():
                        curRow = i
                        curCell = k
            if event.key() == Qt.Key_Up:
                if curRow >= 1: self.textFields[curRow-1][curCell].setFocus()
            elif event.key() == Qt.Key_Down:
                if curRow <= 7: self.textFields[curRow+1][curCell].setFocus()
            elif event.key() == Qt.Key_Left:
                if curCell >= 1: self.textFields[curRow][curCell-1].setFocus()
            elif event.key() == Qt.Key_Right:
                if curCell <= 7: self.textFields[curRow][curCell+1].setFocus()

        return QObject.event(obj, event)

    # function for setting own initial sudokus by typing numbers into fields
    def createOwnSudoku(self):
        # if flag is in default state button has not been pressed 
        if self.createOwn:
            self.generateSudoku()
            self.createOwn = False
            self.ownSudokuBut.setText('Create sudoku')
            self.newSudoBut.setDisabled(False)
        # if button for creating own sudoku was pressed
        else:
            self.createOwn = True
            style = """
                background-color: white;
                color: black;
            """
            for row in self.textFields:
                for cell in row:
                    cell.setStyleSheet(self.textFieldCss+style)
                    cell.setText('')
                    cell.setReadOnly(False)
            self.ownSudokuBut.setText('Save')
            self.newSudoBut.setDisabled(True)

    # function for generating random sudokus from file or from user input
    def generateSudoku(self):
        # if button for creating own sudoku was pressed process typed values and
        # make them default values for sudoku
        if self.createOwn:
            sud_list = [cell.text() for row in self.textFields for cell in row]
        # if user choose random sudoku open file with sudokus and select 
        # a random one
        else:    
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
    
    # check entire board to see if it's solved correctly and displaying message 
    # about result
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

    # function that automaticaly solves the board
    def solveBoard(self, row, col):
        # if column more than nine process next row from column 0
        if col == 9:
            col = 0
            row += 1
        # if row > 8 that means all rows has been processed - return completed
        if row == 9:
            return True
        # check if value is in predefined values and if it's in
        # not process default values
        if (row, col) in self.initialValues:
            return self.solveBoard(row,col+1)
        else:
            # process each value from 1 to 9
            for val in range(1,10):
                self.textFields[row][col].setText(str(val))
                # if show process checkbox was checked refresh window to show 
                # solving process
                if self.checkBox.isChecked():
                    self.update()
                    QApplication.processEvents()
                # if value is legit process next cell and chain-return True if 
                # processing was completed (initial True comes all the way from
                # row==9 above after last row was processed)
                if (self.checkRow(row) and self.checkColumn(col) 
                        and self.checkSubgrid(row, col)):
                    if self.solveBoard(row,col+1):
                        return True
                    # if not - delete current number from cell and go 
                    # to the next number 
                    else:
                        self.textFields[row][col].setText('')
                        continue
                self.textFields[row][col].setText('')
            return False

    # clear all user input in board
    def clearBoard(self):
        self.initUI()

    # check if row is completed (without blank cells)
    def rowCompleted(self, row):
        row_list = [cell.text() for cell in self.textFields[row]]
        if '' in row_list:
            return False
        else:
            return True

    # checks if there no repeated numbers in a row
    def checkRow(self, row):
        row_list = [
            cell.text() for cell in self.textFields[row] if cell.text() != ''
        ]
        if len(set(row_list)) != len(row_list):
            return False
        return True

    # checks if there no repeated numbers in a column
    def checkColumn(self, col):
        col_list = [
            self.textFields[row][col].text() for row in range(9) 
                if self.textFields[row][col].text() != ''
        ]
        if len(set(col_list)) != len(col_list):
            return False
        return True

    # checks if there no repeated numbers in a subgrid (3x3 cells)
    def checkSubgrid(self, row, col):
       
        def setRowCol(i):
            if i < 3:
                return 0
            elif i >= 3 and i < 6:
                return 3
            else:
                return 6
        
        col = setRowCol(col)
        row = setRowCol(row)
        grid = []
        for i in range(3):
            grid.extend([
                cell.text() for cell in self.textFields[row+i][col:col+3]
            ])
        grid = [cell for cell in grid if cell != '']
        if len(set(grid)) != len(grid):
            return False
        return True

    # function for changing color of typing numbers (dev)
    # def changeTypingColor(self):
    #     [cell.setStyleSheet(
    #         self.textFieldCss+f'color: {self.selectTypeColor.currentText()}')
    #         for row in self.textFields for cell in row 
    #         if cell.isReadOnly() == False and cell.text() == ''
    #     ]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    a = app.exec_()