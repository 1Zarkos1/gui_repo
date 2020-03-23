import sys
import datetime
import socket
import selectors
import json
import traceback

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QTimeEdit, QCheckBox)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, pyqtSignal, pyqtSlot, QThread


class SocketWork(QObject):

    messageSignal = pyqtSignal(dict)
    usersChanged = pyqtSignal()

    def __init__(self, userType, name, host, port):
        super().__init__()
        self.type = userType
        self.name = name
        self.sel = selectors.DefaultSelector()
        self.host, self.port = host, port
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.userList = {}
        self.pendingMessages = []
        self.run = True
        self.encoding = 'utf-8'
        self.sendUserListTo = []

    @pyqtSlot()
    def startConnection(self):
        if self.type == 'server':
            self.lsock.bind((self.host, self.port))
            self.lsock.listen(3)
            self.lsock.setblocking(False)
            self.sel.register(self.lsock, selectors.EVENT_READ, data='Server')
        else:
            self.lsock.connect_ex((self.host, self.port))
            self.lsock.setblocking(False)
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            self.sel.register(self.lsock, events, data='Client')
        try:
            while self.run:
                events = self.sel.select()
                for key, mask in events:
                    if key.data == 'Server':
                        self.acceptUser(key.fileobj)
                    else:
                        result = self.communicate(key, mask)
                        if result == 'received':
                            break
                else:
                    if self.pendingMessages:
                        self.pendingMessages.pop(0)
        except Exception as excp:
            *_, tb = sys.exc_info()
            print('before traceback')
            traceback.print_tb(tb)
            print("caught keyboard interrupt, exiting")
            print(excp)
        finally:
            pass

    def closeConnection(self, sock=None):
        if sock == None or self.type != 'server':
            while self.sel.get_map() and len(self.sel.get_map()) > 1:
                events = self.sel.select()
                for key, mask in events:
                    if selectors.EVENT_WRITE and mask:
                        key.fileobj.send('_quit'.encode(self.encoding)) 
                        self.sel.unregister(key.fileobj)
                        key.fileobj.close()
            self.run = False
            self.sel.close()
        else:
            del self.userList[sock.getpeername()]
            self.usersChanged.emit()
            self.sel.unregister(sock)
            sock.close()
            return '_quit'

    def translateMessage(self, message):
        if type(message) == bytes:
            message = json.loads(message.decode(self.encoding))
        elif type(message) == dict or type(message) == list:
            message = json.dumps(message).encode(self.encoding)
        return message

    def acceptUser(self, sock):
        conn, _ = sock.accept()
        conn.setblocking(False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data='_client')

    def receiveSysMessage(self, sock, header):
        if header == '_quit':
            return self.closeConnection(sock)
        elif header == '_name':
            if self.type == 'server':
                sock.setblocking(True)
                lenHeader = int(sock.recv(5).decode(self.encoding))
                username = sock.recv(lenHeader).decode(self.encoding)
                sock.setblocking(False)
                print(username, self.userList.values())
                if username in self.userList.values():
                    print('unreg.host')
                    self.closeConnection(sock)
                    print('signal emmited')
                else:
                    print(f'received {username}')
                    userAddress = sock.getpeername()
                    self.userList[userAddress] = username
                    self.sendUserListTo.append(userAddress)
                    self.usersChanged.emit()
        elif header == 'users' and self.type != 'server':
            sock.setblocking(True)
            print(f'its header {header}')
            lenHeader = int(sock.recv(5).decode(self.encoding))
            print(f'its lenHeader {lenHeader}')
            userList = self.translateMessage(sock.recv(lenHeader))
            print(f'its userList {userList}')
            sock.setblocking(False)
            self.userList = {i:value for i, value in enumerate(userList)}
            print('emit for users')
            self.usersChanged.emit()

    def sendSysMessage(self, sock, header):
        userAddress = sock.getpeername()
        if self.type == 'server' and userAddress not in self.userList:
            sock.send('_name'.encode(self.encoding))
            self.userList[userAddress] = None
            print('ask message send')
        elif self.type != 'server' and header == '_name':
            name = self.name.encode(self.encoding)
            print('sending _name')
            sock.send('_name'.encode(self.encoding))
            print('sending header')
            sock.send(f"{len(name):05}".encode(self.encoding))
            print('sending name')
            sock.send(name)
            print('name send')
        elif (self.sendUserListTo != [] and self.sendUserListTo[0] 
                == userAddress):
            print(f' hey its me {list(self.userList.values())}')
            currentUsers = self.translateMessage(list(self.userList.values()))
            print(currentUsers.decode(self.encoding))
            sock.setblocking(True)
            sock.send('users'.encode(self.encoding))
            sock.send(f"{len(currentUsers):05}".encode(self.encoding))
            print('sending name')
            sock.send(currentUsers)
            sock.setblocking(False)
            print('name send')
            self.sendUserListTo.pop(0)

    def communicate(self, key, mask):
        sock = key.fileobj
        receivedHeader = ''
        if mask & selectors.EVENT_READ:
            header = sock.recv(5)
            if header:
                receivedHeader = header.decode(self.encoding)
                if receivedHeader.isnumeric():
                    sock.setblocking(True)
                    message = self.translateMessage(
                        sock.recv(int(receivedHeader)))
                    sock.setblocking(False)
                    self.messageSignal.emit(message)
                    if self.type == 'server':
                        self.pendingMessages.append(message)
                        return 'received'
                else:
                    result = self.receiveSysMessage(sock, receivedHeader)
                    if result == '_quit':
                        return

        if mask & selectors.EVENT_WRITE:
            self.sendSysMessage(sock, receivedHeader)
            if self.pendingMessages:
                message = self.pendingMessages[0]
                if (self.type != 'server' or message['name'] 
                        != self.userList[sock.getpeername()]):
                    byteMessage = self.translateMessage(message)
                    sock.send(f"{len(byteMessage):05}".encode(self.encoding))
                    sock.send(byteMessage)


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
        self.soket.usersChanged.connect(self.showUserList)
        self.startSign.connect(self.soket.startConnection)
        self.startSign.emit()

        self.soket.userList[(host, port)] = name

        self.initUI()

    def initUI(self):
        cenWidget = QWidget(self)
        self.mainVertLayout = QVBoxLayout(cenWidget)
        self.mainVertLayout.setSpacing(0)
        self.mainVertLayout.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(QLabel('Chat messages:'))

        self.messageScroll = QScrollArea()
        self.messageScroll.setWidgetResizable(True)
        self.messageScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messageScrollBar = self.messageScroll.verticalScrollBar()
        self.messageScrollBar.rangeChanged.connect(self.changeScrollFocus)
        butWidg = QWidget()
        self.chatLay = QVBoxLayout(butWidg)
        self.chatLay.setAlignment(Qt.AlignTop)
        self.chatLay.setSpacing(2)
        self.chatLay.setContentsMargins(3, 3, 3, 3)
        self.messageScroll.setWidget(butWidg)
        self.mainVertLayout.addWidget(self.messageScroll)

        butWidg = QWidget()
        butLay = QHBoxLayout(butWidg)
        self.messageInput = QLineEdit(butWidg)
        self.messageInput.returnPressed.connect(self.queueMessage)
        butLay.addWidget(self.messageInput)
        butLay.addWidget(QPushButton('Send', clicked=self.queueMessage))
        butWidg.setLayout(butLay)
        butLay.setSpacing(2)
        butLay.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(butWidg)

        checkWidg = QWidget()
        checkLay = QHBoxLayout(checkWidg)
        self.showUsersCheckBox = QCheckBox(checkWidg)
        self.showUsersCheckBox.stateChanged.connect(self.showUserList)
        checkLay.addWidget(self.showUsersCheckBox)
        checkLay.addWidget(QLabel('Show user list'))
        checkLay.setAlignment(Qt.AlignLeft)
        checkWidg.setLayout(checkLay)
        butLay.setSpacing(2)
        butLay.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(checkWidg)

        self.setCentralWidget(cenWidget)

    def changeScrollFocus(self):
        if self.focusOnBottom:
            self.messageScrollBar.setValue(self.messageScrollBar.maximum())

    def queueMessage(self):
        if self.messageInput.text():
            message = {'name': self.name,
                       'time': datetime.datetime.now().strftime("%H:%M"),
                       'text': self.messageInput.text()}
            self.addMessage(message)
            self.soket.pendingMessages.append(message)
            self.messageInput.setText('')

    def addMessage(self, message):
        messageWidget = QLabel(f'<b>{message["name"]} <i>at {message["time"]}:</b><br>'
                               f'{message["text"]}')
        messageWidget.setWordWrap(True)
        messageWidget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if message["name"] == self.name:
            messageWidget.setStyleSheet('color: green;')
        if message['text'].startswith(f'@{self.name}, '):
            messageWidget.setStyleSheet('color: red;')
        self.focusOnBottom = (self.messageScrollBar.value() ==
                              self.messageScrollBar.maximum())
        self.chatLay.addWidget(messageWidget)

    def showUserList(self):
        self.hideUserList()
        print('signal received')
        if self.showUsersCheckBox.isChecked():
            self.scrolli = QScrollArea()
            self.scrolli.setWidgetResizable(True)
            self.scrolli.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            butWidg = QWidget()
            chatLay = QVBoxLayout(butWidg)
            chatLay.setAlignment(Qt.AlignTop)
            chatLay.setSpacing(2)
            chatLay.setContentsMargins(2, 2, 2, 2)
            for userName in self.soket.userList.values():
                chatLay.addWidget(QLabel(f'{userName}'))
            self.scrolli.setWidget(butWidg)
            self.mainVertLayout.addWidget(self.scrolli)

    def hideUserList(self):
        if hasattr(self, 'scrolli'):
            self.scrolli.setParent(None)
            del self.scrolli 

    def closeEvent(self, event):
        print('closing programm')
        self.soket.closeConnection()
        self.threadWork.quit()
        print(self.soket.userList)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        # run the code first with given parameters then chage 'server' to
        # something else, change username and run again
        # window = MyWindow('server', 'Server', '127.0.0.1', 65530)
        window = MyWindow('serve1r2', 'Seerver3R1', '127.0.0.1', 65530)
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(e)