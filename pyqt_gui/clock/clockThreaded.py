import sys
import datetime
import time
from functools import partial

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QTimeEdit, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSlot, pyqtSignal


# class with main functions for threading functionality
class Worker(QObject):
    # signals for communicating with PyQT application for each tool respectively
    currentTimeSign = pyqtSignal(str)
    stopwatchSign = pyqtSignal(str)
    timerSign = pyqtSignal(str)

    # flag variable for stopping loops of main functions
    run = True

    # clock function (returns current time)
    @pyqtSlot()
    def returnTime(self):
        while self.run:
            timeNow = datetime.datetime.now().strftime('%H:%M:%S')
            self.currentTimeSign.emit(timeNow)
            time.sleep(0.01)

    # stopwatch function, takes initialTime (previous stopwatch time if it was
    # paused earlier) and return difference between now and start time
    @pyqtSlot(datetime.timedelta)
    def returnStopwatch(self, initialTime):
        startTime = datetime.datetime.now()
        while self.run == True:
            now = datetime.datetime.now()
            diff = now + initialTime - startTime
            self.stopwatchSign.emit(str(diff)[:-4])
            time.sleep(0.01)

    # timer function, takes time that was set on timer and returns difference
    # between time now and time that was set + time when timer was set
    @pyqtSlot(datetime.datetime)
    def returnTimer(self, timerT):
        timerTime = (datetime.timedelta(minutes=timerT.minute,
                                       seconds=timerT.second) 
                                       + datetime.datetime.now())
        while datetime.datetime.now() < timerTime and self.run:
            diff = timerTime - datetime.datetime.now()
            self.timerSign.emit(str(diff)[2:-7])
            time.sleep(0.01)
        # check if timer stopped because time passed and not because user 
        # stopped it
        if datetime.datetime.now() >= timerTime:
            self.timerSign.emit('passed')


class MyWindow(QMainWindow):

    # signals for communicating with worker class
    clockStart = pyqtSignal()
    stopwatchStart = pyqtSignal(datetime.timedelta)
    timerStart = pyqtSignal(datetime.time)

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 1, 1)
        self.setWindowTitle('Stopwatch/timer')
        self.setWindowIcon(QIcon('../img/clock.png'))
        self.setStyleSheet(open('style.css').read())
        # group of tools that available in the app
        self.tools = ['Clock', 'Stopwatch', 'Timer']
        # current tool
        self.tool = self.tools[0]
        # time for stopwatch tool
        self.initialTime = datetime.timedelta(hours=0, minutes=0, seconds=0)

        # initialize instanse of worker class as well as instanse of threading
        # class connect signals with it's destination functions
        self.worker = Worker()
        self.workerThread = QThread()
        self.workerThread.start()
        self.worker.moveToThread(self.workerThread)
        # connect signals of mainWindow app to the methods of Worker class
        # instance
        self.clockStart.connect(self.worker.returnTime)
        self.stopwatchStart.connect(self.worker.returnStopwatch)
        self.timerStart.connect(self.worker.returnTimer)
        # connect signals of Worker class instance the methods of mainWindow app
        self.worker.currentTimeSign.connect(self.setTime)
        self.worker.stopwatchSign.connect(self.setStopwatch)
        self.worker.timerSign.connect(self.setTimer)

        # choose specific tool and initialize layout
        self.changeTools(self.tool)
        self.initUI()

    def initUI(self):
        # create central widget and main vertical layout
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setContentsMargins(1, 1, 1, 1)
        # create button widget and horizontal layout for buttons to select the
        # tool
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

        # set different main widgets depending on tool selected
        if self.tool == 'Clock':
            self.mainWidg = QLabel()
        if self.tool == 'Stopwatch':
            if str(self.initialTime) == '0:00:00':
                self.mainWidg = QLabel(str(self.initialTime))
            else:
                self.mainWidg = QLabel(str(self.initialTime)[:-4])
            # scroll widget for lap times
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            lapWidg = QWidget()
            self.lapVertLayout = QVBoxLayout(lapWidg)
            self.lapVertLayout.setAlignment(Qt.AlignTop)
            self.lapVertLayout.setSpacing(0)
            self.lapVertLayout.setContentsMargins(3, 3, 3, 3)
            scroll.setWidget(lapWidg)
        if self.tool == 'Timer':
            if not self.started:
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

        # add buttons depending on on tool selected and state of programm
        # (started, paused)
        butWidg = QWidget()
        butLay = QHBoxLayout(butWidg)
        if self.tool in ['Stopwatch', 'Timer']:
            if not self.started:
                self.startBut = QPushButton('Start')
                self.startBut.clicked.connect(self.startTool)
                butLay.addWidget(self.startBut)
            elif self.tool == 'Stopwatch' and self.started:
                self.startBut = QPushButton('Pause')
                self.startBut.clicked.connect(self.setPause)
                butLay.addWidget(self.startBut)
                lapBut = QPushButton('Lap')
                lapBut.clicked.connect(self.addLap)
                butLay.addWidget(lapBut)
            if (self.tool == 'Stopwatch' and self.paused
                    or self.tool == 'Timer' and self.started):
                stopBut = QPushButton('Stop')
                stopBut.clicked.connect(partial(self.changeTools, self.tool))
                butLay.addWidget(stopBut)
        butLay.setSpacing(2)
        butLay.setContentsMargins(0, 0, 0, 0)
        mainVertLayout.addWidget(butWidg)

        self.setCentralWidget(cenWidget)

    # set tool based on input and set everything to default state
    def changeTools(self, tool):
        self.worker.run = False
        time.sleep(0.02)
        self.tool = tool
        self.started = False
        self.paused = False
        if tool == 'Stopwatch':
            self.laps = []
            self.initialTime = datetime.timedelta(
                hours=0, minutes=0, seconds=0)
        self.initUI()
        if tool == 'Clock':
            self.startTool()

    # do specific operation to run tool that is currently selected
    def startTool(self):
        if self.tool == 'Clock':
            self.worker.run = True
            self.clockStart.emit()
        elif self.tool == 'Stopwatch':
            self.paused = False
            self.started = True
            self.initUI()
            self.worker.run = True
            self.stopwatchStart.emit(self.initialTime)
        else:
            self.started = True
            self.worker.run = True
            # convert qtime timer to python time to work with it in worker
            # instatnce
            time = self.mainWidg.time().toPyTime()
            self.initUI()
            self.timerStart.emit(time)

    # method for pausing stopwatch
    def setPause(self):
        # stop loop in worker instanse
        self.worker.run = False
        self.paused = True
        # split current stopwatch time into hours, minutes and seconds
        time = list(map(int, self.mainWidg.text()[:-3].split(':')))
        # save initial save that time to continue stopwatch from it later
        self.initialTime = datetime.timedelta(
            hours=time[0], minutes=time[1], seconds=time[2],
            milliseconds=int(self.mainWidg.text()[-2:]))
        # set state to not started and repaint UI
        self.started = False
        self.initUI()

    def setTime(self, time):
        self.mainWidg.setText(time)

    def setStopwatch(self, time):
        self.mainWidg.setText(time)

    def setTimer(self, time):
        # if signal that time passed is sent display message about it and set
        # values to default
        if time == 'passed':
            QMessageBox.information(self, 'Time is up!',
                                    'The time you set has passed!', 
                                    QMessageBox.Ok)
            self.changeTools(self.tool)
        # else set text of main widget to the accepted value
        else:
            self.mainWidg.setText(time)

    # method for adding laps from stopwatch
    def addLap(self):
        lapTime = self.mainWidg.text()[:-3]
        # if there is any previous laps get last lap and calculate difference
        # between it and current time
        try:
            prevLap = datetime.datetime.strptime(self.laps[-1][0], '%H:%M:%S')
            diff = datetime.datetime.strptime(lapTime, '%H:%M:%S') - prevLap
        # if not, set difference to 0
        except IndexError:
            diff = '0:00:00'
        # add new lap to the dictionary and add it to the scroll widget as label
        self.laps.append((lapTime, str(diff)))
        newLap = QLabel(f'{lapTime}   +{diff}')
        newLap.setAlignment(Qt.AlignCenter)
        self.lapVertLayout.addWidget(newLap)

    # things to do when app is closed
    def closeEvent(self, event):
        self.worker.run = False
        self.workerThread.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())