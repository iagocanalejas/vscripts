import logging
import os
import random
import time

import requests


def download(url: str, output_folder: str, output_file: str):
    assert "{}" in url, "URL must contain a placeholder for the chunk number"
    assert os.path.exists(output_folder), "output folder does not exist"

    tmp_file = os.path.join(output_folder, f"{output_file}.tmp")
    file_extension = None

    with open(tmp_file, "ab") as outfile:
        i = 1
        while True:
            response = requests.get(url.format(i), headers=HTTP_HEADERS(), stream=True)
            if response.status_code != 200:
                break

            response_size = 0
            for chunk in response.iter_content(chunk_size=None):
                if i == 1 and file_extension is None:
                    file_extension = detect_file_extension(chunk[:16])
                    logging.info(f"detected file format: {file_extension}")

                outfile.write(chunk)
                response_size += len(chunk)

            logging.info(f"fragment {i} downloaded ({response_size} bytes) and appended")
            i += 1

            if i % 10 == 0:
                time.sleep(random.randint(1, 5))

    os.rename(tmp_file, os.path.join(output_folder, f"{output_file}{file_extension}"))
    logging.info(f"all fragments merged into {output_file}{file_extension}")


_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",  # noqa
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/54.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/16.16299",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",  # noqa
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6",  # noqa
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/60.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.18362",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",  # noqa
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/70.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/75.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",  # noqa
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",  # noqa
]


def HTTP_HEADERS():  # pragma: no cover
    return {
        "Accept": "*/*",
        "User-Agent": _USER_AGENTS[random.randint(0, len(_USER_AGENTS) - 1)],
        "Accept-Language": "gl-ES,gl;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "Origin": "https://tmdbcdn.lat",
        "Connection": "keep-alive",
        "Referer": "https://tmdbcdn.lat/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }


# Magic bytes for video file type detection
def detect_file_extension(data):
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
