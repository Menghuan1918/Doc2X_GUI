# 来源于pdfdeal库，对其进行了部分修改以适配GUI界面需求
# https://github.com/Menghuan1918/pdfdeal
import requests
import json
import os
import zipfile
import time
import logging
import re

Base_URL = "https://api.doc2x.noedgeai.com/api"


def refresh_key(personal_key):
    """
    Get a new key by refreshing the old key
    """
    url = Base_URL + "/token/refresh"
    get_res = requests.post(url, headers={"Authorization": "Bearer " + personal_key})
    if get_res.status_code == 200:
        return json.loads(get_res.content.decode("utf-8"))["data"]["token"]
    else:
        raise RuntimeError(
            f"Refresh key failed, status code: {get_res.status_code}:{get_res.text}"
        )


def async_pdf2file(api_key, pdf_file, ocr=True):
    """
    `api_key`: personal key, get from function
    `pdf_file`: pdf file path
    `ocr`: whether to use OCR, default is True
    return: uuid of the file
    """
    url = Base_URL + "/platform/async/pdf"
    ocr = "1" if ocr else "0"
    get_res = requests.post(
        url,
        headers={"Authorization": "Bearer " + api_key},
        files={"file": open(pdf_file, "rb")},
        data={"ocr": ocr},
        stream=True,
    )
    if get_res.status_code == 200:
        return json.loads(get_res.content.decode("utf-8"))["data"]["uuid"]
    else:
        if get_res.status_code == 429:
            print("Too many requests, wait for 20s and try again")
            time.sleep(10)
            print("10s left")
            time.sleep(10)
            temp = async_pdf2file(api_key, pdf_file, ocr)
            return temp
        raise RuntimeError(
            f"Async_pdf2file failed, status code: {get_res.status_code}:{get_res.text}"
        )


def async_pic2file(api_key, image_file, option=False):
    """
    `api_key`: personal key, get from function
    `image_file`: image file path
    `option`: only output equation, default is False
    return: uuid of the file
    """
    url = Base_URL + "/platform/async/img"
    option = "true" if option else "false"
    get_res = requests.post(
        url,
        headers={"Authorization": "Bearer " + api_key},
        files={"file": open(image_file, "rb")},
        data={"option": option},
        stream=True,
    )
    if get_res.status_code == 200:
        return json.loads(get_res.content.decode("utf-8"))["data"]["uuid"]
    else:
        if get_res.status_code == 429:
            logging.warning("Too many requests, wait for 20s and try again")
            time.sleep(20)
            temp = async_pic2file(api_key, image_file, option)
            return temp
        raise RuntimeError(
            f"Async_pic2file failed, status code: {get_res.status_code}:{get_res.text}"
        )


def un_zip(zip_path):
    """
    Unzip the file
    """
    folder_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_path = os.path.join(os.path.dirname(zip_path), folder_name)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        os.remove(zip_path)
        return extract_path
    except Exception as e:
        raise RuntimeError(f"Unzip failed: {e}")


def uuid2file(api_key, uuid, output_format, output_path=None):
    """
    `api_key`: personal key, get from function 'refresh_key'
    `uuid`: uuid of the file
    `output_path`: output file path, default is None, which means same directory as the input file
    `output_format`: Accept "md", "md_dollar", "latex", "docx", which will save to output_path
    """
    url = Base_URL + f"/export?request_id={uuid}&to={output_format}"
    output_format = output_format if output_format in ["docx", "latex"] else "zip"
    get_res = requests.get(url, headers={"Authorization": "Bearer " + api_key})
    if get_res.status_code == 200:
        if output_path is None:
            path = os.getcwd()
            output_path = os.path.join(path, "doc2xoutput", f"{uuid}.{output_format}")
        else:
            if not output_path.endswith(output_format):
                output_path = os.path.join(output_path, f"{uuid}.{output_format}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(get_res.content)
        if output_format == "zip":
            output_path = un_zip(output_path)
        yield 500, output_path
    else:
        if get_res.status_code == 429:
            logging.warning("Too many requests, wait for 20s and try again")
            time.sleep(20)
            for process, message in uuid2file(api_key, uuid, output_format, output_path):
                yield process, message
        raise RuntimeError(
            f"Uuid2file failed, status code: {get_res.status_code}:{get_res.text}"
        )


def async_uuid2file(api_key, uuid, convert=False):
    """
    `api_key`: personal key, get from function 'refresh_key'
    `uuid`: uuid of the file
    `convert`: whether to convert "[" to "$" and "[[" to "$$", default is False

    output will return a list of text content in pages
    """
    url = Base_URL + "/platform/async/status?uuid=" + uuid
    get_res = requests.get(url, headers={"Authorization": "Bearer " + api_key})
    if get_res.status_code == 200:
        datas = json.loads(get_res.content.decode("utf-8"))["data"]
        if datas["status"] == "ready":
            yield 0, ""
            time.sleep(3)
            for a, b in async_uuid2file(api_key, uuid):
                yield a, b
        elif datas["status"] == "processing":
            yield int(datas["progress"]), ""
            time.sleep(3)
            for a, b in async_uuid2file(api_key, uuid):
                yield a, b
        elif datas["status"] == "success":
            yield 100, ""
        elif datas["status"] == "pages limit exceeded":
            raise RuntimeError(f"You have exceeded the page limit!")
        else:
            raise RuntimeError(f"Get error: {datas}")
    else:
        raise RuntimeError(
            f"Async_uuid2file failed, status code: {get_res.status_code}:{get_res.text}"
        )


def pic2file(
    api_key,
    image_file,
    output_path=None,
    output_format="text",
    img_correction=True,
    equation=False,
):
    """
    `api_key`: personal key, get from function 'refresh_key'
    `image_file`: image file path
    `output_path`: output file path, default is None, which means same directory as the input file
    `output_format`: output format, default is 'text', which will return the text content.
    Also accept "md", "md_dollar", "latex", "docx", which will save to output_path
    `img_correction`: whether to correct the image, default is True
    `equation`: whether only output equation, default is False

    yeild : Process status, if success, return the output file path
    """
    uuid = async_pic2file(api_key, image_file, equation)
    for process, message in async_uuid2file(api_key, uuid):
        yield process, message
        if process == 100:
            for process, message in uuid2file(
                api_key, uuid, output_format, output_path
            ):
                yield process, message


def pdf2file(api_key, pdf_file, output_path=None, output_format="text", ocr=True):
    """
    `api_key`: personal key, get from function 'refresh_key'
    `pdf_file`: pdf file path
    `output_path`: output file path, default is None, which means same directory as the input file
    `output_format`: output format, default is 'text', which will return the text content.
    Also accept "md", "md_dollar", "latex", "docx", which will save to output_path
    `ocr`: whether to use OCR, default is True

    yeild : Process status, if success, return the output file path
    """
    uuid = async_pdf2file(api_key, pdf_file, ocr)
    yield 0, "Uploading file done, waiting for processing...\n文件上传完成，等待处理中..."
    for process, message in async_uuid2file(api_key, uuid):
        yield process, message
        if process == 100:
            for process, message in uuid2file(
                api_key, uuid, output_format, output_path
            ):
                yield process, message
