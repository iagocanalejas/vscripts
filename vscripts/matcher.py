import os
import re

from pyutils.strings import remove_trailing_hyphen, whitespaces_clean


class NameMatcher:
    def __init__(self, name: str):
        self.name = name

    def clean(self) -> str:
        if self.matches_season_x_episode():
            return self.clean_season_x_episode()
        elif self.matches_s_season_e_episode():
            return self.clean_s_season_e_episode()
        elif self.matches_cap_dot_season_episode():
            return self.clean_cap_dot_season_episode()
        return self.name

    def matches_season_x_episode(self) -> bool:
        reg = r"[ -]*(\d+)x(\d+)[ -]*"
        return bool(re.search(reg, self.name))

    def matches_s_season_e_episode(self) -> bool:
        reg = r"[ -]*S(\d+)E(\d+)[ -]*"
        return bool(re.search(reg, self.name))

    def matches_cap_dot_season_episode(self) -> bool:
        reg = r"cap.(\d{3})"
        return bool(re.search(reg, self.name))

    def clean_season_x_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        name = re.sub(r"[ -]*(\d+)x(\d+)[ -]*", r" - S\1E\2 - ", name, flags=re.IGNORECASE)
        name = whitespaces_clean(remove_trailing_hyphen(name))

        return f"{os.path.splitext(name)[0]}.mkv"

    def clean_s_season_e_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        name = re.sub(r"[ -]*S(\d+)E(\d+)[ -]*", r" - S\1E\2 - ", name, flags=re.IGNORECASE)
        name = whitespaces_clean(remove_trailing_hyphen(name))

        return f"{os.path.splitext(name)[0]}.mkv"

    def clean_cap_dot_season_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        match = re.match(r".*cap\.(\d)(\d{2}).*", name)
        assert match is not None, f"could not match cap number in {name}"

        show_name = name.split(" - ")[0].strip()
        season = match.group(1)
        episode = match.group(2)

        return whitespaces_clean(f"{show_name} - S0{season}E{episode}.mkv")

    def _clean_after_resolution(self, name: str) -> str:
        # remove everything after resolution except the extension
        return re.sub(r"_?\d+p.*\.(\w{3})", r".\1", name, flags=re.IGNORECASE)

    def _clean_suffixes(self, name: str) -> str:
        file_name = name.replace(" (1)", "")
        file_name = file_name.replace(" (TV)", "")
        return file_name
