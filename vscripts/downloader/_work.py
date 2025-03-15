import logging
import os
import re

from pyutils.validators import is_valid_url


class WorkQueue:
    _QUEUE: list[str] = []
    _PROCESSING: str | None = None
    _COMPLETED: list[str] = []
    _LAST_MODIFIED: float | None = None

    _todo_file: str

    @property
    def is_processing(self) -> bool:
        return self._PROCESSING is not None

    @property
    def can_process(self) -> bool:
        return self._PROCESSING is not None or len(self._QUEUE) > 0

    @property
    def completed(self) -> int:
        return len(self._COMPLETED)

    def __init__(self, todo_file: str):
        self._todo_file = todo_file

    def next(self) -> str | None:
        if self._PROCESSING is not None:
            self._COMPLETED.append(self._PROCESSING)
            self._PROCESSING = None

        self._PROCESSING = self._QUEUE.pop(0) if len(self._QUEUE) > 0 else None
        return self._PROCESSING

    def check_file_changes(self):
        modified = os.path.getmtime(self._todo_file)
        if modified != self._LAST_MODIFIED:
            self._LAST_MODIFIED = modified
            self._add_new_urls()

    def remove_completed_urls(self):
        """Filter lines in a file to remove those already completed."""
        with open(self._todo_file) as file:
            lines = file.readlines()

        with open(self._todo_file, "w") as file:
            for line in lines:
                if re.sub(r"\s", "", line) in self._COMPLETED:
                    continue
                file.write(line)

        logging.info("\n\nProcessed: \n\n")
        logging.info(self._COMPLETED)

    def _add_new_urls(self):
        """Filter lines in a file to check for new URLs to download."""
        with open(self._todo_file) as file:
            lines = file.readlines()

        for pos, line in enumerate(lines):
            line = re.sub(r"\s", "", line)
            if not line or not is_valid_url(line):
                logging.error(f"invalid {pos}: {line=}")
                continue

            if line in self._COMPLETED or line in self._QUEUE:
                continue

            logging.info(f"adding new {line=}")
            self._QUEUE.append(line)
