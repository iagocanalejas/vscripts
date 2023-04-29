import os
from typing import Tuple, List
from pathlib import Path
import shlex


def inout(path: Path) -> Tuple[str, str]:
    return shlex.quote(str(path.resolve(strict=True))), shlex.quote(str(path.parent / path.stem))


def expand_path(path: str, valid_files: List[str] | None = None) -> List[str]:
    if os.path.isfile(path):
        return [os.path.abspath(path)]

    def is_valid(file: str) -> bool:
        if not valid_files:
            return True
        _, extension = os.path.splitext(file)
        return extension.upper() in valid_files

    return [os.path.abspath(os.path.join(dp, f)) for dp, _, filenames in os.walk(path) for f in filenames if is_valid(f)]
