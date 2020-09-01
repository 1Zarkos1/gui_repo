from sqlite3.dbapi2 import DatabaseError
import sys
import sqlite3
import os
from datetime import datetime

import click
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QVBoxLayout, QFileDialog, QComboBox,
                             QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QMessageBox)
from PyQt5.QtCore import Qt


class SQLExec():

    def __init__(self, dbpath):
        self.dbpath = os.path.abspath(dbpath)
        self.conn = sqlite3.connect(f'{self.dbpath}')
        self.cursor = self.conn.cursor()
        self.availableTables = [x[0] for x in self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()[:-1]]
        self.correspondingTypes = {'int': int, 'integer': int, 'numeric': float,
                                   'boolean': bool}

    def getTable(self, tableName):
        tableInfo = self.cursor.execute(
            f'''SELECT name, type 
            FROM pragma_table_info("{tableName}")'''
        )
        self.columnNames, self.columnTypes = list(zip(*tableInfo.fetchall()))
        self.columnTypes = [colType.split('(')[0].lower()
                            for colType in self.columnTypes]
        self.values = self.cursor.execute(
            f'SELECT * FROM {tableName}').fetchall()
        return (self.columnNames, self.values)

    def convertValue(self, col, newValue):
        colType = self.columnTypes[col]
        if colType in 'datetime':
            dateStr = '%Y-%m-%d %H:%M:%S' if len(newValue) > 10 else '%Y-%m-%d'
            return datetime.strptime(newValue, dateStr)
        elif colType in self.correspondingTypes:
            return self.correspondingTypes[colType](newValue)
        else:
            return newValue

    def dbWrite(self, changes, table):
        try:
            for key, value in changes.items():
                row, col = key
                updatedColumn = self.columnNames[col]
                filterParams = [
                    (self.values[row][i], self.columnNames[i]) 
                    for i in range(len(self.columnNames)) 
                    if self.values[row][i] is not None
                ]
                filterValues, filterColumns = list(zip(*filterParams))
                queryFilter = ' AND '.join(
                    [f'{filterColumns[i]}=?' for i in range(len(filterColumns))]
                )
                query = f'''UPDATE {table}
                            SET {updatedColumn}=?
                            WHERE {queryFilter}'''
                self.cursor.execute(query, (value, *filterValues))
                self.conn.commit()
        except DatabaseError as err:
            err = f'{err} with value ({value}) in column ({updatedColumn})'
            raise sqlite3.IntegrityError(err)


class MyWindow(QMainWindow):

    def __init__(self, dbname, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(500, 500, 300, 300)
        self.setWindowTitle('SQL viewer')

        self.dbname = dbname
        if self.dbname:
            self.selectDB()

        self.pendingChanges = {}

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
            self.changeTable()

        self.setCentralWidget(cenWidget)

    def showTable(self):
        if hasattr(self, 'tableWidg'):
            self.tableWidg.setParent(None)
            self.buttons.setParent(None)
        self.tableWidg = QTableWidget()
        header, table = self.sqlObj.getTable(self.currentTable)
        self.tableWidg.setRowCount(len(table))
        self.tableWidg.setColumnCount(len(header))
        self.tableWidg.setHorizontalHeaderLabels(header)
        for row in range(len(table)):
            for col in range(len(header)):
                cellValue = QTableWidgetItem(str(table[row][col]))
                self.tableWidg.setItem(row, col, cellValue)
        self.tableWidg.cellChanged.connect(self.stageChanges)
        self.mainVertLayout.addWidget(self.tableWidg)

    def stageChanges(self, row, col):
        newValue = self.tableWidg.item(row, col).text()
        initialValue = str(self.pendingChanges.get((row, col), None)
                           or self.sqlObj.values[row][col])
        if newValue == initialValue:
            return
        try:
            convertedValue = self.sqlObj.convertValue(col, newValue)
            self.pendingChanges[(row, col)] = convertedValue
            self.saveButton.setDisabled(False)
            self.cancelButton.setDisabled(False)
        except ValueError:
            rightColumnType = self.sqlObj.columnTypes[col]
            QMessageBox.warning(
                self, 'Wrong data format!',
                f'Data type for this column - {rightColumnType}')
            self.tableWidg.setItem(row, col,
                                   QTableWidgetItem(initialValue))
        print(self.pendingChanges)

    def showButtons(self):
        if hasattr(self, 'buttons'):
            self.mainVertLayout.addWidget(self.buttons)
        else:
            self.buttons = QWidget()
            horLayout = QHBoxLayout(self.buttons)
            addButton = QPushButton('Add row')
            horLayout.addWidget(addButton)
            addButton.clicked.connect(self.addRow)
            self.saveButton = QPushButton('Save changes')
            horLayout.addWidget(self.saveButton)
            self.saveButton.clicked.connect(self.saveChanges)
            self.cancelButton = QPushButton('Cancel')
            horLayout.addWidget(self.cancelButton)
            self.cancelButton.clicked.connect(self.cancelChanges)
            horLayout.setAlignment(Qt.AlignCenter)
            self.mainVertLayout.addWidget(self.buttons)
        self.saveButton.setDisabled(True)
        self.cancelButton.setDisabled(True)

    def cancelChanges(self):
        self.pendingChanges = {}
        self.changeTable()

    def saveChanges(self):
        try:
            self.sqlObj.dbWrite(self.pendingChanges, self.currentTable)
            self.changeTable()
            self.pendingChanges = {}
        except DatabaseError as dbExc:
            QMessageBox.critical(
                self, 'Database error!',
                f'Failed to write to database with following error - {dbExc}!')
            self.sqlObj.conn.rollback()

    def addRow(self):
        self.tableWidg.insertRow(self.tableWidg.rowCount())

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
        self.showButtons()

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