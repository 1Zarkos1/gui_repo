import sys
import os
from functools import partial
import datetime
import socket
import selectors
import types
import time
import json

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget, 
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QTimeEdit)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, pyqtSignal, pyqtSlot, QThread


class SocketWork(QObject):

    messageSignal = pyqtSignal(dict)

    def __init__(self, userType, name, host, port):
        super().__init__()
        self.type = userType
        self.name = name
        self.sel = selectors.DefaultSelector()
        self.host, self.port = host, port
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pendingMessages = []
        self.run = True

    @pyqtSlot()
    def startConnection(self):
        if self.type == 'server':
            self.lsock.bind((self.host, self.port))
            self.lsock.listen(3)
            self.lsock.setblocking(False)
            self.sel.register(self.lsock, selectors.EVENT_READ, data='Server')
        else:
            self.lsock.connect_ex((self.host, self.port))
            # self.lsock.send(str(int(self.name)).encode('utf-8'))
            # self.lsock.send(self.name.encode('utf-8'))
            self.lsock.setblocking(False)
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            self.sel.register(self.lsock, events, data=self.name)
        try:
            while self.run:
                events = self.sel.select()
                for key, mask in events:
                    if key.data == 'Server':
                        self.accept_wrapper(key.fileobj)
                    else:
                        result = self.service_connection(key, mask)
                        if result == 'received': 
                            break
                else:
                    if self.pendingMessages:
                        self.pendingMessages.pop(0)
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self.run = False
            self.sel.close()

    def translateMessage(self, message):
        if type(message) == bytes:
            message = json.loads(message.decode('utf-8'))
            return message
        elif type(message) == dict:
            message = json.dumps(message).encode('utf-8')
            return message


    def accept_wrapper(self, sock):
        conn, addr = sock.accept()
        # header = conn.recv(2)
        # name = conn.recv(int(header.decode('utf-8')))
        conn.setblocking(False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data='_client')
        # print(f'accepted {name}')

    def service_connection(self, key, mask):
        sock = key.fileobj
        if mask & selectors.EVENT_READ:
            header = sock.recv(5)
            if header.decode('utf-8') == '_quit':
                self.sel.unregister(sock)
                sock.close()
            if header:
                sock.setblocking(True)
                message = self.translateMessage(sock.recv(int(header)))
                sock.setblocking(False)
                self.messageSignal.emit(message)
                # if key.data == '_client':
                #     key.data = message['name']
                if self.type == 'server':
                    self.pendingMessages.append(message)
                    return 'received'
                # else:
                # self.messageSignal.emit(message)
        if mask & selectors.EVENT_WRITE:
            if self.pendingMessages:
                message = self.translateMessage(self.pendingMessages[0])
                sock.send(f"{len(message):5}".encode('utf-8'))
                sock.send(message)
                # if self.type == 'server':
                #     self.messageSignal.emit(self.pendingMessages[0])  # Should be ready to write

class MyWindow(QMainWindow):

    startSign = pyqtSignal()

    def __init__(self, userType, name, host, port, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 400, 500)
        self.setWindowTitle(f'PyQT messanger - as {name}')
        self.setWindowIcon(QIcon('../img/message.png'))
        # self.setStyleSheet(open('style.css').read())
        self.name = name
        self.type = userType

        self.soket = SocketWork(userType, name, host, port)
        self.threadWork = QThread()
        self.threadWork.start()
        self.soket.moveToThread(self.threadWork)
        self.soket.messageSignal.connect(self.addMessage)
        self.startSign.connect(self.soket.startConnection)
        self.startSign.emit()

        self.initUI()

    def initUI(self):
        cenWidget = QWidget(self)
        mainVertLayout = QVBoxLayout(cenWidget)
        mainVertLayout.setSpacing(0)
        mainVertLayout.setContentsMargins(1, 1, 1, 1)
        mainVertLayout.addWidget(QLabel('Chat messages:'))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        butWidg = QWidget()
        self.chatLay = QVBoxLayout(butWidg)
        self.chatLay.setAlignment(Qt.AlignTop)
        self.chatLay.setSpacing(2)
        self.chatLay.setContentsMargins(3, 3, 3, 3)
        scroll.setWidget(butWidg)
        mainVertLayout.addWidget(scroll)

        butWidg = QWidget()
        butLay = QHBoxLayout(butWidg)
        self.messageInput = QLineEdit(butWidg)
        self.messageInput.returnPressed.connect(self.queueMessage)
        butLay.addWidget(self.messageInput)
        butLay.addWidget(QPushButton('Send', clicked=self.queueMessage))
        butWidg.setLayout(butLay)
        butLay.setSpacing(2)
        butLay.setContentsMargins(1, 1, 1, 1)
        mainVertLayout.addWidget(butWidg)

        self.setCentralWidget(cenWidget)

    def queueMessage(self):
        if self.messageInput.text():
            message = {'name': self.name, 
                    'time': datetime.datetime.now().strftime("%H:%M"),
                    'text': self.messageInput.text()}
            if self.type == 'server':
                self.addMessage(message)
            self.soket.pendingMessages.append(message)
            self.messageInput.setText('')
    
    def addMessage(self, message):
        messageWidget = QLabel(f'<b>{message["name"]} <i>at {message["time"]}:</b><br>'
                             f'{message["text"]}')
        messageWidget.setWordWrap(True)
        messageWidget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.chatLay.addWidget(messageWidget)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        # run the code first with given parameters then chage 'server' to 
        # something else, change username and run again
        window = MyWindow('server', 'User1', '127.0.0.1', 65530)
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(e)