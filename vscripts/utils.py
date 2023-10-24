import subprocess


def retrieve_audio_format(file_path: str, track: int) -> str:
    probe_command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        f"a:{track}",
        "-show_entries",
        "stream=codec_name",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        file_path,
    ]

    return subprocess.check_output(probe_command, stderr=subprocess.PIPE, text=True).strip()
