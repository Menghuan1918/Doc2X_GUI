<br>

<div align=center>
<h1 aligh="center">
<img src="icon.png" width="100"> 

Doc2X GUI
</h1>

[![License][License-image]][License-url]
[![Releases][Releases-image]][Releases-url]
[![Commit][GitHub-last-commit]][Commit-url]
[![PR][PRs-image]][PRs-url]

[License-image]: https://img.shields.io/github/license/Menghuan1918/Doc2X_GUI
[Releases-image]: https://img.shields.io/github/v/release/Menghuan1918/Doc2X_GUI
[GitHub-last-commit]: https://img.shields.io/github/last-commit/Menghuan1918/Doc2X_GUI
[PRs-image]: https://img.shields.io/badge/PRs-welcome-pink?style=flat-square

[License-url]: https://github.com/Menghuan1918/Doc2X_GUI/blob/main/LICENSE
[Releases-url]: https://github.com/Menghuan1918/Doc2X_GUI/releases
[Commit-url]: https://github.com/Menghuan1918/Doc2X_GUI/commits/master/
[PRs-url]: https://github.com/Menghuan1918/Doc2X_GUI/pulls

</div>
<br>

第三方Doc2X桌面应用，支持Linux(Wayland,X11)以及Windows。

- 支持监听剪切板中的图片或PDF文件(Windows不支持监听文件)。
- 支持监听Wayland剪切板图片
- 支持从剪切板复制图片解析

> [!NOTE]
> 如你不需要监听剪切板/从剪切板粘贴图片的功能，你可以在AUR上使用@asukaminato0721的[Dox2X官方Windows的移植版](https://aur.archlinux.org/packages/doc2x)

> [!IMPORTANT]
> 为了监听剪切板，Linux用户需要安装`xclip`
> 
> 如果你使用的Wayland，还需要安装`wl-clipboard`
>
> Ubuntu/Debian:`sudo apt install xclip wl-clipboard`
>
> Arch/Manjaro:`sudo pacman -S xclip wl-clipboard`

[linux.webm](https://github.com/Menghuan1918/Doc2X_GUI/assets/122662527/64360ec5-f5e6-4b98-8719-6dffe314583c)

[windows.webm](https://github.com/Menghuan1918/Doc2X_GUI/assets/122662527/c28aedb9-5eb0-47ed-9f0b-c994082072d7)

![图片](https://github.com/Menghuan1918/Doc2X_GUI/assets/122662527/47596a8f-b363-4038-ac98-ec8b06e62c6a)


# 下载
你可以从[Release](https://github.com/Menghuan1918/Doc2X_GUI/releases)下载对应系统的安装包。

对于Arch用户，你可以从[AUR](https://aur.archlinux.org/packages/doc2xgui-git)下载：
```bash
paru -S doc2xgui-git
#yay -S doc2xgui-git
```

或者你也可以从源码运行：
```bash
conda create -n doc2x python=3.12
conda activate doc2x
git clone https://github.com/Menghuan1918/Doc2X_GUI
cd Doc2X_GUI
pip install -r requirements.txt
python Doc2X.py
```

> [!IMPORTANT]
> 为了保证部分功能的正常工作，默认情况下程序会在XWayland下运行。如希望在Wayland下运行，请添加运行参数`-wayland 1`

## Release构建方法
Windows安装包与Deb包均是封装的nuitka打包的二进制文件(偷懒)

Windows打包指令：
```python
python -m nuitka --standalone --include-data-file=icon.png=./icon.png --include-data-file=pdf.png=./pdf.png --include-data-file=Doc2X_zh.qm=./Doc2X_zh.qm --plugin-enable=pyqt6 Doc2X.py
```

Linux打包指令：
```python
python -m nuitka --standalone --include-data-file=icon.png=./icon.png --include-data-file=pdf.png=./pdf.png --plugin-enable=pyqt6 --include-data-file=Doc2X_zh.qm=./Doc2X_zh.qm --onefile --mingw64 --windows-console-mode=disable --windows-icon-from-ico=./icon.png Doc2X.py
```

# To DO
- [ ] 接入未来的RAG API，与其他LLM集成
- [ ] 支持批量操作
