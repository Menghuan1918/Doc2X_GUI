import sys
import os
import argparse
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
    QProgressBar,
    QFileDialog,
)
from PyQt6.QtGui import QPixmap, QClipboard, QAction, QGuiApplication, QFont, QIcon
from PyQt6.QtCore import (
    Qt,
    QCoreApplication,
    QEvent,
    QTimer,
    QObject,
    pyqtSignal,
    QRunnable,
    QThreadPool,
    QTranslator,
)
from Clip import GetClipboard, Clear_cache
import imagehash
from PIL import Image
from PyQt6.QtWidgets import QLineEdit, QInputDialog, QMessageBox
from Tools.Config import read_config_file, change_one_config
from Tools.Doc2x import get_key, file_to_file
import logging
import os
import pyperclip
from urllib.parse import unquote


# 信号类
class Doc2X_Single(QObject):
    Get = pyqtSignal(int, str)


class Doc2X(QRunnable):
    def __init__(self, file, outputtype, key, temp_path):
        super().__init__()
        self.parent = Doc2X_Single()
        self.file = file
        self.outputtype = outputtype
        self.key = key
        self.temp_path = temp_path

    def run(self):
        outputtype = self.outputtype
        outputtype = "md_dollar" if outputtype == "text" else outputtype
        for process, text in file_to_file(
            self.file, outputtype, self.key, self.temp_path
        ):
            self.parent.Get.emit(process, text)
            # logging.info(f"Process: {process}, Text: {text}")


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
                screen_geometry.width() - self.width() - 100,
                screen_geometry.height() - self.height() - 400,
            )
        self.autohide = QTimer()
        self.autohide.timeout.connect(self.hide)
        self.autohide.start(5000)

    def save_config(self):
        change_one_config(filename="General_config", key="Ask_x", value=str(self.x()))
        change_one_config(filename="General_config", key="Ask_y", value=str(self.y()))

    def convert_to_file(self):
        self.autohide.stop()
        items = ["docx", "md", "md_dollar", "latex"]
        item, ok = QInputDialog.getItem(
            self,
            self.tr("Output Format"),
            self.tr("Select output format:"),
            items,
            0,
            False,
        )
        if ok and item:
            self.parent.Convert(item)
        self.save_config()
        self.close()

    def convert_to_text(self):
        self.parent.Convert("text")
        self.save_config()
        self.close()

    def closeEvent(self, event):
        self.save_config()
        self.hide()
        event.ignore()


# 主窗口
class OCRWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.General_config = read_config_file("General_config")
        self.setWindowTitle(self.tr("Doc2X GUI"))

        self.setFont(
            QFont(
                self.General_config["font"], int(self.General_config["font_size"]) - 2
            )
        )
        self.setWindowIcon(QIcon("icon.png"))

        # 创建控件
        self.imageLabel = QLabel()
        self.textLabel = QTextEdit()
        self.textLabel.setFont(
            QFont(self.General_config["font"], int(self.General_config["font_size"]))
        )
        self.openButton = QPushButton(self.tr("Select File"))
        self.copyButton = QPushButton(self.tr("Copy Text"))
        self.getfromClip = QPushButton(self.tr("Get picture from Clipboard"))
        self.getHistory = QPushButton(self.tr("OCR History"))
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        # 全局信号
        self.prevClipboard = ""  # 用于监听剪切板变化
        self.FilePath = ""  # 用于存储文件路径
        self.ClipTypr = ""  # 剪切板文件类型状态
        self.TimeWait_flag = 3  # 用于判断是否需要等待
        self.API_Key = ""  # 用于存储API Key
        self.Key_Valid = False  # 用于判断API Key是否有效
        self.Listen = False  # 用于判断是否需要监听剪切板

        try:
            self.Listen = self.General_config["Listen"] == "True"
        except:
            pass

        # 布局
        hbox = QVBoxLayout()
        layout_1 = QHBoxLayout()
        layout_1.addWidget(self.imageLabel)
        layout_1.addWidget(self.textLabel)
        layout_2 = QHBoxLayout()
        layout_2.addWidget(self.progressBar)
        layout_3 = QHBoxLayout()
        layout_3.addWidget(self.openButton)
        layout_3.addWidget(self.copyButton)
        layout_4 = QHBoxLayout()
        layout_4.addWidget(self.getfromClip)
        layout_4.addWidget(self.getHistory)
        hbox.addLayout(layout_1)
        hbox.addLayout(layout_2)
        hbox.addLayout(layout_3)
        hbox.addLayout(layout_4)
        self.setLayout(hbox)

        # 连接信号和槽
        self.openButton.clicked.connect(self.openImage)
        self.copyButton.clicked.connect(self.copyText)
        self.getfromClip.clicked.connect(self.get_fromClip)
        self.getHistory.clicked.connect(self.get_history)

        # 创建系统托盘图标
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("icon.png"))
        self.tray.setVisible(True)
        self.tray.activated.connect(self.onTrayActivated)

        # 检查剪贴板图片
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.GetClipboardImage)
        if self.Listen:
            self.timer.start(2000)
        self.threadpool = QThreadPool()

        # 检查API Key
        self.CheckAPIKey()

        # 创建菜单
        self.creare_menu()

        try:
            self.resize(
                int(self.General_config["width"]), int(self.General_config["height"])
            )
        except:
            pass

    def get_fromClip(self):
        get, self.ClipTypr = GetClipboard(self.prevClipboard)
        if self.ClipTypr == "image":
            self.FilePath = get
            self.Convert("text")
        else:
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("No image found in clipboard"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def get_history(self):
        if os.name == "nt":
            os.system("start https://doc2x.noedgeai.com/")
        else:
            os.system("xdg-open https://doc2x.noedgeai.com/")
        self.hide()
        self.TimeWait_flag = 3

    def creare_menu(self):
        # 创建托盘菜单
        self.menu = QMenu(self)
        self.toggle_action = QAction(self.tr("Toggle Clipboard Listening State"), self)
        self.toggle_action.triggered.connect(self.toggle_monitoring)
        self.menu.addAction(self.toggle_action)

        self.settingsMenu = self.menu.addMenu(self.tr("Settings"))
        self.languageMenu = self.settingsMenu.addMenu(self.tr("Language"))
        self.apiKeyAction = self.settingsMenu.addAction(self.tr("Set API Key"))
        self.quitAction = self.menu.addAction(self.tr("Quit"))
        self.tray.setContextMenu(self.menu)

        # 切换语言：中/EN
        self.zhAction = QAction("简体中文", self)
        self.enAction = QAction("English", self)
        self.languageMenu.addAction(self.zhAction)
        self.languageMenu.addAction(self.enAction)

        # 连接菜单操作
        self.quitAction.triggered.connect(QCoreApplication.quit)
        self.apiKeyAction.triggered.connect(self.setAPIKey)
        self.zhAction.triggered.connect(lambda: self.set_language("zh"))
        self.enAction.triggered.connect(lambda: self.set_language("en"))

    def set_language(self, language):
        self.retranslateUi(language)
        if language == "zh":
            self.zhAction.triggered.disconnect()
        else:
            self.enAction.triggered.disconnect()

    def openImage(self):
        # 仅允许jpg，png和pdf文件
        file_accept = "All accept files (*.jpg *.png *.jpeg *.pdf)"
        file, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open File"), "", file_accept
        )
        if file:
            self.FilePath = file
            items = ["docx", "text", "md", "md_dollar", "latex"]
            item, ok = QInputDialog.getItem(
                self,
                self.tr("Output Format"),
                self.tr("Select output format:"),
                items,
                0,
                False,
            )
            if ok and item:
                self.outputtype = item
                self.Convert(item)

    def copyText(self):
        try:
            pyperclip.copy(self.textLabel.toPlainText())
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("Text copied to clipboard"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self.TimeWait_flag = 3
            self.Block()
            Clear_cache()
            self.hide()
        except Exception as e:
            logging.error(e)
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("Copy failed, please copy by yourself."),
                QSystemTrayIcon.MessageIcon.Critical,
                6000,
            )

    def setAPIKey(self):
        try:
            api, ok = QInputDialog.getText(
                self,
                self.tr("Set API Key"),
                self.tr("API Key:"),
                text=self.General_config["API_Key"],
            )
        except:
            api, ok = QInputDialog.getText(
                self, self.tr("Set API Key"), self.tr("API Key:")
            )
        if ok:
            change_one_config(filename="General_config", key="API_Key", value=api)
            self.General_config = read_config_file("General_config")
            self.CheckAPIKey()

    def CheckAPIKey(self):
        try:
            self.API_Key = get_key(self.General_config["API_Key"])
            if self.API_Key == None:
                raise Exception
            self.Key_Valid = True
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("API key validation successful"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self.TimeWait_flag = 3
        except:
            self.API_Key = None
            self.TimeWait_flag = -100
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(
                    """The API key acquisition exception may be caused by the key not being set or expired. Please right-click the taskbar icon and select 'Set API Key'.
                    Please go to the website and select 'personal information' -> 'identity token' to copy it. The website URL has been copied to your clipboard."""
                ),
            )
            pyperclip.copy("https://doc2x.noedgeai.com/")

    def GetClipboardImage(self):
        if self.TimeWait_flag < -10:
            return
        elif self.TimeWait_flag != 3:
            self.TimeWait_flag += 1
            return

        get, self.ClipTypr = GetClipboard(self.prevClipboard)
        # print(f"Get: {get}, Type: {self.ClipTypr}")
        if self.ClipTypr == "image":
            try:
                hashcheck = imagehash.phash(Image.open(get))
                self.prevClipboard = hashcheck
            except:
                get = unquote(get)
                try:
                    hashcheck = imagehash.phash(Image.open(get))
                    self.prevClipboard = hashcheck
                except Exception as e:
                    logging.error(e)
        elif self.ClipTypr != "same":
            self.prevClipboard = get

        if self.ClipTypr != "same" and self.ClipTypr != "text":
            self.FilePath = get
            self.TimeWait_flag = 0
            self.showNotification()

    def toggle_monitoring(self):
        self.Listen = not self.Listen
        change_one_config(
            filename="General_config", key="Listen", value=str(self.Listen)
        )
        if self.Listen:
            self.timer.start(2000)
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("Clipboard monitoring turned on"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        else:
            self.timer.stop()
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr("Clipboard monitoring turned off"),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def update_meau(self):
        self.toggle_action.setText(
            self.tr("Turn on clipboard monitoring")
            if not self.Listen
            else self.tr("Turn off clipboard monitoring")
        )

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()
            self.TimeWait_flag = -100

    def showNotification(self):
        self.ask = Ask(self, self.FilePath, self.ClipTypr, self.General_config)
        self.ask.show()

    def set_flag(self):
        # 等待超时恢复
        self.TimeWait_flag = 3
        self.Block()

    def Convert(self, outputtype):
        # 设置等待标志以及响应超时设置
        self.TimeWait_flag = -100
        self.Flag_Time_out = QTimer()
        self.Flag_Time_out.timeout.connect(self.set_flag)
        self.Flag_Time_out.start(45000)

        self.outputtype = str(outputtype)
        self.show()
        if self.FilePath.endswith(".pdf"):
            pixmap = QPixmap("pdf.png")
        else:
            pixmap = QPixmap(self.FilePath)
        pixmap = pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.setMaximumSize(600, 400)
        self.textLabel.setText(self.tr("Converting...Please wait."))
        self.textLabel.setFixedSize(500, 400)
        self.Block()
        if self.outputtype == "text":
            temp_path = os.path.expanduser("~") + "/.cache/Doc2X_GUI"
        else:
            temp_path = os.path.expanduser("~") + "/Downloads/Doc2X_GUI"
        os.makedirs(temp_path, exist_ok=True)
        Doc2X_Process = Doc2X(self.FilePath, self.outputtype, self.API_Key, temp_path)
        Doc2X_Process.parent.Get.connect(self.Update_process)
        self.threadpool.start(Doc2X_Process)

    def Update_process(self, pocess, text):
        if text != "":
            self.textLabel.setText(text)
        if pocess >= 0 and pocess <= 100:
            self.progressBar.setValue(pocess)
        elif pocess > 100:
            if self.outputtype == "text":
                try:
                    path = f"{text}/{os.path.basename(text)}.md"
                    with open(path, "r") as f:
                        get_text = f.read()
                    get_text = str(get_text)
                    self.textLabel.setText(get_text)
                    self.TimeWait_flag = -20  # 解锁按钮但是不恢复监听
                    self.Block()
                    Clear_cache()
                except Exception as e:
                    self.textLabel.setText(str(e))
            else:
                self.textLabel.setText(self.tr("Conversion completed."))
                try:
                    if os.name == "nt":
                        os.system(f"start {text}")
                    else:
                        os.system(f"xdg-open {text}")
                    self.TimeWait_flag = 3
                    Clear_cache()
                    self.Block()
                    self.hide()
                except Exception as e:
                    logging.error(e)
        else:
            self.textLabel.setText(f"Error: {text}")

    def Block(self):
        # 在等待标志为处理中时锁定所有按钮(设置为-50是因为有处理完当前图片后的等待复制的空间)
        if self.TimeWait_flag < -50:
            self.openButton.setEnabled(False)
            self.copyButton.setEnabled(False)
            self.textLabel.setEnabled(False)
        else:
            self.openButton.setEnabled(True)
            self.copyButton.setEnabled(True)
            self.textLabel.setEnabled(True)

    def retranslateUi(self, lau):
        try:
            translater = QTranslator()
            translater.load(f"Doc2X_{lau}.qm")
            app.installTranslator(translater)
            change_one_config(filename="General_config", key="lang", value=lau)
            self.tray.showMessage(
                self.tr("Doc2X GUI"),
                self.tr(
                    "Language changed successfully, please restart the program.\n语言切换成功，请重启程序。"
                ),
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        except:
            logging.error(f"Failed to load {lau} language file.")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.TimeWait_flag = 3
        self.Block()
        Clear_cache()
        change_one_config(
            filename="General_config", key="width", value=str(self.width())
        )
        change_one_config(
            filename="General_config", key="height", value=str(self.height())
        )
        self.tray.showMessage(
            self.tr("Doc2X GUI"),
            self.tr("The program will keep running in the system tray."),
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.hide()
                self.TimeWait_flag = 3
                self.Block()
                Clear_cache()
                self.tray.showMessage(
                    self.tr("Doc2X GUI"),
                    self.tr("The program will keep running in the system tray."),
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )
        super().changeEvent(event)


if __name__ == "__main__":
    logfile = os.path.expanduser("~") + "/.config/DOC2X_GUI/Doc2X_GUI.log"
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    # 除非设置标示，否则在Wayland环境中使用XWayland
    parser = argparse.ArgumentParser()
    parser.add_argument("-wayland", help="Run on Wayland")
    args = parser.parse_args()
    if os.environ.get("WAYLAND_DISPLAY") is not None and not args.wayland:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    config = read_config_file("General_config")
    app = QApplication(sys.argv)
    try:
        translater = QTranslator()
        translater.load(f"Doc2X_{config['lang']}.qm")
        app.installTranslator(translater)
    except:
        logging.error(f"Failed to load {config['lang']} language file.")

    ex = OCRWidget()
    ex.hide()
    sys.exit(app.exec())
