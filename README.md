# Doc2X_GUI
第三方Doc2X桌面应用
使用nuitka进行打包
```python
python -m nuitka --standalone --include-data-file=icon.png=./icon.png --include-data-file=pdf.png=./pdf.png --plugin-enable=pyqt6 Doc2X.py
```