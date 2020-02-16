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
        # defines central widget and vertical layout for it
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        # defines grid widget and main field as group of buttons, styles them
        # and adds to layout
        gridWidget = QWidget()
        gridLayout = QGridLayout(gridWidget)
        gridLayout.setSpacing(0)
        gridWidget.setLayout(gridLayout)
        self.button_size = 20
        self.buttonInstances = [QPushButton()
                                for num in range(self.rows*self.cols)]
        for i, button in enumerate(self.buttonInstances):
            button.setFixedSize(self.button_size, self.button_size)
            button.setStyleSheet('background-color: #4955ff;')
            button.installEventFilter(self)
            gridLayout.addWidget(button, i//self.cols, i % self.cols)
        # define horizontal widget and add combo box with label to choose
        # algorithm
        algWidg = QWidget(cenWidget)
        algLayout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.addItem('BFS')
        self.comboBox.addItem('Dijkstra')
        self.comboBox.addItem('A*')
        self.comboBox.addItem('Best-first')
        algLayout.addWidget(QLabel('Choose an algorithm:'))
        algLayout.addWidget(self.comboBox)
        algWidg.setLayout(algLayout)
        # add widgets to the main layout
        mainVertLayout.addWidget(gridWidget)
        mainVertLayout.addWidget(algWidg)
        mainVertLayout.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setAlignment(Qt.AlignCenter)
        # add label and checkbox for displaying cells processed during
        # pathfinding
        chBLayerWidg = QWidget(cenWidget)
        checkBoxLayout = QHBoxLayout()
        self.chb = QCheckBox()
        checkBoxLayout.addWidget(QLabel('Display search process?:'))
        checkBoxLayout.addWidget(self.chb)
        chBLayerWidg.setLayout(checkBoxLayout)
        mainVertLayout.addWidget(chBLayerWidg)
        # add functional buttons with horizontal layout
        funcButtonsWidg = QWidget(cenWidget)
        funcButtonsLayout = QHBoxLayout()
        startBut = QPushButton("Start")
        startBut.clicked.connect(self.doSearch)
        clearBut = QPushButton("Clear")
        clearBut.clicked.connect(self.clearField)
        stopBut = QPushButton("Exit")
        stopBut.clicked.connect(lambda x: sys.exit())
        funcButtonsLayout.addWidget(startBut)
        funcButtonsLayout.addWidget(clearBut)
        funcButtonsLayout.addWidget(stopBut)
        funcButtonsWidg.setLayout(funcButtonsLayout)
        mainVertLayout.addWidget(funcButtonsWidg)

        self.setCentralWidget(cenWidget)

    # defines what to do when certain mouse buttons are pressed on cells
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
                # index of buttosn in 2d array
                rowColInd = (index//self.cols, index % self.cols)
                imgs = ['../img/finish.png', '../img/start.png']
                if rowColInd != self.end and rowColInd != self.start:
                    if event.button() == Qt.RightButton:
                        self.setStartEndIcons(obj, self.end, imgs[0], rowColInd)
                        self.end = rowColInd
                    else:
                        self.setStartEndIcons(
                            obj, self.start, imgs[1], rowColInd)
                        self.start = rowColInd
        return QObject.event(obj, event)

    # set and del icons for start and end destination points
    def setStartEndIcons(self, obj, point, img_ref, rowColInd):
        obj.setIcon(QIcon(img_ref))
        obj.setIconSize(QSize(self.button_size-2, self.button_size-2))
        if point:
            self.buttonInstances[
                int(point[0]*self.cols+point[1])
            ].setIcon(QIcon())

    # main function that defines searchClass object, and calls it's seatch
    # method the calls function for showing founded path and, based on wheter or
    # not user wants to see processed cells calls that function accordingly
    def doSearch(self):
        # check if start and end points are defined, if not display message
        if not self.start or not self.end:
            return QMessageBox.question(self, 'Start/end not defined',
                                        'Please set up your start/end points\n'
                                        '(use middle and rights buttons of the mouse)',
                                        QMessageBox.Ok)
        # translate maze from buttons to simple array
        arrayMaze = [
            0 if button.isEnabled() else 1 for button in self.buttonInstances
        ]
        # create main working class and call it's search function
        sClass = SearchClass(arrayMaze, self.comboBox.currentText(), self.cols,
                             self.start, self.end)
        sClass.do_search()

        # if user wants all cells processed by algorithm, by checking checkbox
        # widget - display them
        if self.chb.isChecked():
            self.displayProcessedCells(sClass)

        # display path if it's been found else print message that no path
        # is found
        try:
            self.showPath(sClass)
        except KeyError:
            QMessageBox.question(self, 'No path found',
                                 'There is no available path in current layout',
                                 QMessageBox.Ok)

    # diplay cells processed by algorithm
    def displayProcessedCells(self, sClass):
        for coord in sClass.came_from.keys():
            self.buttonInstances[coord[0]*self.cols+coord[1]].setStyleSheet(
                'background-color:#00ff00')

    # return field and variables to their initial states
    def clearField(self):
        self.initUI()
        self.start = None
        self.stop = None

    # display path found by an algorithm
    def showPath(self, sClass):
        ans = sClass.get_final_path()
        for coord in ans:
            self.buttonInstances[coord[0]*self.cols+coord[1]].setStyleSheet(
                'background-color:#ff0000')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    a = app.exec_()