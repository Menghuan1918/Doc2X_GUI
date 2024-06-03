import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt


# 询问是否处理文件
class Ask(QWidget):
    def __init__(self, prevClipboard, ClipTypr):
        super().__init__()
        self.prevClipboard = prevClipboard
        self.ClipTypr = ClipTypr
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Clipboard Converter")
        self.setGeometry(100, 100, 300, 100)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.label = QLabel(f"{self.prevClipboard}", self)

        self.fileButton = QPushButton("转换为文件", self)
        self.textButton = QPushButton("转换为文本", self)

        self.fileButton.clicked.connect(self.convert_to_file)
        self.textButton.clicked.connect(self.convert_to_text)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.fileButton)
        layout.addWidget(self.textButton)

        self.setLayout(layout)

        # 设置窗口位置在右下角
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(
            screen_geometry.width() - self.width() - 10,
            screen_geometry.height() - self.height() - 10,
        )

    def convert_to_file(self):
        QMessageBox.information(self, "转换为文件", "路径已转换为文件")

    def convert_to_text(self):
        QMessageBox.information(self, "转换为文本", "路径已转换为文本")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Ask("C:/Users/username/Desktop/1.jpg", "image")
    ex.show()
    sys.exit(app.exec())
