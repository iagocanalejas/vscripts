from typing import Tuple
from pathlib import Path

def inout(path: Path) -> Tuple[str, str]:
    return str(path.resolve(strict=True)).replace(' ', r'\ '), str(path.parent / path.stem).replace(' ', r'\ ')

