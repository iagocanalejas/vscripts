import logging
import subprocess

from pyutils.shortcuts import random_user_agent

logger = logging.getLogger("vscripts")


def download_url(url: str, output_dir: str) -> str:
    command = ["yt-dlp", "--progress", url, "--user-agent", random_user_agent(), "-P", output_dir]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert process.stdout is not None
    for line in process.stdout:
        logger.info(line)  # show yt-dlp’s live progress

    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{stderr}")

    return stdout
