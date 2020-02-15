import operator
import sys
import os
import random
from functools import partial
from searchAlg import SearchClass

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QLineEdit, QShortcut, QAction,
                             QMessageBox, QHBoxLayout, QComboBox, QCheckBox)
from PyQt5.QtGui import QKeySequence, QDoubleValidator, QIcon
from PyQt5.QtCore import QLocale, Qt, QEvent, QObject, QSize


class MyWindow(QMainWindow):

    def __init__(self, cols=20, rows=20, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(800, 400, 4, 4)
        self.setWindowTitle('Pathfinder')
        self.cols = cols
        self.rows = rows
        self.start = None
        self.end = None

        self.initUI()

    def initUI(self):
        # self.button_colors = {
        #     '0': '#c7c7c7', '1': '#00ffff', '2': '#00aaff', '3': '#0072ff',
        #     '4': '#0030ff', '5': '#7800ff', '6': '#04a800', '7': '#ab0081',
        #     '8': '#a8002f', '9': '#ff0000'
        # }
        cenWidget = QWidget(self)
        vertLayout = QVBoxLayout(cenWidget)
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        gridLayout.setSpacing(0)
        gridWidget.setLayout(gridLayout)

        self.buttonInstances = [QPushButton()
                                for num in range(self.rows*self.cols)]
        for i, button in enumerate(self.buttonInstances):
            button.setFixedSize(20, 20)
            button.setStyleSheet('background-color: #4955ff;')
            button.installEventFilter(self)
            # button.pressed.connect(partial(self.open_button, button, i))
            gridLayout.addWidget(button, i//self.cols, i % self.cols)

        hLayWidg = QWidget(cenWidget)
        hLay = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.addItem('BFS')
        self.comboBox.addItem('Dijkstra')
        self.comboBox.addItem('A*')
        self.comboBox.addItem('Best-first')
        hLay.addWidget(QLabel('Choose an algorithm:'))
        hLay.addWidget(self.comboBox)
        hLayWidg.setLayout(hLay)

        vertLayout.addWidget(gridWidget)
        vertLayout.addWidget(hLayWidg)
        vertLayout.setContentsMargins(0, 0, 0, 0)
        vertLayout.setSpacing(0)

        vertLayout.setAlignment(Qt.AlignCenter)

        hLayWidg1 = QWidget(cenWidget)
        hLay1 = QHBoxLayout()
        self.chb = QCheckBox()
        hLay1.addWidget(QLabel('Display search process?:'))
        hLay1.addWidget(self.chb)
        hLayWidg1.setLayout(hLay1)
        vertLayout.addWidget(hLayWidg1)

        hLayWidg2 = QWidget(cenWidget)
        hLay2 = QHBoxLayout()
        startBut = QPushButton("Start")
        startBut.clicked.connect(self.doSearch)
        stopBut = QPushButton("Exit")
        stopBut.clicked.connect(lambda x: sys.exit())
        hLay2.addWidget(startBut)
        hLay2.addWidget(stopBut)
        hLayWidg2.setLayout(hLay2)
        vertLayout.addWidget(hLayWidg2)

        self.setCentralWidget(cenWidget)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if obj.isEnabled():
                    obj.setEnabled(False)
                    obj.setStyleSheet('background-color: #444444;')
                else:
                    obj.setEnabled(True)
                    obj.setStyleSheet('background-color: #4955ff;')
            elif obj.isEnabled():
                index = self.buttonInstances.index(obj)
                row_col_ind = (index//self.cols, index % self.cols)
                imgs = ['../img/finish.png', '../img/start.png']
                if row_col_ind != self.end and row_col_ind != self.start:
                    if event.button() == Qt.RightButton:
                        self.set_start_end(obj, self.end, imgs[0], row_col_ind)
                        self.end = row_col_ind
                    else:
                        self.set_start_end(
                            obj, self.start, imgs[1], row_col_ind)
                        self.start = row_col_ind
        return QObject.event(obj, event)

    def set_start_end(self, obj, point, img_ref, row_col_ind):
        obj.setIcon(QIcon(img_ref))
        obj.setIconSize(QSize(19, 19))
        if point:
            self.buttonInstances[
                int(point[0]*self.cols+point[1])
            ].setIcon(QIcon())

    def doSearch(self):
        array_maze = [
            0 if button.isEnabled() else 1 for button in self.buttonInstances
        ]
        sClass = SearchClass(array_maze, self.comboBox.currentText(), self.cols,
                             self.start, self.end)
        algorithms = {'BFS': sClass.bfs_search,
                      'Dijkstra': sClass.dkstr_search,
                      'A*': sClass.astar_search,
                      'Best-first': sClass.bestfst_search}
        algorithms[self.comboBox.currentText()]()

        try:
            self.show_final_path(sClass)
        except KeyError:
            QMessageBox.question(self, 'No path available',
                        'There is no available path in current layout',
                        QMessageBox.Ok)

    def show_final_path(self, sClass):
        ans = sClass.get_final_path()
        for coord in ans:
            self.buttonInstances[coord[0]*self.cols+coord[1]].setStyleSheet(
                'background-color:#ff0000')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    a = app.exec_()