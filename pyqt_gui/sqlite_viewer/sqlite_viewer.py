from sqlite3.dbapi2 import DatabaseError
import sys
import sqlite3
import os
from datetime import datetime
from itertools import groupby

import click
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QWidget,
                             QMainWindow, QVBoxLayout, QFileDialog, QComboBox,
                             QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QMessageBox)
from PyQt5.QtCore import Qt


class SQLExec():
    '''Helper class for sql operations'''

    def __init__(self, dbpath):
        # initialize connection to databasa
        self.dbpath = os.path.abspath(dbpath)
        self.conn = sqlite3.connect(f'{self.dbpath}')
        self.cursor = self.conn.cursor()
        # get all available tables from selected databasa
        self.availableTables = [x[0] for x in self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()[:-1]]
        # corresponding types of sqlite types to python types
        self.correspondingTypes = {'int': int, 'integer': int, 'numeric': float,
                                   'boolean': bool}

    def getTable(self, tableName):
        '''Get selected table (column names, types and values) from database'''
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
        '''Convert string values fetched from table widget to corresponding 
        format according to column data type
        '''
        colType = self.columnTypes[col]
        if colType in 'datetime':
            dateStr = '%Y-%m-%d %H:%M:%S' if len(newValue) > 10 else '%Y-%m-%d'
            return datetime.strptime(newValue, dateStr)
        elif colType in self.correspondingTypes:
            return self.correspondingTypes[colType](newValue)
        else:
            return newValue

    def dbWrite(self, changes, table):
        '''Writes staged changes to database'''
        try:
            # group changes based on row to insert changes one row at a time
            # and not one value at a time
            rowGroups = groupby(sorted(changes), lambda x: x[0])
            # for each row group gets names of columns being changed or 
            # added and new values
            for row, coords in rowGroups:
                columnValues = [(self.columnNames[coord[1]], changes[coord])
                                for coord in coords]
                columns, values = list(zip(*columnValues))
                # if row number is bigger or equals that means that it is a new 
                # row - builds according query
                if row >= len(self.values):
                    query = f'''
                        INSERT INTO {table}({', '.join(columns)})
                        VALUES ({', '.join(['?' for _ in range(len(values))])})
                    '''
                    self.cursor.execute(query, values)
                # else it is row update
                else:
                    # get ititial values of the row to filter on them, exclude 
                    # None values because NULL is not equal to any value
                    filterParams = [
                        (self.values[row][i], self.columnNames[i])
                        for i in range(len(self.columnNames))
                        if self.values[row][i] is not None
                    ]
                    filterValues, filterColumns = list(zip(*filterParams))
                    queryFilter = ' AND '.join(
                        [f'{filterColumns[i]}=?' for i in range(
                            len(filterColumns))]
                    )
                    # build query based on updated value and filter on values 
                    # above
                    query = f'''
                        UPDATE {table}
                        SET {', '.join([f'{column}=?' for column in columns])}
                        WHERE {queryFilter}
                    '''
                    self.cursor.execute(query, (*values, *filterValues))
            self.conn.commit()
        # in case of database error add row value on which error occured and 
        # propagate exception to caller
        except DatabaseError as err:
            err = f'{err} with values in row - {row}!'
            raise sqlite3.IntegrityError(err)


class MyWindow(QMainWindow):

    def __init__(self, dbname, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setGeometry(500, 500, 500, 500)
        self.setWindowTitle('SQL viewer')

        self.dbname = dbname
        if self.dbname:
            self.selectDB()

        # dictionary to store values to be changed or added in "(row, col): new
        # value" format
        self.pendingChanges = {}

        self.initUI()

    def initUI(self):
        cenWidget = QWidget(self)
        self.mainVertLayout = QVBoxLayout(cenWidget)
        self.mainVertLayout.setAlignment(Qt.AlignHCenter)

        # if database is not provided through --dbfile option show message and
        # button for selection
        if not self.dbname:
            self.mainVertLayout.addWidget(
                QLabel("Database is not selected. "
                       "Click button below to select."))
            selectButton = QPushButton('Select database')
            selectButton.clicked.connect(self.selectDB)
            self.mainVertLayout.addWidget(selectButton)
        else:
            self.mainVertLayout.addWidget(QLabel('Available tables:'))
            # combo box for table selection
            self.qBox = QComboBox()
            self.qBox.addItems(self.sqlObj.availableTables)
            self.qBox.currentTextChanged.connect(self.changeTable)
            self.mainVertLayout.addWidget(self.qBox)
            self.showTable()
            self.showButtons()

        self.setCentralWidget(cenWidget)

    def showTable(self):
        '''Show table when it has been newly selected or changed'''
        # if any table was previously selected and showed, delete it from layout
        # and  recreate with new values
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
        '''Adds changes to pendingChanges list after converting them from string 
        to corresponding python format based on data type of column being 
        updated or inserted
        '''
        newValue = self.tableWidg.item(row, col).text()
        # try to get initial value (value before change) that is either in
        # changes dictionary or, if it was not staged, in initial table
        try:
            initialValue = str(self.pendingChanges.get((row, col), None)
                               or self.sqlObj.values[row][col])
        # if there is no value in either places that means that it is new row
        # and initial value is just blank space
        except IndexError:
            initialValue = ''
        # if new value equal to previous value, that means that function was
        # trigered by value change caused by except block later in this function
        # and it does need to do anything
        if newValue == initialValue:
            return
        # tries to convert value to python type based on column data type, if
        # successful adds to changes dictionary
        try:
            convertedValue = self.sqlObj.convertValue(col, newValue)
            self.pendingChanges[(row, col)] = convertedValue
            self.saveButton.setDisabled(False)
            self.cancelButton.setDisabled(False)
        # if conversion is unsuccessful shows error message and restores value
        # in cellbefore change occured
        except ValueError:
            rightColumnType = self.sqlObj.columnTypes[col]
            QMessageBox.warning(
                self, 'Wrong data format!',
                f'Data type for this column - {rightColumnType}')
            self.tableWidg.setItem(row, col,
                                   QTableWidgetItem(initialValue))

    def showButtons(self):
        # if table changed or new table has been selected add buttons to layout
        # else create them anew
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
        '''Delete all values to change and restore table to initial state'''
        self.pendingChanges = {}
        self.changeTable()

    def saveChanges(self):
        '''Try to save changes to database via helper object. In case of failure 
        show error message and rollback changes
        '''
        try:
            self.sqlObj.dbWrite(self.pendingChanges, self.currentTable)
            self.changeTable()
            self.pendingChanges = {}
            QMessageBox.information(
                self, 'Changes saved!',
                f'All changes has been successully saved!')
        except DatabaseError as dbExc:
            QMessageBox.critical(
                self, 'Database error!',
                f'Failed to write to database with following error - {dbExc}!')
            self.sqlObj.conn.rollback()

    def addRow(self):
        '''Insert new blank row to the table'''
        self.tableWidg.insertRow(self.tableWidg.rowCount())

    def selectDB(self):
        '''If dbname is not provided gets it through file dialog and initializes
        sql helper object
        '''
        if not self.dbname:
            self.dbname = QFileDialog().getOpenFileName()[0]
        self.sqlObj = SQLExec(self.dbname)
        self.currentTable = self.sqlObj.availableTables[0]
        self.setWindowTitle(f'SQL viewer - {os.path.basename(self.dbname)}')
        self.initUI()

    def changeTable(self):
        '''Change currently selected table and repaint buttons and table widget 
        itself
        '''
        self.currentTable = self.qBox.currentText()
        self.showTable()
        self.showButtons()

    def closeEvent(self, event):
        try:
            self.sqlExec.conn.close()
        except AttributeError:
            pass


@click.command()
@click.option('--dbpath', type=str)
def start(dbpath):
    app = QApplication(sys.argv)
    window = MyWindow(dbpath)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    start()