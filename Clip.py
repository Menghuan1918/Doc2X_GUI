import pyperclip
from PIL import ImageGrab
import os
import time
import logging
import imagehash
from PIL import Image
from urllib.parse import unquote


def same_image(image_path, phash):
    try:
        hash = imagehash.phash(Image.open(image_path))
        try:
            return hash == phash
        except:
            return False
    except:
        try:
            image_path = unquote(image_path)
            hash = imagehash.phash(Image.open(image_path))
            return hash == phash
        except:
            return False


def get_file_path():
    filename = f"clipboard_{time.strftime('%Y%m%d%H%M%S')}.png"
    image_path = os.path.expanduser(f"~/.cache/Doc2X_GUI/{filename}")
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    return image_path


def Windows_pic(pretext):
    text = "None"
    Clip_type = "text"
    try:
        image = ImageGrab.grabclipboard()
        if image is not None:
            image_path = get_file_path()
            image.save(image_path)
            if same_image(image_path, pretext):
                Clip_type = "same"
                os.remove(image_path)
            else:
                Clip_type = "image"
                text = image_path
        else:
            text = pyperclip.paste()
    except:
        text = pyperclip.paste()

    return text, Clip_type


def Linux_pic(pretext):
    text = "None"
    Clip_type = "text"

    # Wayland
    if os.environ.get("WAYLAND_DISPLAY") is not None:
        try:
            text = pyperclip.paste()
        except:
            image_path = get_file_path()
            os.system(f"wl-paste > {image_path}")
            if same_image(image_path, pretext):
                Clip_type = "same"
                os.remove(image_path)
            else:
                logging.info(f"Clipboard image saved to {image_path}")
                Clip_type = "image"
                text = image_path
    # X11
    else:
        try:
            image = ImageGrab.grabclipboard()
            if image is not None:
                image_path = get_file_path()
                image.save(image_path)
                if same_image(image_path, pretext):
                    Clip_type = "same"
                    os.remove(image_path)
                else:
                    Clip_type = "image"
                    text = image_path
            else:
                text = pyperclip.paste()
        except:
            text = pyperclip.paste()

    try:
        # 去除可能的多余\r\n
        if text.endswith("\r\n"):
            text = text[:-2]
        # 检测是否为pdf文件
        if text.startswith("file:///") and text.endswith(".pdf"):
            Clip_type = "pdf"
            text = text[7:]

        # 检测是否为图片文件
        if text.startswith("file:///") and text.endswith((".png", ".jpg", ".jpeg")):
            Clip_type = "image"
            text = text[7:]
            if same_image(text, pretext):
                Clip_type = "same"

        if pretext == text:
            return text, "same"
    except:
        pass

    return text, Clip_type


def GetClipboard(pretext):
    if os.name == "nt":
        return Windows_pic(pretext)
    else:
        return Linux_pic(pretext)


def Clear_cache():
    place = os.path.expanduser("~") + "/.cache/Doc2X_GUI"
    for root, dirs, files in os.walk(place):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except:
                logging.error(f"Failed to remove {os.path.join(root, name)}")
                pass


if __name__ == "__main__":
    import time

    pre = ""
    while True:
        get, type = GetClipboard(pre)
        print(f"tpye: {type} --> {get}")
        if type == "image":
            try:
                pre = imagehash.phash(Image.open(get))
            except:
                try:
                    pre = imagehash.phash(Image.open(unquote(get)))
                except Exception as e:
                    print(e)
                    
        elif type != "same":
            pre = get
        time.sleep(2)
