#   DFIRlogbook version 0.32 (codename squeak)
#   2022-01-19
#   Author: Matthew Turner ( @MattETurner )
#
#   ____
#  /   /***
# /___/*****
#  /    *****
# /      ******

from PySide6 import QtCore, QtGui, QtWidgets
from datetime import datetime, timezone, timedelta
from PySide6.QtWidgets import QMessageBox

# icons path
QtCore.QDir.addSearchPath('icons', 'icons/')

# global utc state
utcState = 1

class Ui_MainWindow(object):
    def setupUi(self, DFIRlogbook):
        DFIRlogbook.setObjectName("DFIRlogbook")
        DFIRlogbook.resize(694, 600)
        DFIRlogbook.setMinimumSize(QtCore.QSize(694, 600))
        DFIRlogbook.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks | QtWidgets.QMainWindow.AnimatedDocks)
        self.centralwidget = QtWidgets.QWidget(DFIRlogbook)
        self.centralwidget.setObjectName("centralwidget")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(20, 160, 591, 401))
        self.textBrowser.setObjectName("textBrowser")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(20, 50, 331, 31))
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 30, 58, 16))
        self.label.setObjectName("label")
        self.btnSubmit = QtWidgets.QPushButton(self.centralwidget)
        self.btnSubmit.setGeometry(QtCore.QRect(20, 100, 100, 32))
        self.btnSubmit.setObjectName("btnSubmit")
        self.isUTC = QtWidgets.QCheckBox(self.centralwidget)
        self.isUTC.setGeometry(QtCore.QRect(380, 100, 161, 20))
        self.isUTC.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.isUTC.setChecked(True)
        self.isUTC.setObjectName("isUTC")
        self.utcoffsethours = QtWidgets.QLineEdit(self.centralwidget)
        self.utcoffsethours.setEnabled(False)
        self.utcoffsethours.setGeometry(QtCore.QRect(460, 50, 31, 31))
        self.utcoffsethours.setTabletTracking(False)
        self.utcoffsethours.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.utcoffsethours.setAcceptDrops(False)
        self.utcoffsethours.setStatusTip("")
        self.utcoffsethours.setReadOnly(False)
        self.utcoffsethours.setObjectName("utcoffsethours")
        self.utcoffsetminutes = QtWidgets.QLineEdit(self.centralwidget)
        self.utcoffsetminutes.setEnabled(False)
        self.utcoffsetminutes.setGeometry(QtCore.QRect(530, 50, 51, 31))
        self.utcoffsetminutes.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.utcoffsetminutes.setAcceptDrops(False)
        self.utcoffsetminutes.setStatusTip("")
        self.utcoffsetminutes.setReadOnly(False)
        self.utcoffsetminutes.setObjectName("utcoffsetminutes")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(379, 49, 71, 31))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(450, 30, 60, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(520, 30, 60, 16))
        self.label_4.setObjectName("label_4")
        DFIRlogbook.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(DFIRlogbook)
        self.statusbar.setObjectName("statusbar")
        DFIRlogbook.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(DFIRlogbook)
        self.toolBar.setMinimumSize(QtCore.QSize(30, 30))
        self.toolBar.setObjectName("toolBar")
        DFIRlogbook.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.toolBar)
        #actionCopy
        self.actionCopy = QtGui.QAction(DFIRlogbook)
        icon = QtGui.QIcon('icons:copy.png')
        self.actionCopy.setIcon(icon)
        self.actionCopy.setObjectName("actionCopy")
        self.toolBar.addAction(self.actionCopy)
        # actionClear
        self.actionClear = QtGui.QAction(DFIRlogbook)
        icon = QtGui.QIcon('icons:clear.png')
        self.actionClear.setIcon(icon)
        self.actionClear.setObjectName("actionClear")
        self.toolBar.addAction(self.actionClear)
        # actionSave
        self.actionSave = QtGui.QAction(DFIRlogbook)
        icon = QtGui.QIcon('icons:save.png')
        self.actionSave.setIcon(icon)
        self.actionSave.setObjectName("actionSave")
        self.toolBar.addAction(self.actionSave)

        self.retranslateUi(DFIRlogbook)
        QtCore.QMetaObject.connectSlotsByName(DFIRlogbook)
        self.btnSubmit.clicked.connect(self.copy_txt)
        self.lineEdit.returnPressed.connect(self.line_edit_return)
        self.actionCopy.triggered.connect(self.clipboard_copy)
        self.actionClear.triggered.connect(self.txt_clear)
        self.actionSave.triggered.connect(self.file_save)
        self.isUTC.stateChanged.connect(self.isUTC_state_changed)

    def isUTC_state_changed(self, int):
        if self.isUTC.isChecked():
            self.isUTC_state(False, 1)
        else:
            self.isUTC_state(True, 0)

    def isUTC_state(self, arg0, arg1):
        global utcState
        self.utcoffsethours.setEnabled(arg0)
        self.utcoffsetminutes.setEnabled(arg0)
        utcState = arg1

    def current_time(self):
        if utcState == 1:
            local_datetime = datetime.now()
            local_datetime = local_datetime.replace(microsecond=0)
            date_time = local_datetime.astimezone(timezone.utc)
        else:
            delta_hours = int(self.utcoffsethours.text())
            delta_minutes = int(self.utcoffsetminutes.text())
            date_time = datetime.utcnow().replace(microsecond=0) + timedelta(hours=delta_hours, minutes=delta_minutes)
        return date_time.isoformat()

    def copy_txt(self):
        delta_hours = int(self.utcoffsethours.text())
        delta_minutes = int(self.utcoffsetminutes.text())
        text = self.lineEdit.text()
        if str(text):
            if utcState == 1:
                text = f"{self.current_time()} | {text} \n"
            elif delta_hours >= 0:
                text = f"{self.current_time()}+{delta_hours:02}:{delta_minutes:02} | {text} \n"
            else:
                text = f"{self.current_time()}{delta_hours:03}:{delta_minutes:02} | {text} \n"
            self.textBrowser.insertPlainText(text)
            self.lineEdit.clear()

    def line_edit_return(self):
        self.copy_txt()

    def clipboard_copy(self):
        cursor = self.textBrowser.textCursor()
        cursor.clearSelection()
        self.textBrowser.selectAll()
        self.textBrowser.copy()
        self.textBrowser.setTextCursor(cursor)

    def txt_clear(self):
        msg = QMessageBox()
        msg.setWindowTitle("Clear Log?")
        msg.setText("Pressing 'OK' will clear the clipboard and the log")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.buttonClicked.connect(self.clear_action)
        msg.exec()

    def clear_action(self, i):
        if i.text() == "Cancel":
            return
        else:
            self.textBrowser.setText("")
            clipboard = QtGui.QClipboard()
            clipboard.clear()

    def file_save(self):
        name = QtWidgets.QFileDialog.getSaveFileName(None, "Save Log as... (.txt)", None,"Text files (*.txt)")
        with open(name[0], "w") as file:
            clipboard = QtGui.QClipboard()
            cursor = self.textBrowser.textCursor()
            cursor.clearSelection()
            self.textBrowser.selectAll()
            self.textBrowser.copy()
            self.textBrowser.setTextCursor(cursor)
            text = clipboard.text()
            file.write(text)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("DFIRlogbook", "DFIRlogbook"))
        self.lineEdit.setStatusTip(_translate("DFIRlogbook", "Input Entry Field"))
        self.actionCopy.setStatusTip(_translate("DFIRlogbook", "copy to clipboard"))
        self.actionClear.setStatusTip(_translate("DFIRlogbook", "Clear Output Field"))
        self.label.setText(_translate("DFIRlogbook", "ENTRY:"))
        self.btnSubmit.setText(_translate("DFIRlogbook", "Submit"))
        self.toolBar.setWindowTitle(_translate("DFIRlogbook", "toolBar"))
        self.actionCopy.setText(_translate("DFIRlogbook", "Copy"))
        self.actionClear.setText(_translate("DFIRlogbook", "Clear"))
        self.actionSave.setText(_translate("DFIRlogbook", "Save"))
        self.isUTC.setText(_translate("DFIRlogbook", "Timezone: UTC"))
        self.utcoffsethours.setText(_translate("DFIRlogbook", "00"))
        self.utcoffsetminutes.setText(_translate("DFIRlogbook", "00"))
        self.label_2.setText(_translate("DFIRlogbook", "UTC offset"))
        self.label_3.setText(_translate("DFIRlogbook", "hours:"))
        self.label_4.setText(_translate("DFIRlogbook", "minutes:"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())