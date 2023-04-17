from dataclasses import dataclass
from pathlib import Path

from vscripts.data.streams import VideoStream


@dataclass
class ProcessingData:
    path: Path
    audio_track: int

    video_stream: VideoStream | None

    @classmethod
    def from_path(cls, path: Path, audio_track: int = 0) -> "ProcessingData":
        if not path.is_file() or not path.exists():
            raise ValueError(f"invalid {path=}")

        video_stream = VideoStream.from_file(path)
        return ProcessingData(
            path=path,
            audio_track=audio_track,
            video_stream=video_stream,
        )
