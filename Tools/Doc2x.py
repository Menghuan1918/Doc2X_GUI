from pdfdeal.doc2x import refresh_key, pdf2file,pic2file
import os


def get_key(key):
    try:
        return refresh_key(key)
    except:
        return None


def file_to_file(file, outputtype, key):
    try:
        if file.endswith(".pdf"):
            return pdf2file(
                api_key=key,
                file=file,
                output_path=os.path.expanduser("~") + "/Downloads",
                output_format=outputtype,
            )

        elif file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            return pic2file(
                api_key=key,
                image_file=file,
                output_path=os.path.expanduser("~") + "/Downloads",
                output_format=outputtype,
            )
    except Exception as e:
        return f"Error: {e}"