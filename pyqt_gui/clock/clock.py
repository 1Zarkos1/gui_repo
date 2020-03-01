import sys
import os
from functools import partial
import datetime

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget, 
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QTimeEdit)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize


class MyWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 1, 1)
        self.setWindowTitle('Stopwatch/timer')
        self.setWindowIcon(QIcon('../img/clock.png'))
        self.setStyleSheet(open('style.css').read())
        self.timeNow = datetime.datetime.now().strftime('%H:%M:%S')
        self.tools = ['Clock', 'Stopwatch', 'Timer']       
        self.tool = self.tools[0]
        self.initialTime = datetime.timedelta(hours=0, minutes=0, seconds=0)
        self.timerTime = None
        self.changeTools(self.tool)

    def initUI(self):
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setContentsMargins(1, 1, 1, 1)

        toolsWidg = QWidget()
        toolsLay = QHBoxLayout(toolsWidg)
        for tool in self.tools:
            but = QPushButton(tool)
            but.setObjectName('toolBut')
            but.clicked.connect(partial(self.changeTools, tool))
            toolsLay.addWidget(but)
        toolsLay.setSpacing(2)
        toolsLay.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.addWidget(toolsWidg)

        if self.tool == 'Clock':
            self.mainWidg = QLabel(self.timeNow)

        if self.tool == 'Stopwatch':
            if str(self.initialTime) == '0:00:00':
                self.mainWidg = QLabel(str(self.initialTime))
            else:
                self.mainWidg = QLabel(str(self.initialTime)[:-4])
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            lapWidg = QWidget()
            self.lapVertLayout = QVBoxLayout(lapWidg)
            self.lapVertLayout.setAlignment(Qt.AlignTop)
            self.lapVertLayout.setSpacing(0)
            self.lapVertLayout.setContentsMargins(3, 3, 3, 3)
            scroll.setWidget(lapWidg)

        if self.tool == 'Timer':
            if not self.timerSet:     
                self.mainWidg = QTimeEdit()
                self.mainWidg.setDisplayFormat('mm:ss')
            else:
                time = self.mainWidg.time().toPyTime()
                self.mainWidg = QLabel(time.strftime('%H:%M:%S'))

        self.mainWidg.setAlignment(Qt.AlignCenter)
        self.mainWidg.setObjectName('MainWidget')
        mainVertLayout.addWidget(self.mainWidg)
        if self.tool == 'Stopwatch':
            mainVertLayout.addWidget(scroll)


        butWidg = QWidget()
        butLay = QHBoxLayout(butWidg)
        if self.tool == 'Clock':
            self.startBut = QPushButton('Start')
            self.startBut.clicked.connect(self.startTool)
            butLay.addWidget(self.startBut)

        if self.tool in ['Stopwatch', 'Timer']:
            if not self.started:
                self.startBut = QPushButton('Start')
                self.startBut.clicked.connect(self.startTool)
                butLay.addWidget(self.startBut)
            else:
                self.startBut = QPushButton('Pause')
                self.startBut.clicked.connect(self.setPause)
                butLay.addWidget(self.startBut)
            
            if self.tool == 'Stopwatch' and self.started:
                lapBut = QPushButton('Lap')
                lapBut.clicked.connect(self.addLap)
                butLay.addWidget(lapBut)
            else:
                stopBut = QPushButton('Stop')
                stopBut.clicked.connect(partial(self.changeTools, self.tool))
                butLay.addWidget(stopBut)
        
        butLay.setSpacing(2)
        butLay.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.addWidget(butWidg)

        self.setCentralWidget(cenWidget)

    def changeTools(self, tool):
        self.tool = tool
        self.timerSet = False
        self.paused = False
        self.started = False
        if tool == 'Stopwatch':
            self.laps = []
            self.prevTime = None
            self.initialTime = datetime.timedelta(hours=0, minutes=0, seconds=0)

        self.initUI()

    def startTool(self):
        if self.tool == 'Clock':
            if self.started:
                self.started = False
                self.startBut.setText('Start')
            else:
                self.started = True
                self.startBut.setText('Pause')
                self.clock()
        if self.tool == 'Stopwatch':
            self.paused = False
            self.started = True
            self.initUI()
            self.stopwatch()
        else:
            self.started = True
            self.timer()

    def setPause(self):
        self.paused = True
        time = list(map(int, self.mainWidg.text()[:-3].split(':')))
        self.initialTime = datetime.timedelta(
            hours=time[0], minutes=time[1], seconds=time[2], 
            milliseconds=int(self.mainWidg.text()[-2:]))
        self.started = False
        self.initUI()

    def clock(self):
        while self.tool == 'Clock' and self.started:
            timeNow = datetime.datetime.now().strftime('%H:%M:%S')
            self.mainWidg.setText(timeNow)
            self.update()
            QApplication.processEvents()

    def stopwatch(self):
        startTime = datetime.datetime.now()
        while self.tool == 'Stopwatch' and self.started and not self.paused:
            now = datetime.datetime.now()
            diff = now + self.initialTime - startTime
            self.mainWidg.setText(str(diff)[:-4])
            self.update()
            QApplication.processEvents()

    def addLap(self):
        lapTime = self.mainWidg.text()[:-3]
        try:
            prevLap = datetime.datetime.strptime(self.laps[-1][0], '%H:%M:%S')
            diff = datetime.datetime.strptime(lapTime, '%H:%M:%S') - prevLap
        except IndexError:
            diff = '0:00:00'
        self.laps.append((lapTime, str(diff)))
        newLap = QLabel(f'{lapTime}   +{diff}')
        newLap.setAlignment(Qt.AlignCenter)
        self.lapVertLayout.addWidget(newLap)

    def timer(self):
        timeNow = datetime.datetime.now()
        time = self.mainWidg.time().toPyTime()
        self.timerSet = True
        self.initUI()
        timerTime = datetime.timedelta(minutes=time.minute, seconds=time.second) + timeNow
        while timeNow <= timerTime and self.timerSet:
            dif = timerTime - timeNow
            self.mainWidg.setText(str(dif)[2:-7])
            self.update()
            QApplication.processEvents()
            timeNow = datetime.datetime.now()
        self.changeTools(self.tool)

    # function for dynamicaly changing styles of elements
    def updateStyle(self, obj):
        obj.style().unpolish(obj)
        obj.style().polish(obj)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()