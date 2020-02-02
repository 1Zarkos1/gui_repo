import operator
import sys
from functools import partial

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout)


class MyWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(0, 0, 200, 300)
        self.setWindowTitle('Img window')
        self.buttons = [
            '/', '*', '-',
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3',
            'c', '0', '+'
        ]
        self.col_num = 3
        self.operators = {'+': operator.add, '-': operator.sub,
                          '/': operator.truediv, '*': operator.mul}
        self.operand = ''
        self.operator = ''
        self.answer = ''
        self.setUI()

    def setUI(self):
        cenWidg = QWidget(self)
        vbLay = QVBoxLayout(cenWidg)
        layerWidg = QWidget()
        grLay = QGridLayout(layerWidg)
        ansLabel = QLabel()
        ansLabel.setText('<h2>0</h2>')
        layerWidg.setLayout(grLay)
        vbLay.addWidget(ansLabel)
        vbLay.addWidget(layerWidg)
        self.ansLabel = ansLabel
        self.buttons1 = [QPushButton(item) for item in self.buttons]
        for i, button in enumerate(self.buttons1):
            button.clicked.connect(partial(self.check_but, button.text()))
            grLay.addWidget(button, i//3, i % 3)
        self.setCentralWidget(cenWidg)

    def check_but(self, but):
        if but == 'c':
            self.operand = ''
            self.operator = ''
            self.answer = ''
        elif but in self.operators:
            self.operator = but
        else:
            self.operand += but
        self.ansLabel.setText(f'<h2>{self.operand + self.operator}</h2>')


app = QApplication(sys.argv)
window = MyWindow()
window.show()
sys.exit(app.exec_())
