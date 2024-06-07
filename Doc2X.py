import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QTextEdit,
)
from PyQt6.QtGui import QPixmap, QClipboard, QAction, QGuiApplication, QFont, QIcon
from PyQt6.QtCore import Qt, QCoreApplication, QEvent, QTimer, QObject, pyqtSignal,QRunnable,QThreadPool
from Clip import GetClipboard
import imagehash
from PIL import Image
from PyQt6.QtWidgets import QLineEdit, QInputDialog, QMessageBox
from Tools.Config import read_config_file, change_one_config
from Tools.Doc2x import get_key, file_to_file

# 信号类
class Doc2X_Single(QObject):
    Get = pyqtSignal(int, str)

class Doc2X(QRunnable):
    def __init__(self, file, outputtype, key):
        super().__init__()
        self.parent = Doc2X_Single()
        self.file = file
        self.outputtype = outputtype
        self.key = key

    def run(self):
        self.parent.Get.emit(1, file_to_file(self.file, self.outputtype, self.key))

# 询问窗口
class Ask(QWidget):
    def __init__(self, parent, FilePath, ClipTypr, config):
        super().__init__()
        self.FilePath = FilePath
        self.ClipTypr = ClipTypr
        self.parent = parent
        self.initUI(config)

    def initUI(self, config):
        self.setWindowTitle(self.tr("File from Clipboard detected"))
        self.setGeometry(100, 100, 300, 100)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setFont(QFont(config["font"], int(config["font_size"]) - 2))

        self.label = QLabel(f"{self.FilePath}", self)

        self.fileButton = QPushButton(self.tr("Convert to File"), self)
        self.textButton = QPushButton(self.tr("Convert to Text"), self)

        self.fileButton.clicked.connect(self.convert_to_file)
        self.textButton.clicked.connect(self.convert_to_text)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.fileButton)
        layout.addWidget(self.textButton)

        self.setLayout(layout)

        screen_geometry = QApplication.primaryScreen().geometry()
        try:
            self.move(config["Ask_x"], config["Ask_y"])
        except:
            self.move(
                screen_geometry.width() - self.width() - 50,
                screen_geometry.height() - self.height() - 400,
            )
        self.autohide = QTimer()
        self.autohide.timeout.connect(self.hide)
        self.autohide.start(5000)

    def save_config(self):
        change_one_config(filename="General_config", key="Ask_x", value=str(self.x()))
        change_one_config(filename="General_config", key="Ask_y", value=str(self.y()))

    def convert_to_file(self):
        pass

    def convert_to_text(self):
        self.parent.Convert()
        self.save_config()
        self.close()

    def closeEvent(self, event):
        self.save_config()
        self.hide()
        event.ignore()

# 主窗口
class OCRWidget(QWidget):
    def __init__(self, General_config):
        super().__init__()
        self.initUI(General_config)

    def initUI(self, General_config):
        self.setWindowTitle(self.tr("Doc2X GUI"))

        self.setFont(
            QFont(General_config["font"], int(General_config["font_size"]) - 2)
        )
        self.setWindowIcon(QIcon("icon.png"))
        # 创建控件
        self.imageLabel = QLabel()
        self.textLabel = QTextEdit()
        self.textLabel.setFont(
            QFont(General_config["font"], int(General_config["font_size"]))
        )
        self.openButton = QPushButton(self.tr("Select Image"))
        self.copyButton = QPushButton(self.tr("Copy Text"))

        # 全局信号
        self.prevClipboard = ""  # 用于监听剪切板变化
        self.FilePath = ""  # 用于存储文件路径
        self.ClipTypr = ""  # 剪切板文件类型状态
        self.TimeWait_flag = 3  # 用于判断是否需要等待
        self.API_Key = ""  # 用于存储API Key
        self.Key_Valid = False  # 用于判断API Key是否有效
        self.Listen = True  # 用于判断是否需要监听剪切板

        # 布局
        hbox = QHBoxLayout()
        imageVBox = QVBoxLayout()
        imageVBox.addWidget(self.imageLabel)
        imageVBox.addWidget(self.openButton)
        textVBox = QVBoxLayout()
        textVBox.addWidget(self.textLabel)
        textVBox.addWidget(self.copyButton)
        hbox.addLayout(imageVBox)
        hbox.addLayout(textVBox)
        self.setLayout(hbox)

        # 连接信号和槽
        self.openButton.clicked.connect(self.openImage)
        self.copyButton.clicked.connect(self.copyText)

        # 创建系统托盘图标
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("icon.png"))
        self.tray.setVisible(True)
        self.tray.activated.connect(self.onTrayActivated)

        # 创建托盘菜单
        menu = QMenu(self)
        self.settingsMenu = menu.addMenu(self.tr("Settings"))
        self.languageMenu = self.settingsMenu.addMenu(self.tr("Language"))
        self.apiKeyAction = self.settingsMenu.addAction(self.tr("Set API Key"))
        self.quitAction = menu.addAction(self.tr("Quit"))
        self.tray.setContextMenu(menu)

        # 连接菜单操作
        self.quitAction.triggered.connect(QCoreApplication.quit)
        self.apiKeyAction.triggered.connect(self.setAPIKey)

        # 检查剪贴板图片
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.GetClipboardImage)
        self.timer.start(2000)
        self.threadpool = QThreadPool()

        # 检查API Key
        self.CheckAPIKey()

        try:
            self.resize(int(General_config["width"]), int(General_config["height"]))
        except:
            pass

    def openImage(self):
        print("Open Image")
        pass

    def copyText(self):
        self.set_flag()
        print("Copy Text")
        pass

    def setAPIKey(self):
        try:
            api, ok = QInputDialog.getText(
                self,
                self.tr("Set API Key"),
                self.tr("API Key:"),
                text=config["API_Key"],
            )
        except:
            api, ok = QInputDialog.getText(
                self, self.tr("Set API Key"), self.tr("API Key:")
            )
        if ok:
            change_one_config(filename="General_config", key="API_Key", value=api)
            self.CheckAPIKey()

    def CheckAPIKey(self):
        try:
            self.API_Key = get_key(config["API_Key"])
            if self.API_Key == None:
                raise Exception
            self.Key_Valid = True
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("API key validation successful"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        except:
            self.API_Key = None
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(
                    "The API key acquisition exception may be caused by the key not being set or expired. Please right-click the taskbar icon and select 'Set API Key'."
                ),
            )

    def GetClipboardImage(self):
        if self.TimeWait_flag < -10:
            return
        elif self.TimeWait_flag != 3:
            self.TimeWait_flag += 1
            return

        get, self.ClipTypr = GetClipboard(self.prevClipboard)
        if self.ClipTypr == "image":
            self.prevClipboard = imagehash.phash(Image.open(get))
        elif self.ClipTypr != "same":
            self.prevClipboard = get

        if self.ClipTypr != "same" and self.ClipTypr != "text":
            self.FilePath = get
            self.TimeWait_flag = 0
            self.showNotification()

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()
            self.TimeWait_flag = -100

    def showNotification(self):
        self.ask = Ask(self, self.FilePath, self.ClipTypr, config)
        self.ask.show()

    def set_flag(self):
        # 等待超时恢复
        self.TimeWait_flag = 3
        self.Block()

    def Convert(self):
        # 设置等待标志以及响应超时设置
        self.TimeWait_flag = -100
        self.Flag_Time_out = QTimer()
        self.Flag_Time_out.timeout.connect(self.set_flag)
        self.Flag_Time_out.start(45000)

        self.show()
        pixmap = QPixmap(self.FilePath)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setMaximumSize(600, 400)
        self.textLabel.setText(self.tr("Converting...Please wait."))
        self.textLabel.setFixedSize(500, 400)
        self.Block()
        Doc2X_Process = Doc2X(self.FilePath, "text", self.API_Key)
        Doc2X_Process.parent.Get.connect(self.Update_process)
        self.threadpool.start(Doc2X_Process)

    #! 由于进度传递还没有实现，所以暂时不使用
    def Update_process(self, pocess, text):
        self.textLabel.setText(text)
        self.TimeWait_flag = 3
        self.Block()

    def Block(self):
        # 在等待标志为处理中时锁定所有按钮
        if self.TimeWait_flag < -10:
            self.openButton.setEnabled(False)
            self.copyButton.setEnabled(False)
            self.textLabel.setEnabled(False)
        else:
            self.openButton.setEnabled(True)
            self.copyButton.setEnabled(True)
            self.textLabel.setEnabled(True)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("OCR Tool"))
        self.openButton.setText(self.tr("Select Image"))
        self.copyButton.setText(self.tr("Copy Text"))
        self.settingsMenu.setTitle(self.tr("Settings"))
        self.languageMenu.setTitle(self.tr("Language"))
        self.apiKeyAction.setText(self.tr("Set API Key"))
        self.quitAction.setText(self.tr("Quit"))

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.TimeWait_flag = 3
        self.tray.showMessage(
            self.tr("Doc2X GUI"),
            self.tr("The program will keep running in the system tray."),
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.hide()
                self.TimeWait_flag = 3
                self.tray.showMessage(
                    self.tr("Doc2X GUI"),
                    self.tr("The program will keep running in the system tray."),
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )
        super().changeEvent(event)


if __name__ == "__main__":
    config = read_config_file("General_config")
    app = QApplication(sys.argv)
    ex = OCRWidget(config)
    ex.hide()
    sys.exit(app.exec())
