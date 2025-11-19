from typing import Any

from pyutils.strings import whitespaces_clean


def parse_srt(content: str) -> list[dict[str, Any]]:
    blocks = []
    current: dict[str, Any] = {"index": None, "time": None, "lines": []}
    for line in content.splitlines():
        if line.strip().isdigit():
            if current["index"] is not None:
                blocks.append(current)
            current = {"index": line.strip(), "time": None, "lines": []}
        elif "-->" in line:
            current["time"] = line
        elif line.strip():
            current["lines"].append(whitespaces_clean(line))
    if current["index"] is not None:
        blocks.append(current)
    return blocks


def rebuild_srt(blocks: list[dict[str, Any]], lines: list[str]) -> str:
    index = 0
    out = []
    for block in blocks:
        out.append(block["index"])
        out.append(block["time"])
        for _ in block["lines"]:
            out.append(lines[index])
            index += 1
        out.append("")
    return "\n".join(out)


def to_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
