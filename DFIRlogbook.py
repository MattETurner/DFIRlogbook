#   DFIRlogbook
# Version constant for easy updates
VERSION = "0.6.0.6"
#   Date: 2025-05-12
#   Author: Matthew Turner ( @MattETurner )
#   License: MIT
#   Description: A simple tool for capturing screenshots and files. Adding them to an ISO8601 timestamped log.
#   Features:
#   - Capture screenshots of specific areas of the screen
#   - Add files to log
#   - Add tags to entries
#   - Export log to PDF
#
#   ____
#  /   /***
# /___/********
#  /       *********
# /           ***********
#
import sys
import os
import logging
from datetime import datetime, timezone, timedelta
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QMessageBox, QRubberBand, QApplication, QWidget,
                              QInputDialog, QLineEdit, QMenu, QCheckBox,
                              QVBoxLayout, QHBoxLayout, QDialog, QPushButton, QListWidget,
                              QListWidgetItem, QLabel, QAbstractItemView, QComboBox)
from PySide6.QtCore import Signal
from PySide6.QtCore import QRect, QPoint, Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QCursor, QColor, QFont, QContextMenuEvent, QAction, QPalette
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, PageTemplate, Frame, BaseDocTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import time
import shutil

# Custom exceptions
class DFIRLogbookError(Exception):
    """Base exception class for DFIRlogbook"""
    pass

class TagError(DFIRLogbookError):
    """Exception raised for tag-related errors"""
    pass

class ExportError(DFIRLogbookError):
    """Exception raised for export-related errors"""
    pass

class ScreenshotError(DFIRLogbookError):
    """Exception raised for screenshot-related errors"""
    pass

# Logging setup
class LogManager:
    def __init__(self):
        self.logger = logging.getLogger("DFIRlogbook")
        self.setup_logging()
        
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # Configure logging
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            "logs/dfirlogbook.log",
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter with ISO8601 timestamp
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03dZ | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        formatter.converter = time.gmtime  # Use UTC time
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_error(self, error, context=None):
        """Log an error with optional context"""
        if context:
            self.logger.error(f"{error} - Context: {context}")
        else:
            self.logger.error(str(error))
    
    def log_info(self, message):
        """Log an info message"""
        self.logger.info(message)
    
    def log_warning(self, message):
        """Log a warning message"""
        self.logger.warning(message)

# Initialize logging
log_manager = LogManager()

# icons resources | commented out for now while revising images for taskbar
# import res_icons

# global utc state
utcState = 1

class ScreenshotCropWindow(QWidget):
    cropped = Signal(QPixmap)

    def __init__(self, screenshot, screen):
        super().__init__()
        self.screenshot = screenshot
        self.screen = screen
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(self.screen.geometry())
        
        # Add size label
        self.sizeLabel = QLabel(self)
        self.sizeLabel.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-family: monospace;
            }
        """)
        self.sizeLabel.hide()
        
        # Add instruction label
        self.instructionLabel = QLabel("Click and drag to select area\nPress Esc to cancel", self)
        self.instructionLabel.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.instructionLabel.setAlignment(Qt.AlignCenter)
        self.instructionLabel.setGeometry(QRect(0, 20, self.width(), 60))
        
        # Add keyboard shortcuts
        self.shortcut_esc = QtGui.QShortcut(QtGui.QKeySequence("Esc"), self)
        self.shortcut_esc.activated.connect(self.close)
        
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            # Draw the screenshot
            painter.drawPixmap(self.rect(), self.screenshot)
            
            # Draw semi-transparent overlay
            overlay = QColor(0, 0, 0, 100)
            painter.fillRect(self.rect(), overlay)
            
            # Draw the selected area without overlay
            if not self.rubberBand.geometry().isEmpty():
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.fillRect(self.rubberBand.geometry(), Qt.transparent)
        finally:
            painter.end()

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()
        self.instructionLabel.hide()

    def mouseMoveEvent(self, event):
        if self.rubberBand.isVisible():
            self.rubberBand.setGeometry(QRect(self.origin, event.position().toPoint()).normalized())
            
            # Update size label
            rect = self.rubberBand.geometry()
            self.sizeLabel.setText(f"{rect.width()} x {rect.height()}")
            self.sizeLabel.adjustSize()
            
            # Position size label above the selection
            label_x = rect.x() + (rect.width() - self.sizeLabel.width()) // 2
            label_y = rect.y() - self.sizeLabel.height() - 5
            self.sizeLabel.move(label_x, label_y)
            self.sizeLabel.show()

    def mouseReleaseEvent(self, event):
        if not self.rubberBand.isVisible():
            return
            
        self.rubberBand.hide()
        self.sizeLabel.hide()
        
        rect = QRect(self.origin, event.position().toPoint()).normalized()
        if rect.width() < 10 or rect.height() < 10:
            self.close()
            return

        devicePixelRatio = self.screen.devicePixelRatio()
        deviceRect = QRect(
            int(rect.x() * devicePixelRatio),
            int(rect.y() * devicePixelRatio),
            int(rect.width() * devicePixelRatio),
            int(rect.height() * devicePixelRatio)
        )

        cropped = self.screenshot.copy(deviceRect)
        self.cropped.emit(cropped)
        self.close()


class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": {
                "background": "#FFFFFF",
                "text": "#000000",
                "accent": "#007AFF",
                "secondary": "#F5F5F5",
                "border": "#E0E0E0",
                "highlight": "#E3F2FD",
                "button_hover": "#0056b3",  # Darker blue for hover
                "button_pressed": "#004494"  # Even darker for pressed state
            },
            "dark": {
                "background": "#1E1E1E",
                "text": "#FFFFFF",
                "accent": "#0A84FF",
                "secondary": "#2C2C2C",
                "border": "#404040",
                "highlight": "#1A3B5C",
                "button_hover": "#0066cc",  # Lighter blue for hover
                "button_pressed": "#0052a3"  # Slightly darker for pressed state
            }
        }
    
    def apply_theme(self, widget, theme_name="light"):
        if theme_name not in self.themes:
            theme_name = "light"
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Create palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme["background"]))
        palette.setColor(QPalette.WindowText, QColor(theme["text"]))
        palette.setColor(QPalette.Base, QColor(theme["secondary"]))
        palette.setColor(QPalette.AlternateBase, QColor(theme["highlight"]))
        palette.setColor(QPalette.Text, QColor(theme["text"]))
        palette.setColor(QPalette.Button, QColor(theme["secondary"]))
        palette.setColor(QPalette.ButtonText, QColor(theme["text"]))
        palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme["background"]))
        
        # Apply palette
        widget.setPalette(palette)
        
        # Apply stylesheet with improved button states
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme["background"]};
                color: {theme["text"]};
            }}
            QTextBrowser {{
                border: 1px solid {theme["border"]};
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit {{
                border: 1px solid {theme["border"]};
                border-radius: 4px;
                padding: 4px;
                background: {theme["secondary"]};
            }}
            QPushButton {{
                background-color: {theme["accent"]};
                color: {theme["background"]};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme["button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {theme["button_pressed"]};
            }}
            QToolBar {{
                background-color: {theme["secondary"]};
                border-bottom: 1px solid {theme["border"]};
            }}
            QStatusBar {{
                background-color: {theme["secondary"]};
                color: {theme["text"]};
            }}
            QToolButton {{
                background-color: {theme["accent"]};
                color: {theme["background"]};
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background-color: {theme["button_hover"]};
            }}
            QToolButton:pressed {{
                background-color: {theme["button_pressed"]};
            }}
        """)

class Ui_MainWindow(object):
    def __init__(self):
        self.entry_sequence = 0  # Initialize sequence counter
        self.attached_files = {}  # Store file paths for entries
        
    def capture_screen(self):
        try:
            # Get the screen where the cursor currently is
            target_screen = QApplication.screenAt(QCursor.pos())
            if not target_screen:
                target_screen = QApplication.primaryScreen()
                log_manager.log_warning("Falling back to primary screen for screenshot")

            self.full_screenshot = target_screen.grabWindow(0)
            if self.full_screenshot.isNull():
                raise ScreenshotError("Failed to capture screen")

            self.crop_window = ScreenshotCropWindow(self.full_screenshot, target_screen)
            self.crop_window.cropped.connect(self._process_screenshot)
            
            log_manager.log_info("Screenshot capture initiated")
            
        except Exception as e:
            log_manager.log_error(e, "Screenshot capture failed")
            QMessageBox.critical(self.central_widget, "Error", "Failed to capture screenshot")

    def _process_screenshot(self, cropped_screenshot):
        try:
            if cropped_screenshot and not cropped_screenshot.isNull():
                # Increment sequence number
                self.entry_sequence += 1
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
                if not os.path.exists("screenshots"):
                    os.makedirs("screenshots")
                
                save_path = os.path.join("screenshots", filename)
                if not cropped_screenshot.save(save_path):
                    raise ScreenshotError("Failed to save screenshot")
                
                # Add screenshot reference to log with sequence number and separator
                log_entry = f"[#{self.entry_sequence:03d}] | {self.current_time()} | Screenshot captured: {filename}\n"
                self.text_browser.insertPlainText(log_entry)
                
                # Auto-scroll to the bottom
                self.text_browser.verticalScrollBar().setValue(
                    self.text_browser.verticalScrollBar().maximum()
                )
                
                log_manager.log_info(f"Screenshot saved: {filename} (Entry #{self.entry_sequence})")
                
        except Exception as e:
            log_manager.log_error(e, "Failed to process screenshot")
            QMessageBox.critical(self.central_widget, "Error", "Failed to save screenshot")

    def add_file_to_log(self):
        """Add a file to the log with a reference"""
        try:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.central_widget,
                "Select File to Add",
                "",
                "All Files (*.*)"
            )
            
            if not file_path:
                return
                
            # Create a files directory if it doesn't exist
            if not os.path.exists("files"):
                os.makedirs("files")
                
            # Copy file to files directory with timestamp
            original_filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"file_{timestamp}_{original_filename}"
            new_path = os.path.join("files", new_filename)
            
            shutil.copy2(file_path, new_path)
            
            # Increment sequence number
            self.entry_sequence += 1
            
            # Add file reference to log using the new filename
            log_entry = f"[#{self.entry_sequence:03d}] | {self.current_time()} | File added: {new_filename}\n"
            self.text_browser.insertPlainText(log_entry)
            
            # Store file reference with the new filename
            self.attached_files[self.entry_sequence] = new_path
            
            # Auto-scroll to the bottom
            self.text_browser.verticalScrollBar().setValue(
                self.text_browser.verticalScrollBar().maximum()
            )
            
            log_manager.log_info(f"File added to log: {new_filename} (Entry #{self.entry_sequence})")
            
        except Exception as e:
            log_manager.log_error(e, "Failed to add file to log")
            QMessageBox.critical(self.central_widget, "Error", "Failed to add file to log")

    def archive_log(self):
        """Archive the current log with timestamp"""
        try:
            # Create archives directory if it doesn't exist
            if not os.path.exists("archives"):
                os.makedirs("archives")
                
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"log_archive_{timestamp}.txt"
            archive_path = os.path.join("archives", archive_name)
            
            # Get current log content
            log_content = self.text_browser.toPlainText()
            
            # Add archive entry to log
            self.entry_sequence += 1
            archive_entry = f"[#{self.entry_sequence:03d}] | {self.current_time()} | Log archived as: {archive_name}\n"
            self.text_browser.insertPlainText(archive_entry)
            
            # Save archive
            with open(archive_path, 'w') as f:
                f.write(log_content)
                
            log_manager.log_info(f"Log archived: {archive_name}")
            
            return archive_path
            
        except Exception as e:
            log_manager.log_error(e, "Failed to archive log")
            QMessageBox.critical(self.central_widget, "Error", "Failed to archive log")
            return None

    def txt_clear(self):
        msg = QMessageBox()
        msg.setWindowTitle("Clear Log?")
        msg.setText("Pressing 'OK' will archive and clear the log")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Cancel)
        msg.buttonClicked.connect(self.clear_action)
        msg.exec()

    def clear_action(self, i):
        if i == QMessageBox.Cancel:
            return
        else:
            # Archive the log first
            archive_path = self.archive_log()
            if archive_path:
                # Clear the text browser
                self.text_browser.setText("")
                # Reset sequence counter
                self.entry_sequence = 0
                # Clear attached files
                self.attached_files = {}
                # Auto-scroll to the bottom
                self.text_browser.verticalScrollBar().setValue(
                    self.text_browser.verticalScrollBar().maximum()
                )

    def setupUi(self, main_window):
        try:
            if not main_window.objectName():
                main_window.setObjectName(u"DFIRlogbook")
            main_window.resize(760, 547)
            
            # Initialize components
            self.central_widget = QtWidgets.QWidget(main_window)
            self.central_widget.setObjectName(u"centralwidget")
            
            # Setup text browser with error handling
            try:
                self.text_browser = QtWidgets.QTextBrowser(self.central_widget)
                self.text_browser.setObjectName(u"textBrowser")
                self.text_browser.setGeometry(QRect(20, 142, 691, 370))
                self.text_browser.setContextMenuPolicy(Qt.CustomContextMenu)
                self.text_browser.customContextMenuRequested.connect(self.show_text_context_menu)
            except Exception as e:
                log_manager.log_error(e, "Failed to setup text browser")
                raise
            
            self.line_edit = QtWidgets.QLineEdit(self.central_widget)
            self.line_edit.setGeometry(QtCore.QRect(20, 50, 331, 31))
            self.line_edit.setObjectName("lineEdit")
            self.label = QtWidgets.QLabel(self.central_widget)
            self.label.setGeometry(QtCore.QRect(20, 30, 58, 16))
            self.label.setObjectName("label")
            self.submit_button = QtWidgets.QPushButton(self.central_widget)
            self.submit_button.setGeometry(QtCore.QRect(20, 100, 100, 32))
            self.submit_button.setObjectName("btnSubmit")
            
            # Add file button
            self.file_button = QtWidgets.QPushButton(self.central_widget)
            self.file_button.setGeometry(QtCore.QRect(130, 100, 100, 32))
            self.file_button.setObjectName("btnFile")
            self.file_button.clicked.connect(self.add_file_to_log)
            
            # Store current tags for next entry (without separate UI elements)
            self.current_entry_tags = []
            self.is_utc = QtWidgets.QCheckBox(self.central_widget)
            self.is_utc.setGeometry(QtCore.QRect(380, 100, 161, 20))
            self.is_utc.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.is_utc.setChecked(True)
            self.is_utc.setObjectName("isUTC")
            self.utc_offset_hours = QtWidgets.QLineEdit(self.central_widget)
            self.utc_offset_hours.setEnabled(False)
            self.utc_offset_hours.setGeometry(QtCore.QRect(460, 50, 31, 31))
            self.utc_offset_hours.setTabletTracking(False)
            self.utc_offset_hours.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
            self.utc_offset_hours.setAcceptDrops(False)
            self.utc_offset_hours.setStatusTip("")
            self.utc_offset_hours.setReadOnly(False)
            self.utc_offset_hours.setObjectName("utcoffsethours")
            self.utc_offset_minutes = QtWidgets.QLineEdit(self.central_widget)
            self.utc_offset_minutes.setEnabled(False)
            self.utc_offset_minutes.setGeometry(QtCore.QRect(530, 50, 51, 31))
            self.utc_offset_minutes.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
            self.utc_offset_minutes.setAcceptDrops(False)
            self.utc_offset_minutes.setStatusTip("")
            self.utc_offset_minutes.setReadOnly(False)
            self.utc_offset_minutes.setObjectName("utcoffsetminutes")
            self.label_2 = QtWidgets.QLabel(self.central_widget)
            self.label_2.setGeometry(QtCore.QRect(379, 49, 71, 31))
            self.label_2.setObjectName("label_2")
            self.label_3 = QtWidgets.QLabel(self.central_widget)
            self.label_3.setGeometry(QtCore.QRect(450, 30, 60, 16))
            self.label_3.setObjectName("label_3")
            self.label_4 = QtWidgets.QLabel(self.central_widget)
            self.label_4.setGeometry(QtCore.QRect(520, 30, 60, 16))
            self.label_4.setObjectName("label_4")
            main_window.setCentralWidget(self.central_widget)
            self.statusbar = QtWidgets.QStatusBar(main_window)
            self.statusbar.setObjectName("statusbar")
            main_window.setStatusBar(self.statusbar)
            
            # Add a status bar label for the current tags
            self.tagStatusLabel = QtWidgets.QLabel("Tags for next entry: None")
            self.statusbar.addPermanentWidget(self.tagStatusLabel)
            self.tool_bar = QtWidgets.QToolBar(main_window)
            self.tool_bar.setMinimumSize(QtCore.QSize(30, 30))
            self.tool_bar.setObjectName("toolBar")
            main_window.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.tool_bar)
            
            # actionCopy
            self.action_copy = QtGui.QAction(main_window)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/main/icons/copy.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.action_copy.setIcon(icon)
            self.action_copy.setObjectName("actionCopy")
            self.tool_bar.addAction(self.action_copy)
            
            # actionClear
            self.action_clear = QtGui.QAction(main_window)
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(":/main/icons/clear.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.action_clear.setIcon(icon1)
            self.action_clear.setObjectName("actionClear")
            self.tool_bar.addAction(self.action_clear)
            
            # actionSave
            self.action_save = QtGui.QAction(main_window)
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap(":/main/icons/save.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.action_save.setIcon(icon2)
            self.action_save.setObjectName("actionSave")
            self.tool_bar.addAction(self.action_save)

            # Add screen capture action
            self.action_screen_capture = QtGui.QAction(main_window)
            icon3 = QtGui.QIcon()
            icon3.addPixmap(QtGui.QPixmap(":/main/icons/camera.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.action_screen_capture.setIcon(icon3)
            self.action_screen_capture.setObjectName("actionScreenCapture")
            self.tool_bar.addAction(self.action_screen_capture)

            # Initialize theme manager
            try:
                self.theme_manager = ThemeManager()
                self.theme_manager.apply_theme(main_window)
            except Exception as e:
                log_manager.log_error(e, "Failed to setup theme")
                # Continue without theme - don't raise
            
            # Add theme toggle button to toolbar
            self.action_toggle_theme = QtGui.QAction(main_window)
            self.action_toggle_theme.setObjectName("actionToggleTheme")
            self.action_toggle_theme.setText("Toggle Theme")
            self.action_toggle_theme.triggered.connect(self.toggle_theme)
            self.tool_bar.addAction(self.action_toggle_theme)

            self.retranslateUi(main_window)
            QtCore.QMetaObject.connectSlotsByName(main_window)
            self.submit_button.clicked.connect(self.copy_txt)
            self.line_edit.returnPressed.connect(self.line_edit_return)
            self.action_copy.triggered.connect(self.clipboard_copy)
            self.action_clear.triggered.connect(self.txt_clear)
            self.action_save.triggered.connect(self.file_save)
            
            # Enable context menu for text browser
            self.text_browser.setContextMenuPolicy(Qt.CustomContextMenu)
            self.text_browser.customContextMenuRequested.connect(self.show_text_context_menu)
            # Make sure tag manager is properly initialized
            if not hasattr(self, 'tag_manager') or self.tag_manager is None:
                self.tag_manager = TagManager()
                
            # Add some default tags if there are none to make tagging more discoverable
            if len(self.tag_manager.get_all_tags()) == 0:
                self.tag_manager.add_tag("Evidence")
                self.tag_manager.add_tag("Important")
                self.tag_manager.add_tag("Follow-up")
            self.is_utc.stateChanged.connect(self.is_utc_state_changed)
            self.action_screen_capture.triggered.connect(self.capture_screen)

            log_manager.log_info("UI setup completed successfully")
            
        except Exception as e:
            log_manager.log_error(e, "Failed to setup UI")
            raise

    def is_utc_state_changed(self, int):
        if self.is_utc.isChecked():
            self.is_utc_state(False, 1)
        else:
            self.is_utc_state(True, 0)

    def is_utc_state(self, arg0, arg1):
        global utcState
        self.utc_offset_hours.setEnabled(arg0)
        self.utc_offset_minutes.setEnabled(arg0)
        utcState = arg1

    def current_time(self):
        if utcState == 1:
            local_datetime = datetime.now()
            local_datetime = local_datetime.replace(microsecond=0)
            date_time = local_datetime.astimezone(timezone.utc)
        else:
            delta_hours = int(self.utc_offset_hours.text())
            delta_minutes = int(self.utc_offset_minutes.text())
            date_time = datetime.utcnow().replace(microsecond=0) + timedelta(hours=delta_hours, minutes=delta_minutes)
        return date_time.isoformat()

    def copy_txt(self):
        try:
            text = self.line_edit.text()
            if not text:
                return
                
            if utcState == 1:
                self.is_utc.setChecked(True)
                self.utc_offset_hours.setEnabled(False)
                self.utc_offset_minutes.setEnabled(False)
                delta_hours = 0
                delta_minutes = 0
            else:
                self.is_utc.setChecked(False)
                self.utc_offset_hours.setEnabled(True)
                self.utc_offset_minutes.setEnabled(True)
                
                try:
                    delta_hours = int(self.utc_offset_hours.text())
                except:
                    delta_hours = 0
                    self.utc_offset_hours.setText("0")
                try:
                    delta_minutes = int(self.utc_offset_minutes.text())
                except:
                    delta_minutes = 0
                    self.utc_offset_minutes.setText("0")

                if delta_hours > 12 or delta_hours < -12:
                    delta_hours = 0
                    self.utc_offset_hours.setText("0")
                if delta_minutes >= 60 or delta_minutes < 0:
                    delta_minutes = 0
                    self.utc_offset_minutes.setText("0")
                    
            # Get timestamp
            timestamp = self.current_time()
            if utcState != 1:
                if delta_hours >= 0:
                    timestamp = f"{timestamp}+{delta_hours:02}:{delta_minutes:02}"
                else:
                    timestamp = f"{timestamp}{delta_hours:03}:{delta_minutes:02}"
            
            # Check if there's a selection
            cursor = self.text_browser.textCursor()
            if cursor.hasSelection():
                # If there's a selection, warn the user
                msg = QMessageBox()
                msg.setWindowTitle("Warning")
                msg.setText("You have text selected. Adding a new entry will not modify existing entries.")
                msg.setIcon(QMessageBox.Warning)
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.setDefaultButton(QMessageBox.Cancel)
                
                if msg.exec() == QMessageBox.Cancel:
                    return
                
                # Clear the selection
                cursor.clearSelection()
                self.text_browser.setTextCursor(cursor)
            
            # Increment sequence number
            self.entry_sequence += 1
            
            # Format the entry with tags if any are selected
            if self.current_entry_tags:
                # Store the current tags for the new entry
                entry_idx = self.text_browser.document().blockCount()  # Current block count before adding new entry
                for tag in self.current_entry_tags:
                    self.tag_manager.tag_entry(entry_idx, tag)
                
                # Format with tags and sequence number
                tags_str = "[" + ", ".join(self.current_entry_tags) + "]"
                entry_text = f"[#{self.entry_sequence:03d}] | {timestamp} {tags_str} | {text} \n"
            else:
                # Standard format without tags but with sequence number
                entry_text = f"[#{self.entry_sequence:03d}] | {timestamp} | {text} \n"
            
            # Move cursor to end of document
            cursor = self.text_browser.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.text_browser.setTextCursor(cursor)
            
            # Add the new entry
            self.text_browser.insertPlainText(entry_text)
            self.line_edit.clear()
            
            # Auto-scroll to the bottom
            self.text_browser.verticalScrollBar().setValue(
                self.text_browser.verticalScrollBar().maximum()
            )

            log_manager.log_info(f"New entry #{self.entry_sequence} added to log")
            
        except Exception as e:
            log_manager.log_error(e, "Failed to add entry")
            QMessageBox.critical(self.central_widget, "Error", "Failed to add entry to log")

    def show_tag_dialog(self):
        """Show dialog for adding tags to the next entry"""
        # Create tag selection dialog
        menu = QMenu(self.central_widget)
        
        # Add existing tags section
        existing_tags = self.tag_manager.get_all_tags()
        if existing_tags:
            for tag in existing_tags:
                action = QAction(tag, menu)
                action.setCheckable(True)
                # Check if tag is already selected for current entry
                if tag in self.current_entry_tags:
                    action.setChecked(True)
                def connect_and_close(act, func):
                    def wrapper(checked=False):
                        func(checked)
                        menu.close()
                    act.triggered.connect(wrapper)
                connect_and_close(action, lambda checked, t=tag: self.toggle_current_tag(t, checked))
                menu.addAction(action)
            menu.addSeparator()
        
        # Add 'New Tag' option
        new_tag_action = QAction("New Tag...", menu)
        new_tag_action.triggered.connect(lambda: (self.create_new_current_tag(), menu.close()))
        menu.addAction(new_tag_action)
        
        # Add 'Clear All Tags' option if we have tags
        if self.current_entry_tags:
            menu.addSeparator()
            clear_action = QAction("Clear All Tags", menu)
            clear_action.triggered.connect(lambda: (self.clear_current_tags(), menu.close()))
        
        # Show the menu at the button's position
        menu.exec(self.tagButton.mapToGlobal(QPoint(0, self.tagButton.height())))
    
    def toggle_current_tag(self, tag, checked):
        """Toggle a tag for the next entry"""
        if checked and tag not in self.current_entry_tags:
            self.current_entry_tags.append(tag)
            # Add to available tags if not already there
            self.tag_manager.add_tag(tag)
        elif not checked and tag in self.current_entry_tags:
            self.current_entry_tags.remove(tag)
        
        # Update the tag display
        self.update_current_tags_display()
    
    def create_new_current_tag(self):
        """Create a new tag for the next entry"""
        tag, ok = QInputDialog.getText(self.central_widget, "New Tag", "Enter tag name:")
        if ok and tag:
            self.tag_manager.add_tag(tag)
            if tag not in self.current_entry_tags:
                self.current_entry_tags.append(tag)
                self.update_current_tags_display()
    
    def clear_current_tags(self):
        """Clear all tags for the next entry"""
        self.current_entry_tags = []
        self.update_current_tags_display()
    
    def update_current_tags_display(self):
        """Update the status bar display of current tags"""
        if not self.current_entry_tags:
            self.tagStatusLabel.setText("Tags for next entry: None")
        else:
            tags_text = ", ".join(self.current_entry_tags)
            self.tagStatusLabel.setText(f"Tags for next entry: {tags_text}")
            
    def line_edit_return(self):
        """Handle return key press in line edit"""
        # Check if there's a selection
        cursor = self.text_browser.textCursor()
        if cursor.hasSelection():
            # If there's a selection, warn the user
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("You have text selected. Adding a new entry will not modify existing entries.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            
            if msg.exec() == QMessageBox.Cancel:
                return
            
            # Clear the selection
            cursor.clearSelection()
            self.text_browser.setTextCursor(cursor)
        
        self.copy_txt()

    def clipboard_copy(self):
        cursor = self.text_browser.textCursor()
        cursor.clearSelection()
        self.text_browser.selectAll()
        self.text_browser.copy()
        self.text_browser.setTextCursor(cursor)

    def show_text_context_menu(self, position):
        """Enhanced context menu for text browser with tagging options"""
        cursor = self.text_browser.cursorForPosition(position)
        
        # Check if there's a selection
        if self.text_browser.textCursor().hasSelection():
            # If there's a selection, use the block number of the selection start
            cursor = self.text_browser.textCursor()
            cursor.setPosition(cursor.selectionStart())
        
        # Get the line under cursor
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        selected_text = cursor.selectedText()
        
        # If no text is selected or the line is empty, return
        if not selected_text.strip():
            return
        
        # Highlight the selected line to make it clear which entry is being tagged
        self.highlight_selected_line(cursor)
        
        # Create menu
        menu = QMenu()
        
        # Add standard edit options
        copy_action = menu.addAction("Copy Line")
        copy_action.triggered.connect(lambda: self.copy_selected_line(cursor))
        menu.addSeparator()
        
        # Get entry index (line number)
        entry_idx = cursor.blockNumber()
        
        # Verify this is a valid entry (has timestamp)
        if not self.is_valid_entry(selected_text):
            menu.addAction("⚠️ Invalid Entry").setEnabled(False)
            menu.exec(self.text_browser.mapToGlobal(position))
            self.remove_highlight(cursor)
            return
        
        # Tagging section title
        menu.addSection("Tagging Options")
        
        # Always show the 'Tags for Next Entry' menu
        next_entry_menu = menu.addMenu("📝 Tags for Next Entry")
        
        # Add existing tags section with checkboxes
        existing_tags = self.tag_manager.get_all_tags()
        if existing_tags:
            for tag in existing_tags:
                action = QAction(tag, next_entry_menu)
                action.setCheckable(True)
                if tag in self.current_entry_tags:
                    action.setChecked(True)
                def connect_and_close(act, func):
                    def wrapper(checked=False):
                        func(checked)
                        menu.close()
                    act.triggered.connect(wrapper)
                connect_and_close(action, lambda checked, t=tag: self.toggle_current_tag(t, checked))
                next_entry_menu.addAction(action)
            next_entry_menu.addSeparator()
        
        # New tag option for next entry
        new_next_tag = next_entry_menu.addAction("➕ New Tag...")
        new_next_tag.triggered.connect(lambda: (self.create_new_current_tag(), menu.close()))
        
        # Clear tags option if we have any
        if self.current_entry_tags:
            next_entry_menu.addSeparator()
            clear_action = next_entry_menu.addAction("❌ Clear All Tags")
            clear_action.triggered.connect(lambda: (self.clear_current_tags(), menu.close()))
        
        # Tag existing entry submenu
        tag_menu = menu.addMenu("🏷️ Tag This Entry #{0}".format(entry_idx+1))
        
        # Add existing tags section with checkboxes
        existing_tags = self.tag_manager.get_all_tags()
        if existing_tags:
            for tag in existing_tags:
                action = tag_menu.addAction(tag)
                # Show checkbox for existing tags on this entry
                action.setCheckable(True)
                # Get current tags for this entry
                entry_tags = self.tag_manager.get_entry_tags(entry_idx)
                # Set checked state based on actual tags
                action.setChecked(tag in entry_tags)
                def connect_and_close(act, func):
                    def wrapper(checked=False):
                        func(checked)
                        menu.close()
                    act.triggered.connect(wrapper)
                connect_and_close(action, lambda checked, t=tag, idx=entry_idx: self.toggle_tag_on_entry(idx, t, checked))
            tag_menu.addSeparator()
        
        # Add 'New Tag' option
        new_tag_action = tag_menu.addAction("➕ New Tag...")
        new_tag_action.triggered.connect(lambda: (self.create_new_tag(entry_idx), menu.close()))
        
        # Add 'Clear All Tags for this Entry' option if it has tags
        entry_tags = self.tag_manager.get_entry_tags(entry_idx)
        if entry_tags:
            tag_menu.addSeparator()
            clear_entry_action = tag_menu.addAction("❌ Clear All Tags from this Entry")
            clear_entry_action.triggered.connect(lambda: (self.clear_entry_tags(entry_idx), menu.close()))
        
        # Show the menu
        menu.exec(self.text_browser.mapToGlobal(position))
        # Ensure menu closes highlight if user clicks away without choosing
        self.remove_highlight(cursor)
    
    def copy_selected_line(self, cursor):
        """Copy the selected line to clipboard"""
        # If there's a selection, use that instead of the whole line
        if self.text_browser.textCursor().hasSelection():
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(self.text_browser.textCursor().selectedText())
        else:
            # Otherwise copy the whole line
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(cursor.selectedText())
    
    def highlight_selected_line(self, cursor):
        """Temporarily highlight the selected line to make it clear which entry is being tagged"""
        # Save the original cursor and selection
        original_cursor = self.text_browser.textCursor()
        
        # If there's a selection, use that instead of the whole line
        if original_cursor.hasSelection():
            # Get the block containing the selection start
            cursor.setPosition(original_cursor.selectionStart())
        
        # Set the temporary highlight
        highlight_format = QtGui.QTextCharFormat()
        highlight_format.setBackground(QtGui.QColor(240, 240, 150))  # Light yellow background
        
        # Apply the highlight to the selected line
        self.text_browser.setTextCursor(cursor)
        
        # Schedule removal of highlight after a short delay (2 seconds)
        QtCore.QTimer.singleShot(2000, lambda: self.remove_highlight(original_cursor))
    
    def remove_highlight(self, original_cursor):
        """Remove the temporary highlight and restore the original cursor"""
        # Restore the document's default style
        self.text_browser.setTextCursor(original_cursor)
        
    def toggle_tag_on_entry(self, entry_idx, tag, checked):
        """Toggle a tag on an existing entry"""
        try:
            # Verify the entry exists
            if entry_idx >= self.text_browser.document().blockCount():
                raise TagError(f"Entry index {entry_idx} is out of range")
            
            # Get the text of the entry to verify it's valid
            cursor = self.text_browser.textCursor()
            cursor.movePosition(QtGui.QTextCursor.Start)
            cursor.movePosition(QtGui.QTextCursor.Down, QtGui.QTextCursor.MoveAnchor, entry_idx)
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            entry_text = cursor.selectedText()
            
            if not entry_text.strip():
                raise TagError(f"Entry {entry_idx} is empty or invalid")
            
            if checked:
                self.add_tag_to_entry(entry_idx, tag)
            else:
                self.remove_tag_from_entry(entry_idx, tag)
            
            # Close the context menu after tagging
            self.text_browser.clearFocus()
            # Force immediate refresh of the display
            self.refresh_entry_display()
            
        except Exception as e:
            log_manager.log_error(e, f"Failed to toggle tag {tag} on entry {entry_idx}")
            QMessageBox.critical(self.central_widget, "Error", "Failed to update tag")
    
    def add_tag_to_entry(self, entry_idx, tag):
        """Add a tag to a specific entry and update the display"""
        try:
            self.tag_manager.tag_entry(entry_idx, tag)
            self.refresh_entry_display()
        except Exception as e:
            log_manager.log_error(e, f"Failed to add tag {tag} to entry {entry_idx}")
            raise
    
    def remove_tag_from_entry(self, entry_idx, tag):
        """Remove a tag from an entry and update the display"""
        try:
            self.tag_manager.untag_entry(entry_idx, tag)
            self.refresh_entry_display()
        except Exception as e:
            log_manager.log_error(e, f"Failed to remove tag {tag} from entry {entry_idx}")
            raise
    
    def refresh_entry_display(self):
        """Update the text browser to show tags"""
        try:
            # Save current cursor position and scroll value
            cursor = self.text_browser.textCursor()
            scroll_pos = self.text_browser.verticalScrollBar().value()
            
            text = self.text_browser.toPlainText()
            entries = text.split('\n')
            
            # Format entries with tags
            new_text = []
            for i, entry in enumerate(entries):
                if entry.strip():
                    # Check if entry already has tags formatted in it
                    # Extract content by finding the pipe separator
                    if ' | ' in entry:
                        # Remove existing tags if present
                        if '[' in entry and ']' in entry and ' | ' in entry:
                            # Extract sequence, timestamp and content parts
                            parts = entry.split(' | ', 1)
                            header_part = parts[0]
                            content_part = parts[1]
                            
                            # Extract sequence number
                            sequence_end = header_part.find(']')
                            sequence = header_part[2:sequence_end]
                            
                            # Extract timestamp
                            timestamp_part = header_part[sequence_end+1:].strip()
                            if '[' in timestamp_part and ']' in timestamp_part:
                                timestamp = timestamp_part.split('[')[0].strip()
                            else:
                                timestamp = timestamp_part
                            
                            # Format with current tags
                            new_entry = self.tag_manager.format_entry_with_tags(timestamp, content_part, i, sequence)
                            new_text.append(new_entry)
                        else:
                            # Standard format without tags
                            parts = entry.split(' | ', 1)
                            header_part = parts[0]
                            content = parts[1]
                            
                            # Extract sequence number
                            sequence_end = header_part.find(']')
                            sequence = header_part[2:sequence_end]
                            
                            # Extract timestamp
                            timestamp = header_part[sequence_end+1:].strip()
                            
                            new_entry = self.tag_manager.format_entry_with_tags(timestamp, content, i, sequence)
                            new_text.append(new_entry)
                    else:
                        new_text.append(entry)  # Keep unchanged if format doesn't match
                else:
                    new_text.append(entry)  # Keep blank lines
            
            # Update display
            self.text_browser.setPlainText('\n'.join(new_text))
            
            # Restore cursor position and scroll value
            self.text_browser.setTextCursor(cursor)
            self.text_browser.verticalScrollBar().setValue(scroll_pos)
            
            # Ensure the last entry is visible
            self.text_browser.verticalScrollBar().setValue(
                self.text_browser.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            log_manager.log_error(e, "Failed to refresh entry display")
            raise

    def file_save(self):
        try:
            # Launch modular template builder dialog
            tmpl = TemplateDialog(self.tag_manager, self.central_widget)
            if tmpl.exec() != QDialog.Accepted:
                return

            modules = tmpl.get_modules()
            if not modules:
                QMessageBox.warning(self.central_widget, "No sections", "Add at least one section to the template.")
                return
            image_scale_percent = tmpl.get_image_scale_percent()

            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save Report as... (.pdf)", None, "PDF files (*.pdf)")
            if not save_path:
                return

            # Get current log entries
            entries = self.text_browser.toPlainText().split('\n')

            # Create a custom DocTemplate with footer
            class DFIRDocTemplate(BaseDocTemplate):
                def __init__(self, filename, **kwargs):
                    BaseDocTemplate.__init__(self, filename, **kwargs)
                    self.pagesize = letter
                    self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # Define frames
                    frame = Frame(self.leftMargin, self.bottomMargin, 
                                 self.width, self.height - 20, # Reserve space for footer
                                 id='normal')
                    
                    # Add page template with footer
                    template = PageTemplate(id='with_footer', frames=[frame], onPage=self.add_footer)
                    self.addPageTemplates([template])
                
                def add_footer(self, canvas, doc):
                    canvas.saveState()
                    # Draw horizontal line above footer
                    canvas.setStrokeColor(colors.grey)
                    canvas.line(doc.leftMargin, doc.bottomMargin - 10, 
                             doc.leftMargin + doc.width, doc.bottomMargin - 10)
                    # Add footer text
                    canvas.setFont('Helvetica', 8)
                    # Left - timestamp
                    canvas.drawString(doc.leftMargin, doc.bottomMargin - 25, f"Generated: {self.timestamp}")
                    # Center - DFIRlogbook version
                    canvas.drawCentredString(doc.leftMargin + doc.width/2, doc.bottomMargin - 25, 
                                          f"DFIRlogbook v{VERSION}")
                    # Right - page number
                    page_num = canvas.getPageNumber()
                    canvas.drawRightString(doc.leftMargin + doc.width, doc.bottomMargin - 25, 
                                        f"Page {page_num}")
                    canvas.restoreState()

            # Ask for report folder name
            folder_name, ok = QInputDialog.getText(
                self.central_widget,
                "Report Folder",
                "Enter name for report folder:",
                text=os.path.splitext(os.path.basename(save_path))[0]
            )
            
            if not ok or not folder_name:
                return
                
            # Create report folder
            report_folder = os.path.join(os.path.dirname(save_path), folder_name)
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
                
            # Copy log to report folder
            log_content = self.text_browser.toPlainText()
            log_path = os.path.join(report_folder, "log.txt")
            with open(log_path, 'w') as f:
                f.write(log_content)
                
            # Copy only referenced screenshots
            if os.path.exists("screenshots"):
                screenshots_folder = os.path.join(report_folder, "screenshots")
                os.makedirs(screenshots_folder, exist_ok=True)
                
                # Extract screenshot filenames from log entries
                screenshot_files = set()
                for entry in entries:
                    if "Screenshot captured:" in entry:
                        try:
                            filename = entry.split(': ')[-1].strip()
                            screenshot_files.add(filename)
                        except:
                            continue
                
                # Copy only the referenced screenshots
                for filename in screenshot_files:
                    src_path = os.path.join("screenshots", filename)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(screenshots_folder, filename))
                        
            # Copy only referenced files
            if self.attached_files:
                files_folder = os.path.join(report_folder, "files")
                os.makedirs(files_folder, exist_ok=True)
                
                # Extract file references from log entries
                file_entries = set()
                for entry in entries:
                    if "File added:" in entry:
                        try:
                            filename = entry.split(': ')[-1].strip()
                            file_entries.add(filename)
                        except:
                            continue
                
                # Copy only the referenced files
                for entry_idx, file_path in self.attached_files.items():
                    if os.path.exists(file_path):
                        # Get the filename as it appears in the log
                        stored_filename = os.path.basename(file_path)
                        if stored_filename in file_entries:
                            # Copy the file with the same name as in the log
                            shutil.copy2(file_path, os.path.join(files_folder, stored_filename))
                            log_manager.log_info(f"Copied file to report: {stored_filename}")

            # Generate PDF in report folder
            pdf_path = os.path.join(report_folder, os.path.basename(save_path))
            
            # Create document
            doc = DFIRDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            def append_entry(entry, show_numbers=True):
                if not entry.strip():
                    return
                    
                # Extract sequence number if present
                sequence = ""
                if entry.startswith('[#') and ']' in entry:
                    end_seq = entry.find(']')
                    sequence = entry[2:end_seq]
                    entry = entry[end_seq+1:].strip()
                
                # Remove tags from the entry
                if '[' in entry and ']' in entry and ' | ' in entry:
                    # Split into timestamp and content
                    parts = entry.split(' | ', 1)
                    timestamp_part = parts[0]
                    content_part = parts[1]
                    
                    # Remove tags from timestamp part
                    if '[' in timestamp_part and ']' in timestamp_part:
                        timestamp = timestamp_part.split('[')[0].strip()
                    else:
                        timestamp = timestamp_part
                    
                    # Reconstruct entry without tags
                    if sequence and show_numbers:
                        formatted_entry = f"[#{sequence}] | {timestamp} | {content_part}"
                    else:
                        formatted_entry = f"{timestamp} | {content_part}"
                else:
                    if sequence and show_numbers:
                        formatted_entry = f"[#{sequence}] | {entry}"
                    else:
                        formatted_entry = entry

                # Handle screenshots specially
                if "Screenshot captured:" in entry:
                    story.append(Paragraph(formatted_entry, styles['Normal']))
                    story.append(Spacer(1, 12))
                    screenshot_name = entry.split(': ')[-1].strip()
                    img_path = os.path.join(screenshots_folder, screenshot_name)
                    if os.path.exists(img_path):
                        img = Image(img_path)
                        max_width = (6 * 72) * (image_scale_percent / 100.0)
                        aspect = img.imageWidth / img.imageHeight if img.imageHeight else 1
                        img_width = min(max_width, img.imageWidth)
                        img_height = img_width / aspect
                        img.drawWidth = img_width
                        img.drawHeight = img_height
                        story.append(img)
                        story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph(formatted_entry, styles['Normal']))
                    story.append(Spacer(1, 12))

            # Build story from modules
            for module in modules:
                module_type = module.get('type')
                show_numbers = module.get('show_entry_numbers', True)
                
                if module_type == 'title':
                    story.append(Paragraph(module.get('text', ''), styles['Title']))
                    story.append(Spacer(1, 12))
                elif module_type == 'divider':
                    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
                    story.append(Spacer(1, 6))
                elif module_type == 'comments':
                    if module.get('header'):
                        story.append(Paragraph(module.get('header'), styles['Heading2']))
                        story.append(Spacer(1, 6))
                    story.append(Paragraph(module.get('text', '').replace('\n', '<br />'), styles['Normal']))
                    story.append(Spacer(1, 12))
                elif module_type == 'all':
                    for entry in entries:
                        append_entry(entry, show_numbers)
                elif module_type == 'tag':
                    tag = module.get('tag')
                    if module.get('header'):
                        story.append(Paragraph(tag, styles['Heading2']))
                        story.append(Spacer(1, 6))
                    entry_indices = self.tag_manager.get_entries_with_tag(tag)
                    for idx in entry_indices:
                        if 0 <= idx < len(entries):
                            append_entry(entries[idx], show_numbers)

            doc.build(story)

            # Ask if user wants to clear the log
            msg = QMessageBox()
            msg.setWindowTitle("Clear Log?")
            msg.setText("Would you like to archive and clear the log?")
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            
            if msg.exec() == QMessageBox.Yes:
                self.clear_action(QMessageBox.Ok)

            log_manager.log_info(f"Report saved: {pdf_path}")
            
        except Exception as e:
            log_manager.log_error(e, "Failed to save report")
            QMessageBox.critical(self.central_widget, "Error", "Failed to save report")

    def retranslateUi(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("DFIRlogbook", "DFIRlogbook"))
        self.line_edit.setStatusTip(_translate("DFIRlogbook", "Input Entry Field"))
        self.action_copy.setStatusTip(_translate("DFIRlogbook", "Copy to Clipboard"))
        self.action_clear.setStatusTip(_translate("DFIRlogbook", "Clear Output Field"))
        self.label.setText(_translate("DFIRlogbook", "ENTRY:"))
        self.submit_button.setText(_translate("DFIRlogbook", "Submit"))
        self.file_button.setText(_translate("DFIRlogbook", "Add File"))
        self.tool_bar.setWindowTitle(_translate("DFIRlogbook", "toolBar"))
        self.action_copy.setText(_translate("DFIRlogbook", "Copy"))
        self.action_clear.setText(_translate("DFIRlogbook", "Clear"))
        self.action_save.setText(_translate("DFIRlogbook", "Save"))
        self.action_screen_capture.setText(_translate("DFIRlogbook", "Screenshot"))
        self.action_screen_capture.setStatusTip(_translate("DFIRlogbook", "Capture a region of the screen"))
        self.is_utc.setText(_translate("DFIRlogbook", "Timezone: UTC"))
        self.utc_offset_hours.setText(_translate("DFIRlogbook", "00"))
        self.utc_offset_minutes.setText(_translate("DFIRlogbook", "00"))
        self.label_2.setText(_translate("DFIRlogbook", "UTC offset"))
        self.label_3.setText(_translate("DFIRlogbook", "hours:"))
        self.label_4.setText(_translate("DFIRlogbook", "minutes:"))

    def toggle_theme(self):
        new_theme = "dark" if self.theme_manager.current_theme == "light" else "light"
        self.theme_manager.apply_theme(self.central_widget.parent(), new_theme)

    def is_valid_entry(self, text):
        """Check if the text represents a valid entry (has timestamp and sequence number)"""
        try:
            # Check if the text contains a sequence number and timestamp
            if ' | ' not in text or '[#' not in text:
                return False
                
            # Split the entry into sequence, timestamp, and content
            parts = text.split(' | ', 2)  # Split into max 3 parts
            if len(parts) < 2:  # Need at least sequence and timestamp
                return False
                
            header_part = parts[0]
            
            # Extract sequence number
            if not header_part.startswith('[#') or ']' not in header_part:
                return False
                
            sequence_part = header_part.split(']', 1)[0]
            if not sequence_part[2:].isdigit():
                return False
            
            # Extract timestamp part (now after the first separator)
            timestamp_part = parts[1].strip()
            
            # Remove any tags from the timestamp part
            if '[' in timestamp_part and ']' in timestamp_part:
                timestamp_part = timestamp_part.split('[')[0].strip()
            
            # Basic validation of timestamp format
            if not any(c.isdigit() for c in timestamp_part):
                return False
                
            # Check for proper ISO8601 format components
            if not ('T' in timestamp_part and '-' in timestamp_part):
                return False
                
            return True
            
        except Exception as e:
            log_manager.log_error(e, "Failed to validate entry")
            return False

class TagManager:
    """Manages tags for log entries"""
    def __init__(self):
        self.tags = set()  # Available tags
        self.entry_tags = {}  # Maps entry indexes to list of tags
        
    def add_tag(self, tag):
        """Add a new tag to available tags"""
        if tag and tag.strip():
            self.tags.add(tag.strip())
            return True
        return False
    
    def remove_tag(self, tag):
        """Remove tag from available tags"""
        if tag in self.tags:
            self.tags.remove(tag)
            # Remove from any entries
            for idx in self.entry_tags:
                if tag in self.entry_tags[idx]:
                    self.entry_tags[idx].remove(tag)
            return True
        return False
    
    def tag_entry(self, entry_idx, tag):
        """Add tag to an entry"""
        if tag not in self.tags:
            self.add_tag(tag)
            
        if entry_idx not in self.entry_tags:
            self.entry_tags[entry_idx] = set()
        
        self.entry_tags[entry_idx].add(tag)
        return True
    
    def untag_entry(self, entry_idx, tag):
        """Remove tag from an entry"""
        if entry_idx in self.entry_tags and tag in self.entry_tags[entry_idx]:
            self.entry_tags[entry_idx].remove(tag)
            return True
        return False
    
    def get_entry_tags(self, entry_idx):
        """Get all tags for an entry"""
        if entry_idx in self.entry_tags:
            return sorted(list(self.entry_tags[entry_idx]))
        return []
    
    def get_all_tags(self):
        """Get all available tags"""
        return sorted(list(self.tags))
    
    def get_entries_with_tag(self, tag):
        """Get all entries that have a specific tag"""
        result = []
        for entry_idx in self.entry_tags:
            if tag in self.entry_tags[entry_idx]:
                result.append(entry_idx)
        return result
    
    def format_entry_with_tags(self, timestamp, text, entry_idx, sequence=None):
        """Format an entry with its tags"""
        tags = self.get_entry_tags(entry_idx)
        if tags:
            tags_str = "[" + ", ".join(tags) + "]"
            if sequence:
                return f"[#{sequence}] {timestamp} {tags_str} | {text}"
            return f"{timestamp} {tags_str} | {text}"
        else:
            if sequence:
                return f"[#{sequence}] {timestamp} | {text}"
            return f"{timestamp} | {text}"

class ReportSelectionDialog(QDialog):
    """Dialog for selecting entries to include in a report"""
    def __init__(self, entries, tag_manager, parent=None):
        # Make sure we have a valid QWidget parent or None
        if parent is not None and not isinstance(parent, QtWidgets.QWidget):
            parent = None
        super().__init__(parent)
        self.entries = entries
        self.tag_manager = tag_manager
        self.selected_entries = []
        self.tag_filters = []
        
        self.setWindowTitle("Select Entries for Report")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Tag filter section
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Filter by tags:"))
        
        self.tag_list = QListWidget()
        for tag in self.tag_manager.get_all_tags():
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.tag_list.addItem(item)
        self.tag_list.itemChanged.connect(self.update_filtered_entries)
        tag_layout.addWidget(self.tag_list)
        
        layout.addLayout(tag_layout)
        
        # Entry list with checkboxes
        self.entry_list = QListWidget()
        for i, entry in enumerate(self.entries):
            if entry.strip():  # Skip empty entries
                item = QListWidgetItem(entry)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)  # Default to checked
                item.setData(Qt.UserRole, i)  # Store original index
                self.entry_list.addItem(item)
                
        layout.addWidget(self.entry_list)
        
        # Select all/none buttons
        select_buttons = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self.select_all_entries)
        select_buttons.addWidget(select_all)
        select_none = QPushButton("Select None")
        select_none.clicked.connect(self.select_no_entries)
        select_buttons.addWidget(select_none)
        layout.addLayout(select_buttons)
        
        # Buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_cancel = QHBoxLayout()
        ok_cancel.addWidget(ok_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        ok_cancel.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
        
    def update_filtered_entries(self):
        """Update entry list based on selected tag filters"""
        # Get selected tags
        selected_tags = []
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_tags.append(item.text())
        
        # If no tags selected, show all entries
        if not selected_tags:
            for i in range(self.entry_list.count()):
                self.entry_list.item(i).setHidden(False)
            return
            
        # Otherwise filter by tags
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            entry_idx = item.data(Qt.UserRole)
            
            # Get tags for this entry
            entry_tags = self.tag_manager.get_entry_tags(entry_idx)
            
            # Hide if no intersection with selected tags
            show_entry = any(tag in entry_tags for tag in selected_tags)
            item.setHidden(not show_entry)
    
    def select_all_entries(self):
        """Select all visible entries"""
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)
    
    def select_no_entries(self):
        """Deselect all entries"""
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Unchecked)
    
    def get_selected_entries(self):
        """Get selected entry indexes"""
        selected = []
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if item.checkState() == Qt.Checked and not item.isHidden():
                selected.append(item.data(Qt.UserRole))
        return selected


# ------------------ Template Builder ------------------

class TemplateDialog(QDialog):
    """Dialog that lets users assemble report sections via drag & drop"""
    
    def __init__(self, tag_manager, parent=None):
        # Ensure parent is a QWidget
        if parent is not None and not isinstance(parent, QtWidgets.QWidget):
            parent = None
        super().__init__(parent)

        self.tag_manager = tag_manager
        self.setWindowTitle("Report Template Builder")
        self.resize(400, 500)

        main_layout = QVBoxLayout(self)

        # Add checkbox for entry numbers
        self.show_entry_numbers = QCheckBox("Include Entry Numbers in Report")
        self.show_entry_numbers.setChecked(True)  # Default to showing numbers
        self.show_entry_numbers.setToolTip("When checked, entry numbers will be included in the report output")
        main_layout.addWidget(self.show_entry_numbers)

        # Screenshot size control
        image_size_layout = QHBoxLayout()
        image_size_layout.addWidget(QLabel("Screenshot width in PDF:"))
        self.image_size_combo = QComboBox()
        self.image_size_combo.addItems(["100%", "85%", "70%", "55%", "40%"])
        self.image_size_combo.setCurrentText("70%")
        self.image_size_combo.setToolTip("Controls maximum screenshot width in the generated PDF while preserving aspect ratio")
        image_size_layout.addWidget(self.image_size_combo)
        main_layout.addLayout(image_size_layout)

        # Draggable / reorderable list
        self.module_list = QListWidget()
        self.module_list.setDragDropMode(QAbstractItemView.InternalMove)
        main_layout.addWidget(self.module_list)

        # Controls for adding / removing modules
        controls = QHBoxLayout()
        self.module_type = QComboBox()
        self.module_type.addItems(["Title", "Divider", "All Entries", "Tag Section", "Comments"])
        controls.addWidget(self.module_type)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_module)
        controls.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_module)
        controls.addWidget(remove_btn)

        main_layout.addLayout(controls)

        # OK / Cancel buttons
        ok_cancel = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_cancel.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_cancel.addWidget(cancel_btn)
        main_layout.addLayout(ok_cancel)

    # ---------- module management ----------

    def add_module(self):
        mtype = self.module_type.currentText()

        if mtype == "Title":
            text, ok = QInputDialog.getText(self, "Section Title", "Enter title text:")
            if not ok or not text.strip():
                return
            item = QListWidgetItem(f"Title: {text}")
            item.setData(Qt.UserRole, {"type": "title", "text": text})

        elif mtype == "Divider":
            item = QListWidgetItem("Divider")
            item.setData(Qt.UserRole, {"type": "divider"})

        elif mtype == "All Entries":
            item = QListWidgetItem("All Entries")
            item.setData(Qt.UserRole, {"type": "all"})

        elif mtype == "Tag Section":
            tags = sorted(list(self.tag_manager.tags))
            if not tags:
                QMessageBox.warning(self, "No tags available", "There are no tags to select.")
                return
            tag, ok = QInputDialog.getItem(self, "Select Tag", "Tag:", tags, 0, False)
            if not ok:
                return
            include_header = QMessageBox.question(self, "Include Header?", f"Include header for tag '{tag}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
            item = QListWidgetItem(f"Tag: {tag}{' (Header)' if include_header else ''}")
            item.setData(Qt.UserRole, {"type": "tag", "tag": tag, "header": include_header})
        elif mtype == "Comments":
            # Ask for header first
            header, ok = QInputDialog.getText(self, "Comments Header", "Enter header text (optional):")
            if not ok:
                return
                
            # Then get the comments
            text, ok = QInputDialog.getMultiLineText(self, "Comments", "Enter comments:")
            if not ok or not text.strip():
                return
                
            # Create preview text
            preview = text.strip().split('\n')[0]
            if len(preview) > 30:
                preview = preview[:27] + '...'
                
            # Show header in preview if provided
            if header:
                item = QListWidgetItem(f"Comments: {header} - {preview}")
            else:
                item = QListWidgetItem(f"Comments: {preview}")
                
            item.setData(Qt.UserRole, {"type": "comments", "text": text, "header": header})

        else:
            return

        self.module_list.addItem(item)

    def remove_module(self):
        for item in self.module_list.selectedItems():
            self.module_list.takeItem(self.module_list.row(item))

    def get_modules(self):
        modules = []
        for i in range(self.module_list.count()):
            module_data = self.module_list.item(i).data(Qt.UserRole)
            # Add the show_entry_numbers preference to each module
            module_data['show_entry_numbers'] = self.show_entry_numbers.isChecked()
            modules.append(module_data)
        return modules

    def get_image_scale_percent(self):
        try:
            return int(self.image_size_combo.currentText().replace('%', '').strip())
        except (TypeError, ValueError):
            return 70


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    # Initialize the tag manager
    ui.tag_manager = TagManager()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
