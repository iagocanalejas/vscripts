import subprocess


def retrieve_audio_format(file_path: str, track: int) -> str:
    command = (
        f"ffprobe -v error -select_streams a:{track} -show_entries stream=codec_name -of "
        + f"default=nokey=1:noprint_wrappers=1 {file_path}"
    )
    return subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True).strip()


def retrieve_number_of_subtitle_tracks(file_path) -> int:
    command = f"ffprobe -i {file_path} -show_entries stream=index,codec_type:stream_tags=language -v quiet -of csv=p=0"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True).strip()
    return len([e for e in output.split("\n") if "subtitle" in e])
