import subprocess


def retrieve_audio_format(file_path: str, track: int) -> str:
    command = (
        f"ffprobe -v error -select_streams a:{track} -show_entries stream=codec_name -of "
        + f"default=nokey=1:noprint_wrappers=1 {file_path}"
    )
    return subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True).strip()
