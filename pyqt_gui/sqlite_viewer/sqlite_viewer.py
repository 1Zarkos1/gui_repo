import sys
import sqlite3
import os

import click
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QVBoxLayout, QFileDialog, QComboBox,
                             QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt


class SQLExec():

    def __init__(self, dbpath):
        self.dbpath = os.path.abspath(dbpath)
        self.conn = sqlite3.connect(f'{self.dbpath}')
        self.cursor = self.conn.cursor()
        self.availableTables = [x[0] for x in self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()[:-1]]

    def getTable(self, tableName):
        tableNames = self.cursor.execute(
            f'''SELECT name 
            FROM pragma_table_info("{tableName}")'''
        )
        tableNames = [x[0] for x in tableNames.fetchall()]
        values = self.cursor.execute(f'SELECT * FROM {tableName}').fetchall()
        return tableNames, values


class MyWindow(QMainWindow):

    def __init__(self, dbname, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(500, 500, 300, 300)
        self.setWindowTitle('SQL viewer')

        self.dbname = dbname
        if self.dbname:
            self.selectDB()

        self.initUI()

    def initUI(self):
        cenWidget = QWidget(self)
        self.mainVertLayout = QVBoxLayout(cenWidget)
        self.mainVertLayout.setAlignment(Qt.AlignHCenter)

        if not self.dbname:
            self.mainVertLayout.addWidget(
                QLabel("Database is not selected. "
                       "Click button below to select."))
            selectButton = QPushButton('Select database')
            selectButton.clicked.connect(self.selectDB)
            self.mainVertLayout.addWidget(selectButton)
        else:
            self.mainVertLayout.addWidget(QLabel('Available tables:'))
            self.qBox = QComboBox()
            self.qBox.addItems(self.sqlObj.availableTables)
            self.qBox.currentTextChanged.connect(self.changeTable)
            self.mainVertLayout.addWidget(self.qBox)
            self.showTable()

        self.setCentralWidget(cenWidget)

    def showTable(self):
        if hasattr(self, 'tableWidg'):
            self.tableWidg.setParent(None)
        self.tableWidg = QTableWidget()
        header, table = self.sqlObj.getTable(self.currentTable)
        self.tableWidg.setRowCount(len(table))
        self.tableWidg.setColumnCount(len(header))
        self.tableWidg.setHorizontalHeaderLabels(header)
        for row in range(len(table)):
            for col in range(len(header)):
                cellValue = QTableWidgetItem(str(table[row][col]))
                self.tableWidg.setItem(row, col, cellValue)
        self.mainVertLayout.addWidget(self.tableWidg)

    def selectDB(self):
        if not self.dbname:
            self.dbname = QFileDialog().getOpenFileName()[0]
        self.sqlObj = SQLExec(self.dbname)
        self.currentTable = self.sqlObj.availableTables[0]
        self.setWindowTitle(f'SQL viewer - {os.path.basename(self.dbname)}')
        self.initUI()

    def changeTable(self):
        self.currentTable = self.qBox.currentText()
        self.showTable()

    def closeEvent(self, event):
        try:
            self.sqlExec.conn.close()
        except AttributeError:
            pass


@click.command()
@click.option('--dbfile', type=str)
def start(dbfile):
    app = QApplication(sys.argv)
    window = MyWindow(dbfile)
    window.show()
    app.exec_()


if __name__ == '__main__':
    start()
