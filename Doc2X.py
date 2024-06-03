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
from PyQt6.QtGui import QPixmap, QClipboard, QAction, QGuiApplication
from PyQt6.QtCore import Qt, QCoreApplication, QEvent, QTimer
from Clip import GetClipboard
import imagehash
from PIL import Image

class Ask(QWidget):
    def __init__(self, parent, prevClipboard, ClipTypr):
        super().__init__()
        self.prevClipboard = prevClipboard
        self.ClipTypr = ClipTypr
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Clipboard Converter")
        self.setGeometry(100, 100, 300, 100)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.label = QLabel(f"{self.prevClipboard}", self)

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
            screen_geometry.width() - self.width() - 10,
            screen_geometry.height() - self.height() - 10,
        )

    def convert_to_file(self):
        pass

    def convert_to_text(self):
        self.parent.Convert()

class OCRWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.tr("OCR Tool"))

        # 创建控件
        self.imageLabel = QLabel()
        self.textLabel = QLabel()
        self.openButton = QPushButton(self.tr("Select Image"))
        self.copyButton = QPushButton(self.tr("Copy Text"))

        # 全局信号
        self.prevClipboard = ""  # 用于监听剪切板变化
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

    def openImage(self):
        print("Open Image")
        pass

    def copyText(self):
        print("Copy Text")
        pass

    def setAPIKey(self):
        print("Set API Key")
        pass

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
            self.TimeWait_flag = 0
            self.showNotification()

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()

    def showNotification(self, parent=None):
        self.ask = Ask(self, self.prevClipboard, self.ClipTypr)
        self.ask.show()

    def Convert(self):
        print("Convert")
        pass

    def retranslateUi(self):
        self.setWindowTitle(self.tr("OCR Tool"))
        self.openButton.setText(self.tr("Select Image"))
        self.copyButton.setText(self.tr("Copy Text"))
        self.settingsMenu.setTitle(self.tr("Settings"))
        self.languageMenu.setTitle(self.tr("Language"))
        self.apiKeyAction.setText(self.tr("Set API Key"))
        self.quitAction.setText(self.tr("Quit"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = OCRWidget()
    ex.hide()
    sys.exit(app.exec())