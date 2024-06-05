import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import QPixmap, QClipboard, QAction, QGuiApplication, QFont
from PyQt6.QtCore import Qt, QCoreApplication, QEvent, QTimer
from Clip import GetClipboard
import imagehash
from PIL import Image
from PyQt6.QtWidgets import QLineEdit, QInputDialog, QMessageBox
from Tools.Config import read_config_file, change_one_config


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
        self.setFont(QFont(config["font"], int(config["font_size"])))

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
        self.move(
            screen_geometry.width() - self.width() - 50,
            screen_geometry.height() - self.height() - 400,
        )
        self.autohide = QTimer()
        self.autohide.timeout.connect(self.hide)
        self.autohide.start(5000)

    def convert_to_file(self):
        pass

    def convert_to_text(self):
        self.parent.Convert()
        self.close()

    def closeEvent(self, event):
        self.hide()
        event.ignore()



class OCRWidget(QWidget):
    def __init__(self, General_config):
        super().__init__()
        self.initUI(General_config)

    def initUI(self, General_config):
        self.setWindowTitle(self.tr("Doc2X GUI"))

        # 创建控件
        self.imageLabel = QLabel()
        self.textLabel = QLabel()
        self.openButton = QPushButton(self.tr("Select Image"))
        self.copyButton = QPushButton(self.tr("Copy Text"))

        # 全局信号
        self.prevClipboard = ""  # 用于监听剪切板变化
        self.FilePath = ""  # 用于存储文件路径
        self.ClipTypr = ""  # 剪切板文件类型状态
        self.TimeWait_flag = 3  # 用于判断是否需要等待

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
        api, ok = QInputDialog.getText(
            self, self.tr("Set API Key"), self.tr("API Key:")
        )
        if ok:
            # Just for testings
            QMessageBox.information(self, "API Key", f"API Key set to: {api}")

    def GetClipboardImage(self):
        if self.TimeWait_flag < -10:
            return
        elif self.TimeWait_flag != 3:
            self.TimeWait_flag += 1
            return

        get, self.ClipTypr = GetClipboard(self.prevClipboard)
        if self.ClipTypr == "image":
            self.prevClipboard = imagehash.phash(Image.open(get))
            self.FilePath = get
        elif self.ClipTypr != "same":
            self.prevClipboard = get

        if self.ClipTypr != "same" and self.ClipTypr != "text":
            self.TimeWait_flag = 0
            self.showNotification()

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()

    def showNotification(self):
        self.ask = Ask(self, self.FilePath, self.ClipTypr, config)
        self.ask.show()

    def set_flag(self):
        self.TimeWait_flag = 3

    def Convert(self):
        # 设置等待标志以及响应超时设置
        self.TimeWait_flag = -100
        self.Flag_Time_out = QTimer()
        self.Flag_Time_out.timeout.connect(self.set_flag)
        self.Flag_Time_out.start(30000)

        self.show()
        pixmap = QPixmap(self.FilePath)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setMaximumSize(800, 500)
        self.textLabel.setText("Text")

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
