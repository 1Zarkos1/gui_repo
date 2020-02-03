import operator
import sys
from functools import partial

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QLineEdit)


class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(0, 0, 200, 300)
        self.setWindowTitle('PyQt5 calculator')
        self.buttonsText = [
            '<-', '=', '+',
            '/', '*', '-',
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3',
            'c', '0', '.'
        ]
        self.col_num = 3
        self.operators = {'+': operator.add, '-': operator.sub,
                          '/': operator.truediv, '*': operator.mul}
        self.operand = ''
        self.operator = ''
        self.setUI()

    def setUI(self):
        # initialize widgets and layouts
        cenWidget = QWidget(self)
        vertLayout = QVBoxLayout(cenWidget)
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        self.answerField = QLabel(parent=cenWidget)
        self.textField = QLineEdit()
        f = self.textField.font()
        f.setPointSize(18)
        self.textField.setFont(f)
        gridWidget.setLayout(gridLayout)
        # add widgets to top level layout
        vertLayout.addWidget(self.answerField)
        vertLayout.addWidget(self.textField)
        vertLayout.addWidget(gridWidget)
        # add buttons to grid layout
        self.buttonInstances = [QPushButton(item) for item in self.buttonsText]
        for i, button in enumerate(self.buttonInstances):
            button.clicked.connect(partial(self.doMath, button.text()))
            gridLayout.addWidget(button, i//self.col_num, i % self.col_num)

        self.setCentralWidget(cenWidget)

    def doMath(self, buttonValue):
        if buttonValue == 'c':
            self.operand = ''
            self.operator = ''
            self.textField.setText('')
        elif buttonValue in self.operators:
            self.operator = buttonValue
        else:
            self.textField.setText(self.textField.text()+buttonValue)
        self.answerField.setText(f'<h1>{self.operand + self.operator}</h1>')


app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())
