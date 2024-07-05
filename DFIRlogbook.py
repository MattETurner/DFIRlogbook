#   DFIRlogbook version 0.4.2.1 (codename baldeagle)
#   2024-07-05
#   Author: Matthew Turner ( @MattETurner )
#
#   ____
#  /   /***
# /___/********
#  /       *********
# /           ***********

import sys
import os
from datetime import datetime, timezone, timedelta
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QMessageBox, QRubberBand, QApplication, QWidget)
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from PySide6.QtCore import QRect, QPoint, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# icons resources | commented out for now while revising images for taskbar
# import res_icons

# global utc state
utcState = 1

class ScreenshotCropWindow(QWidget):
    cropped = Signal(QPixmap)

    def __init__(self, screenshot):
        super().__init__()
        self.screenshot = screenshot
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.screen = QApplication.primaryScreen()
        self.setGeometry(self.screen.geometry())
        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.screenshot)

    def mousePressEvent(self, event):
        self.origin = self.mapToGlobal(event.position().toPoint())
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, self.mapToGlobal(event.position().toPoint())).normalized())

    def mouseReleaseEvent(self, event):
        self.rubberBand.hide()
        rect = QRect(self.origin, self.mapToGlobal(event.position().toPoint())).normalized()
        
        devicePixelRatio = self.screen.devicePixelRatio()
        
        if devicePixelRatio == 1:
            deviceRect = rect
        else:
            deviceRect = QRect(rect.x() * devicePixelRatio,
                               rect.y() * devicePixelRatio,
                               rect.width() * devicePixelRatio,
                               rect.height() * devicePixelRatio)
        
        cropped = self.screenshot.copy(deviceRect)
        self.cropped.emit(cropped)
        self.close()
        
class Ui_MainWindow(object):
    def capture_screen(self):
        screen = QApplication.primaryScreen()
        self.full_screenshot = screen.grabWindow(0)
        self.crop_window = ScreenshotCropWindow(self.full_screenshot)
        self.crop_window.cropped.connect(self._process_screenshot)

    def _process_screenshot(self, cropped_screenshot):
        if cropped_screenshot and not cropped_screenshot.isNull():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            cropped_screenshot.save(os.path.join("screenshots", filename))
            
            # Add screenshot reference to log
            log_entry = f"{self.current_time()} | Screenshot captured: {filename}\n"
            self.textBrowser.insertPlainText(log_entry)
            
            # Auto-scroll to the bottom
            self.textBrowser.verticalScrollBar().setValue(
                self.textBrowser.verticalScrollBar().maximum()
            )

class Ui_MainWindow(object):
    def setupUi(self, DFIRlogbook):
        DFIRlogbook.setObjectName("DFIRlogbook")
        DFIRlogbook.resize(694, 600)
        DFIRlogbook.setMinimumSize(QtCore.QSize(694, 600))
        DFIRlogbook.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks | QtWidgets.QMainWindow.AnimatedDocks)
        self.main_window = DFIRlogbook
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
        
        # actionCopy
        self.actionCopy = QtGui.QAction(DFIRlogbook)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/main/icons/copy.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.actionCopy.setIcon(icon)
        self.actionCopy.setObjectName("actionCopy")
        self.toolBar.addAction(self.actionCopy)
        
        # actionClear
        self.actionClear = QtGui.QAction(DFIRlogbook)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/main/icons/clear.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.actionClear.setIcon(icon1)
        self.actionClear.setObjectName("actionClear")
        self.toolBar.addAction(self.actionClear)
        
        # actionSave
        self.actionSave = QtGui.QAction(DFIRlogbook)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/main/icons/save.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.actionSave.setIcon(icon2)
        self.actionSave.setObjectName("actionSave")
        self.toolBar.addAction(self.actionSave)

        # Add screen capture action
        self.actionScreenCapture = QtGui.QAction(DFIRlogbook)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/main/icons/camera.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.actionScreenCapture.setIcon(icon3)
        self.actionScreenCapture.setObjectName("actionScreenCapture")
        self.toolBar.addAction(self.actionScreenCapture)

        self.retranslateUi(DFIRlogbook)
        QtCore.QMetaObject.connectSlotsByName(DFIRlogbook)
        self.btnSubmit.clicked.connect(self.copy_txt)
        self.lineEdit.returnPressed.connect(self.line_edit_return)
        self.actionCopy.triggered.connect(self.clipboard_copy)
        self.actionClear.triggered.connect(self.txt_clear)
        self.actionSave.triggered.connect(self.file_save)
        self.isUTC.stateChanged.connect(self.isUTC_state_changed)
        self.actionScreenCapture.triggered.connect(self.capture_screen)

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
            
            # Auto-scroll to the bottom
            self.textBrowser.verticalScrollBar().setValue(
                self.textBrowser.verticalScrollBar().maximum()
            )

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
        msg.setText("Pressing 'OK' will clear the log")
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

    def capture_screen(self):
        screen = QtWidgets.QApplication.primaryScreen()
        self.full_screenshot = screen.grabWindow(0)
        self.crop_window = ScreenshotCropWindow(self.full_screenshot)
        self.crop_window.cropped.connect(self._process_screenshot)
        self.crop_window.showFullScreen()

    def _process_screenshot(self, cropped_screenshot):
        if cropped_screenshot and not cropped_screenshot.isNull():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            cropped_screenshot.save(os.path.join("screenshots", filename))
            
            # Add screenshot reference to log
            log_entry = f"{self.current_time()} | Screenshot captured: {filename}\n"
            self.textBrowser.insertPlainText(log_entry)
            
            # Auto-scroll to the bottom
            self.textBrowser.verticalScrollBar().setValue(
                self.textBrowser.verticalScrollBar().maximum()
            )

    def file_save(self):
        name = QtWidgets.QFileDialog.getSaveFileName(None, "Save Log as... (.pdf)", None, "PDF files (*.pdf)")
        if name[0]:
            doc = SimpleDocTemplate(name[0], pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Get log entries
            log_text = self.textBrowser.toPlainText()
            entries = log_text.split('\n')

            for entry in entries:
                if entry.strip():
                    if "Screenshot captured:" in entry:
                        # Add text
                        story.append(Paragraph(entry, styles['Normal']))
                        story.append(Spacer(1, 12))
                        
                        # Add image
                        screenshot_name = entry.split(": ")[-1].strip()
                        img_path = os.path.join("screenshots", screenshot_name)
                        if os.path.exists(img_path):
                            img = Image(img_path)
                            # Set a maximum width
                            max_width = 6 * 72  # 6 inches * 72 points per inch
                            # Calculate the aspect ratio
                            aspect = img.imageWidth / img.imageHeight
                            # Set the width to either the max_width or the image's original width, whichever is smaller
                            img_width = min(max_width, img.imageWidth)
                            # Calculate the height based on the aspect ratio
                            img_height = img_width / aspect
                            img.drawWidth = img_width
                            img.drawHeight = img_height
                            story.append(img)
                            story.append(Spacer(1, 12))
                    else:
                        story.append(Paragraph(entry, styles['Normal']))
                        story.append(Spacer(1, 12))

            doc.build(story)

    def retranslateUi(self, MainWindow):
            _translate = QtCore.QCoreApplication.translate
            MainWindow.setWindowTitle(_translate("DFIRlogbook", "DFIRlogbook"))
            self.lineEdit.setStatusTip(_translate("DFIRlogbook", "Input Entry Field"))
            self.actionCopy.setStatusTip(_translate("DFIRlogbook", "Copy to Clipboard"))
            self.actionClear.setStatusTip(_translate("DFIRlogbook", "Clear Output Field"))
            self.label.setText(_translate("DFIRlogbook", "ENTRY:"))
            self.btnSubmit.setText(_translate("DFIRlogbook", "Submit"))
            self.toolBar.setWindowTitle(_translate("DFIRlogbook", "toolBar"))
            self.actionCopy.setText(_translate("DFIRlogbook", "Copy"))
            self.actionClear.setText(_translate("DFIRlogbook", "Clear"))
            self.actionSave.setText(_translate("DFIRlogbook", "Save"))
            self.actionScreenCapture.setText(_translate("DFIRlogbook", "Screenshot"))
            self.actionScreenCapture.setStatusTip(_translate("DFIRlogbook", "Capture a region of the screen"))
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