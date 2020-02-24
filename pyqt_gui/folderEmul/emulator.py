import sys
import os
from functools import partial

from PyQt5.QtWidgets import (QApplication, QShortcut, QLabel, QPushButton,
                             QGridLayout, QWidget, QMainWindow, QLineEdit,
                             QVBoxLayout, QShortcut, QAction, QMessageBox,
                             QHBoxLayout, QComboBox, QCheckBox, QScrollArea)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize


class MyWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 700, 500)
        self.setWindowTitle('Folder imitator')
        self.homeDirectory = os.path.splitdrive(os.getcwd())[0]+'\\'
        self.currentDirectory = self.homeDirectory
        self.setStyleSheet(open('style.css').read())
        
        self.dirStack = [self.homeDirectory]
        self.depthLevel = len(self.dirStack)
        self.initUI()

    def initUI(self):
        # defines central widget and vertical layout for it
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)

        topNavWidg = QWidget()
        topNavLayout = QHBoxLayout(topNavWidg)
        actions = ['back', 'forward', 'home']
        for i in range(3):
            but = QPushButton()
            but.clicked.connect(partial(self.navigate, action=actions[i]))
            but.setIcon(QIcon(f'../img/{actions[i]}.png'))
            but.setIconSize(QSize(25, 25))
            topNavLayout.addWidget(but)
        self.curPathLine = QLineEdit()
        self.curPathLine.setText(self.currentDirectory)
        self.curPathLine.installEventFilter(self)
        topNavLayout.addWidget(self.curPathLine)
        mainVertLayout.addWidget(topNavWidg)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        viewWidg = QWidget()
        viewVertLayout = QVBoxLayout(viewWidg)
        viewVertLayout.installEventFilter(self)
        viewVertLayout.setAlignment(Qt.AlignTop)
        viewVertLayout.setSpacing(0)
        viewVertLayout.setContentsMargins(3, 3, 3, 3)
 
        self.files = [QLabel(filename) for filename in self.getDirList()]
        for f in self.files:
            f.setProperty('selected', False)
            f.installEventFilter(self)
            viewVertLayout.addWidget(f)

        scroll.setWidget(viewWidg)

        mainVertLayout.addWidget(scroll)
        mainVertLayout.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setAlignment(Qt.AlignLeft)

        self.setCentralWidget(cenWidget)

    def getDirList(self):
        return sorted(os.listdir(self.currentDirectory), 
            key=lambda x : 1 if os.path.isdir(os.path.join(
            self.currentDirectory, x)) and not x.endswith('.BIN') else 2)

    def navigate(self, action):
        if action == 'back':
            if self.currentDirectory != self.homeDirectory:
                self.currentDirectory = os.path.split(self.currentDirectory)[0]
                self.depthLevel -= 1
                print(self.depthLevel, self.dirStack)
        elif action == 'forward':
            if len(self.dirStack) > self.depthLevel:
                self.openPath(self.dirStack[self.depthLevel])
                print(self.depthLevel, self.dirStack)
        elif action == 'home':
            self.openPath(self.homeDirectory)
        self.initUI()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if not obj.property('selected'):
                    obj.setProperty('selected', True)
                else:
                    obj.setProperty('selected', False)
                obj.setStyleSheet('')
        if event.type() == QEvent.MouseButtonDblClick:
            self.openPath(os.path.join(self.currentDirectory, obj.text()))
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Down:
                self.files[self.files.index(obj)+1].setProperty('selected', True)
            if event.key() == Qt.Key_Return and obj == self.curPathLine:
                self.openPath(self.curPathLine.text())

        return QObject.event(obj, event)

    def openPath(self, path):
        if os.path.exists(path):
            if os.path.isfile(path):
                os.startfile(path)
            elif self.currentDirectory != path:
                print(self.depthLevel, self.dirStack)
                try:
                    if self.dirStack[self.depthLevel] != path:
                        self.dirStack[self.depthLevel:] = [path]
                except IndexError:
                    self.dirStack.append(path)
                self.depthLevel += 1
                print(self.depthLevel, self.dirStack)
                self.currentDirectory = path
                self.initUI()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    a = app.exec_()
