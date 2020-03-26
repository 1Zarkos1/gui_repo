import sys
import datetime
import socket
import selectors
import json
import traceback

from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QTimeEdit, QCheckBox, QTextEdit, QAbstractScrollArea)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import Qt, QObject, QEvent, QSize, pyqtSignal, pyqtSlot, QThread


class SocketWork(QObject):

    messageSignal = pyqtSignal(dict)
    usersChanged = pyqtSignal()

    def __init__(self, userType, name, host, port):
        super().__init__()
        # variables for app
        self.type = userType
        self.name = name
        # list of currently connected users
        self.userList = {}
        # messages to send
        self.pendingMessages = []
        # state of instanse
        self.run = True
        # message encoding used in app
        self.encoding = 'utf-8'
        # list of users who needs to receive list of current users (upon 
        # connecting)
        self.sendUserListTo = []

        # initialize selector
        self.sel = selectors.DefaultSelector()
        self.host, self.port = host, port
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @pyqtSlot()
    def startConnection(self):
        # set server or connect to it depending on the type of user
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
                    # if server socket if ready for use accept user trying to 
                    # connect
                    if key.data == 'Server':
                        self.acceptUser(key.fileobj)
                    # if user already connected communicate with him
                    else:
                        result = self.communicate(key, mask)
                        if result == 'received':
                            break
                # if loop finished without any break e.g. message was sent to 
                # all users - remove message from waiting list
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

    # function for safely closing connections, either connection that is 
    # supplied to function or all available connections
    def closeConnection(self, sock=None):
        if sock == None or self.type != 'server':
            while ((self.sel.get_map() and len(self.sel.get_map()) > 1)
                    or (self.type != 'server' and self.sel.get_map() 
                    and len(self.sel.get_map()) > 0)):
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

    # change message type between bytes and dict before sending or after 
    # receiveing message
    def translateMessage(self, message):
        if type(message) == bytes:
            message = json.loads(message.decode(self.encoding))
        elif type(message) == dict or type(message) == list:
            message = json.dumps(message).encode(self.encoding)
        return message

    # accept new user and store it's socket in selectors
    def acceptUser(self, sock):
        conn, _ = sock.accept()
        conn.setblocking(False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data='_client')

    # method that receives system messages based on header 
    # (if header is not numerical)
    def receiveSysMessage(self, sock, header):
        # receives quit message send by user or server and closes certain socket
        if header == '_quit':
            print('quit message received')
            return self.closeConnection(sock)
        # receives name of user that connects to a server
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
        # receives userlist from server
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
        # adds connected user to userlist and sends message asking to provide 
        # a username
        if self.type == 'server' and userAddress not in self.userList:
            sock.send('_name'.encode(self.encoding))
            self.userList[userAddress] = None
            print('ask message send')
        # sends username to server upon receiving asking header - "_name"
        elif self.type != 'server' and header == '_name':
            name = self.name.encode(self.encoding)
            print('sending _name')
            sock.send('_name'.encode(self.encoding))
            print('sending header')
            sock.send(f"{len(name):05}".encode(self.encoding))
            print('sending name')
            sock.send(name)
            print('name send')
        # sends to user, that was connected and stored in 'self.sendUserListTo',
        # current userlist and removes that user from waiting list
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
        if mask & selectors.EVENT_READ and not self.pendingMessages:
            header = sock.recv(5)
            if header:
                receivedHeader = header.decode(self.encoding)
                # if header is numeric that means that it is header with message 
                # length and message can be received after
                if receivedHeader.isnumeric():
                    sock.setblocking(True)
                    message = self.translateMessage(
                        sock.recv(int(receivedHeader)))
                    sock.setblocking(False)
                    self.messageSignal.emit(message)
                    # if message was received stop and return from current 
                    # function to stop iteration and start it again to send 
                    # received message to users
                    if self.type == 'server':
                        self.pendingMessages.append(message)
                        return 'received'
                # if header received was alphabetical that means that it is 
                # system message and should be processed accordingly
                else:
                    result = self.receiveSysMessage(sock, receivedHeader)
                    if result == '_quit':
                        return

        if mask & selectors.EVENT_WRITE:
            # send system message if needed
            self.sendSysMessage(sock, receivedHeader)
            # if there is message waiting to be send - send it
            if self.pendingMessages:
                message = self.pendingMessages[0]
                if (self.type != 'server' or message['name'] 
                        != self.userList[sock.getpeername()]):
                    byteMessage = self.translateMessage(message)
                    sock.send(f"{len(byteMessage):05}".encode(self.encoding))
                    sock.send(byteMessage)


class MyWindow(QMainWindow):

    # signal to begin running socket object
    startSign = pyqtSignal()

    def __init__(self, userType, name, host, port, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(600, 300, 400, 500)
        self.setWindowTitle(f'PyQT messanger - as {name}')
        self.setWindowIcon(QIcon('../img/message.png'))
        self.setStyleSheet(open('style.css').read())
        self.name = name
        self.type = userType
        self.selection = ''
        # initialize socket object and thread object, add socket object to 
        # thread and add neccessary signals 
        self.soket = SocketWork(userType, name, host, port)
        self.threadWork = QThread()
        self.threadWork.start()
        self.soket.moveToThread(self.threadWork)
        self.soket.messageSignal.connect(self.addMessage)
        self.soket.usersChanged.connect(self.showUserList)
        self.startSign.connect(self.soket.startConnection)
        self.startSign.emit()
        # add current user to userlist
        self.soket.userList[(host, port)] = name

        self.initUI()

    def initUI(self):
        # main layout and central widget
        cenWidget = QWidget(self)
        self.mainVertLayout = QVBoxLayout(cenWidget)
        self.mainVertLayout.setSpacing(0)
        self.mainVertLayout.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(QLabel('Chat messages:'))
        # area for displaying messages
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
        # message input and 'send' button
        butWidg = QWidget()
        butLay = QHBoxLayout(butWidg)
        self.messageInput = QLineEdit(butWidg)
        self.messageInput.setPlaceholderText('Your message')
        self.messageInput.returnPressed.connect(self.queueMessage)
        butLay.addWidget(self.messageInput)
        butLay.addWidget(QPushButton('Send', clicked=self.queueMessage))
        butWidg.setLayout(butLay)
        butLay.setSpacing(2)
        butLay.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(butWidg)

        # checkbox for displaying user list and buttons for message styling 
        checkWidg = QWidget()
        checkLay = QHBoxLayout(checkWidg)
        self.showUsersCheckBox = QCheckBox(checkWidg)
        self.showUsersCheckBox.stateChanged.connect(self.showUserList)
        checkLay.addWidget(self.showUsersCheckBox)
        checkLay.addWidget(QLabel('Show user list'))
        
        styleButtons = [
            ('Bold', '../img/bold.png'), ('Italic', '../img/italic.png')
        ]
        for name, ref in styleButtons:
            button = QPushButton(name, clicked=lambda: 
                                self.addStyles(name[0].lower()))
            button.setObjectName('styleButton')
            button.setIcon(QIcon(ref))
            button.setFocusPolicy(Qt.NoFocus)
            checkLay.addWidget(button)

        checkLay.setAlignment(Qt.AlignLeft)
        checkWidg.setLayout(checkLay)
        butLay.setSpacing(2)
        butLay.setContentsMargins(1, 1, 1, 1)
        self.mainVertLayout.addWidget(checkWidg)

        self.setCentralWidget(cenWidget)

    # function that depending on where user was focused before message was added
    # scroll to last messages (if focus was on last message) or leaves window
    # without scrolling
    def changeScrollFocus(self):
        if self.focusOnBottom:
            self.messageScrollBar.setValue(self.messageScrollBar.maximum())

    # add bold and italic style tags to message
    def addStyles(self, sign):
        selectedText = self.messageInput.selectedText()
        if selectedText:
            text = self.messageInput.text()
            start = self.messageInput.selectionStart()
            end = self.messageInput.selectionEnd()
            fullMessage = f'{text[0:start]}<{sign}>{selectedText}</{sign}>'\
                          f'{text[end:len(text)]}'
            self.messageInput.setText(fullMessage)
        else:
            self.messageInput.insert(f'<{sign}></{sign}>')
    
    # adds message to queue (list) for sending and sets input to blank 
    def queueMessage(self):
        if self.messageInput.text():
            message = {'name': self.name,
                       'time': datetime.datetime.now().strftime("%H:%M"),
                       'text': self.messageInput.text()}
            self.addMessage(message)
            self.soket.pendingMessages.append(message)
            self.messageInput.setText('')

    # adds message to main window message view
    def addMessage(self, message):
        messageWidget = QLabel(f'<b>{message["name"]} <i>at {message["time"]}:</b><br>'
                               f'{message["text"]}')
        messageWidget.setWordWrap(True)
        messageWidget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if message["name"] == self.name:
            messageWidget.setStyleSheet('color: green;')
        if message['text'].startswith(f'@{self.name}, '):
            messageWidget.setStyleSheet('color: red;')
        # check where user is focused (for changeScrollFocus method)
        self.focusOnBottom = (self.messageScrollBar.value() ==
                              self.messageScrollBar.maximum())
        self.chatLay.addWidget(messageWidget)

    # adds userlist from window depending on state of respective checkbox
    def showUserList(self):
        self.hideUserList()
        print('signal received')
        if self.showUsersCheckBox.isChecked():
            self.userListScroll = QScrollArea()
            self.userListScroll.setWidgetResizable(True)
            self.userListScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            butWidg = QWidget()
            chatLay = QVBoxLayout(butWidg)
            chatLay.setAlignment(Qt.AlignTop)
            chatLay.setSpacing(2)
            chatLay.setContentsMargins(2, 2, 2, 2)
            for userName in self.soket.userList.values():
                user = QLabel(f'{userName}')
                user.installEventFilter(self)
                chatLay.addWidget(user)
            self.userListScroll.setWidget(butWidg)
            self.mainVertLayout.addWidget(self.userListScroll)

    # adds functionality to address user by clicking his name in userList
    # without the need to type his name by hand
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and type(obj) == QLabel:
                self.messageInput.setText(f'@{obj.text()}, ' 
                                          + self.messageInput.text())
        return QObject.event(obj, event)

    # removes userlist from window depending on state of respective checkbox
    def hideUserList(self):
        if hasattr(self, 'userListScroll'):
            self.userListScroll.setParent(None)
            del self.userListScroll 

    # operations to do when window is closed
    def closeEvent(self, event):
        print('closing programm')
        self.soket.closeConnection()
        self.threadWork.quit()
        print(self.soket.userList)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        # run the code first with first line ('server') then comment it, 
        # uncomment secons line ('user') and run again
        # window = MyWindow('server', 'Server', '127.0.0.1', 65530)
        window = MyWindow('user', 'User1', '127.0.0.1', 65530)
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(e)