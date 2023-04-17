import logging
import random
import shutil
import time
from pathlib import Path

import requests

from pyutils.shortcuts import random_user_agent


def chunk_download_url(url: str, output_dir: str, first_chunk: int = 1) -> str:
    if "{}" not in url:
        raise ValueError("URL must contain '{}' placeholder for chunk number.")

    tmp_file = Path(output_dir) / "download.tmp"
    file_extension = None
    headers = {
        "Accept": "*/*",
        "User-Agent": random_user_agent(),
        "Accept-Language": "gl-ES,gl;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "Origin": "https://tmdbcdn.lat",
        "Connection": "keep-alive",
        "Referer": "https://tmdbcdn.lat/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    with open(tmp_file, "ab") as outfile:
        i = first_chunk
        while True:
            headers["User-Agent"] = random_user_agent()
            response = requests.get(url.format(i), headers=headers, stream=True)
            if response.status_code != 200:
                break

            response_size = 0
            for chunk in response.iter_content(chunk_size=None):
                if i == 1 and file_extension is None:
                    file_extension = _detect_file_extension(chunk[:16])
                    logging.info(f"detected file format: {file_extension}")

                outfile.write(chunk)
                response_size += len(chunk)

            logging.info(f"fragment {i} downloaded ({response_size} bytes) and appended")
            i += 1

            if i % 10 == 0:
                time.sleep(random.randint(1, 5))

    file_path = Path(output_dir) / f"downloaded_video{file_extension}"
    shutil.move(tmp_file, file_path)
    return str(file_path)


def _detect_file_extension(data):
    signatures = {
        b"\x00\x00\x00\x18ftyp": ".mp4",
        b"\x1a\x45\xdf\xa3": ".mkv",
        b"\x46\x4c\x56\x01": ".flv",
        b"\x52\x49\x46\x46": ".avi",
        b"\x00\x00\x00\x14ftypqt": ".mov",
    }
    for signature, ext in signatures.items():
        if data.startswith(signature):
            return ext
    return ".mp4"  # Default fallback
