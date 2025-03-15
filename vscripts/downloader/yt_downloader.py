import subprocess


def download(url: str, output_folder: str):
    command = ["yt-dlp", "--progress", "--prefer-ffmpeg", url, "-P", output_folder]
    process = subprocess.Popen(command, stdout=None, stderr=None)
    process.wait()
