import operator
import sys
from functools import partial

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QLineEdit, QShortcut, QAction)
from PyQt5.QtGui import QKeySequence, QDoubleValidator
from PyQt5.QtCore import QLocale, Qt


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
        self.initUI()
        self.setShortcuts()

    def initUI(self):
        # initialize widgets and layouts
        cenWidget = QWidget(self)
        vertLayout = QVBoxLayout(cenWidget)
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        gridWidget.setLayout(gridLayout)
        self.hintField = QLabel(parent=cenWidget)
        # configure text filed and validator
        self.textField = QLineEdit()
        f = self.textField.font()
        f.setPointSize(18)
        self.textField.setFont(f)
        validator = QDoubleValidator()
        validator.setLocale(QLocale('English'))
        self.textField.setValidator(validator)
        # add widgets to top level layout
        vertLayout.addWidget(self.hintField)
        vertLayout.addWidget(self.textField)
        vertLayout.addWidget(gridWidget)
        # add buttons to grid layout
        self.buttonInstances = [QPushButton(item) for item in self.buttonsText]
        for i, button in enumerate(self.buttonInstances):
            button.clicked.connect(partial(self.calculateValue, button.text()))
            gridLayout.addWidget(button, i//self.col_num, i % self.col_num)

        self.setCentralWidget(cenWidget)

    def calculateValue(self, buttonValue):
        currentValue = self.textField.text()
        convertedValue = self.convertValue(currentValue)
        if buttonValue == 'c':
            self.clearFields()
        elif buttonValue == '<-':
            self.textField.setText(currentValue[:-1])
        elif buttonValue == '.':
            if '.' not in currentValue:
                self.textField.setText(currentValue+buttonValue)
        elif (not self.operand and buttonValue in self.operators
              and convertedValue != None):
            self.operator = buttonValue
            self.operand = convertedValue
            self.textField.setText('')
        elif (buttonValue == '=' or buttonValue in self.operators 
              and self.operator and convertedValue):
            answer = self.operators[self.operator](
                     self.operand, convertedValue)
            self.clearFields()
            if buttonValue == '=':
                self.textField.setText(f'{answer}')
            else:
                self.operand = answer
                self.operator = buttonValue
        elif self.convertValue(buttonValue) != None:
            self.textField.setText(currentValue+buttonValue)
        
        self.hintField.setText(f'<h1><font color=#a0a0a0>{self.operand}' 
                               f'{self.operator}</font></h1>')

    def setShortcuts(self):
        eqShort= QShortcut(QKeySequence('Enter'), self)
        eqShort.activated.connect(partial(self.calculateValue, '='))
        for sign in self.buttonsText[1:5]:
            short= QShortcut(QKeySequence(sign), self)
            short.activated.connect(partial(self.calculateValue, sign))
        

    def convertValue(self, value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except:
                return None

    def clearFields(self):
        self.operand = ''
        self.operator = ''
        self.textField.setText('')

app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())