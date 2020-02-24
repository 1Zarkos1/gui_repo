import sys
import os
from functools import partial

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget, 
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout, 
                             QScrollArea)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize


class MyWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 700, 500)
        self.setWindowTitle('Folder imitator')
        # set home directory as root of your current working directory
        self.homeDirectory = os.path.splitdrive(os.getcwd())[0]+os.path.sep
        self.currentDirectory = self.homeDirectory
        # set styes in css format
        self.setStyleSheet(open('style.css').read())
        # some holder for current selected element (holding index of selected
        # file in self.files
        self.selected = None
        # visited direcotries as list to 'forward' button functionality
        self.dirStack = [self.homeDirectory]
        # how far you get from root directory (for forward button)
        self.depthLevel = len(self.dirStack)
        self.initUI()

    def initUI(self):
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        # widget and horizontal layout for functional buttons and address bar
        topNavWidg = QWidget()
        topNavLayout = QHBoxLayout(topNavWidg)
        actions = ['back', 'forward', 'home']
        for i in range(3):
            but = QPushButton()
            but.clicked.connect(partial(self.navigate, action=actions[i]))
            but.setIcon(QIcon(f'../img/{actions[i]}.png'))
            but.setIconSize(QSize(25, 25))
            topNavLayout.addWidget(but)
        # address bar
        self.curPathLine = QLineEdit()
        self.curPathLine.setText(self.currentDirectory)
        self.curPathLine.installEventFilter(self)
        topNavLayout.addWidget(self.curPathLine)
        mainVertLayout.addWidget(topNavWidg)
        # scroll area and vertical layout for viewing current directory files
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        viewWidg = QWidget()
        viewVertLayout = QVBoxLayout(viewWidg)
        viewVertLayout.installEventFilter(self)
        viewVertLayout.setAlignment(Qt.AlignTop)
        viewVertLayout.setSpacing(0)
        viewVertLayout.setContentsMargins(3, 3, 3, 3)
        # make label for each directory and file directly in current folder
        self.files = [QLabel(filename) for filename in self.getDirList()]
        for f in self.files:
            f.installEventFilter(self)
            viewVertLayout.addWidget(f)

        scroll.setWidget(viewWidg)

        mainVertLayout.addWidget(scroll)
        mainVertLayout.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setAlignment(Qt.AlignLeft)

        self.setCentralWidget(cenWidget)

    # returns list of files and subfolders in current directory sorted so that
    # folders come before files
    def getDirList(self):
        return sorted(os.listdir(self.currentDirectory), 
            key=lambda x : 1 if os.path.isdir(os.path.join(
            self.currentDirectory, x)) and not x.endswith('.BIN') else 2)

    # functionality for navigation buttons
    def navigate(self, action):
        if action == 'back':
            if self.currentDirectory != self.homeDirectory:
                self.currentDirectory = os.path.split(self.currentDirectory)[0]
                self.depthLevel -= 1
        elif action == 'forward':
            # if direcory stack consist of more levels than the level you are
            # currently on - go to that folder
            if len(self.dirStack) > self.depthLevel:
                self.openPath(self.dirStack[self.depthLevel])
        elif action == 'home':
            self.openPath(self.homeDirectory)
        self.initUI()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # if there already selected file unselect it
                if self.selected and self.files[self.selected] != obj:
                    self.files[self.selected].setProperty('selected', None)
                    self.updateStyle(self.files[self.selected])
                # if current object is not selected - select it and update
                # selected index
                if obj.property('selected') == None:
                    obj.setProperty('selected', True)
                    self.selected = self.files.index(obj)
                # if current object is selected - unselect it
                else:
                    obj.setProperty('selected', None)
                    self.selected = None
                self.updateStyle(obj)
        # open directory or file if it's double clicked
        if event.type() == QEvent.MouseButtonDblClick:
            self.openPath(os.path.join(self.currentDirectory, obj.text()))
        if event.type() == QEvent.KeyPress:
            # for selecting files/directories by keys (dev)
            # if event.key() == Qt.Key_Down:
            #     self.files[self.files.index(obj)+1].setProperty('selected', True)
            # go to directory by typing it in address bar and pressing enter
            if event.key() == Qt.Key_Return and obj == self.curPathLine:
                self.openPath(self.curPathLine.text())

        return QObject.event(obj, event)

    # function for dynamicaly changing styles of elements
    def updateStyle(self, obj):
        obj.style().unpolish(obj)
        obj.style().polish(obj)

    # function opens given path and determens if it's file or directory and
    # procceedes with it accordingly
    def openPath(self, path):
        if os.path.exists(path):
            if os.path.isfile(path):
                os.startfile(path)
            elif self.currentDirectory != path:
                # check is path on current level is the same as the one in saved
                # stack if not rewrite stack from that level
                try:
                    if self.dirStack[self.depthLevel] != path:
                        self.dirStack[self.depthLevel:] = [path]
                # if there is no paht on that level just add it in stack
                except IndexError:
                    self.dirStack.append(path)
                # update depth level (because you gone up 1 level) and current
                # directory
                self.depthLevel += 1
                self.currentDirectory = path
                self.initUI()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()