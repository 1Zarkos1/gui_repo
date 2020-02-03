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
        self.hintField = QLabel(parent=cenWidget)
        self.textField = QLineEdit()
        f = self.textField.font()
        f.setPointSize(18)
        self.textField.setFont(f)
        gridWidget.setLayout(gridLayout)
        # add widgets to top level layout
        vertLayout.addWidget(self.hintField)
        vertLayout.addWidget(self.textField)
        vertLayout.addWidget(gridWidget)
        # add buttons to grid layout
        self.buttonInstances = [QPushButton(item) for item in self.buttonsText]
        for i, button in enumerate(self.buttonInstances):
            button.clicked.connect(partial(self.doMath, button.text()))
            gridLayout.addWidget(button, i//self.col_num, i % self.col_num)

        self.setCentralWidget(cenWidget)

    def doMath(self, buttonValue):
        currentValue = self.textField.text()
        if buttonValue == 'c':
            self.operand = ''
            self.operator = ''
            self.textField.setText('')
        elif buttonValue == '<-' and currentValue != '':
            if len(currentValue) == 1:
                self.textField.setText('')
            else:
                self.textField.setText(currentValue[:-1])
        elif (buttonValue in self.operators
              and self.convertValue(currentValue) is not None):
            self.operator = buttonValue
            self.operand = self.convertValue(currentValue)
            self.textField.setText('')
        elif buttonValue == '.':
            if '.' not in currentValue:
                self.textField.setText(currentValue+buttonValue)
        elif (buttonValue == '=' and self.operator 
              and self.convertValue(currentValue) != None):
            self.textField.setText(
                f'''{self.operators[self.operator](
                   self.operand, self.convertValue(currentValue))}''')
            self.operand = ''
            self.operator = ''
        elif self.convertValue(buttonValue) != None:
            self.textField.setText(currentValue+buttonValue)
        self.hintField.setText(f'<h1><font color=#a0a0a0>{self.operand}' 
                                 f'{self.operator}</font></h1>')

    def convertValue(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except:
                return None


app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())
