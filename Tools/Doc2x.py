from Tools.Doc2x_API import refresh_key, pic2file, pdf2file
import os


def get_key(key):
    try:
        return refresh_key(key)
    except:
        return None


def file_to_file(file, outputtype, key, path=None):
    if path == None:
        path = os.path.expanduser("~") + "/Downloads"
    try:
        if file.endswith(".pdf"):
            for process, message in pdf2file(
                api_key=key,
                pdf_file=file,
                output_path=path,
                output_format=outputtype,
            ):
                yield process, message

        elif file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            for process, message in pic2file(
                api_key=key,
                image_file=file,
                output_path=path,
                output_format=outputtype,
            ):
                yield process, message
    except Exception as e:
        yield -100, f"Error: {e}"
