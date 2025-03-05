import os
import re
from enum import StrEnum

from pyutils.strings import remove_hyphens, whitespaces_clean


class NameMatcher:
    class Type(StrEnum):
        X_NAME = "season_x_episode"
        SE_NAME = "s_season_e_episode"
        CAP_DOT_NAME = "cap_dot_season_episode"

    _CATEGORIES = {
        Type.X_NAME: r"[ -]*(\d+)x(\d+)[ -]*",
        Type.SE_NAME: r"[ -]*S(\d+)E(\d+)[ -]*",
        Type.CAP_DOT_NAME: r"cap (\d{3,4})",
    }

    def __init__(self, name: str):
        self.name = self._fix_spacing(name)

    def classify(self) -> Type:
        for category, pattern in self._CATEGORIES.items():
            if re.search(pattern, self.name, flags=re.IGNORECASE):
                return category
        assert False, f"could not classify {self.name}"

    def clean(self) -> str:
        ttype = self.classify()
        cleaning_methods = {
            self.Type.X_NAME: self._clean_season_x_episode,
            self.Type.SE_NAME: self._clean_s_season_e_episode,
            self.Type.CAP_DOT_NAME: self._clean_cap_dot_season_episode,
        }
        cleaning_method = cleaning_methods.get(ttype, lambda: self.name)
        return cleaning_method()

    def _clean_season_x_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        name = re.sub(
            r"[ -]*(\d+)x(\d+)[ -]*",
            lambda m: f" - S{int(m.group(1)):02d}E{int(m.group(2)):02d} - ",
            name,
            flags=re.IGNORECASE,
        )
        name = whitespaces_clean(remove_hyphens(name))

        return f"{os.path.splitext(name)[0]}.mkv"

    def _clean_s_season_e_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        name = re.sub(
            r"[ -]*S(\d+)E(\d+)[ -]*",
            lambda m: f" - S{int(m.group(1)):02d}E{int(m.group(2)):02d} - ",
            name,
            flags=re.IGNORECASE,
        )
        name = whitespaces_clean(remove_hyphens(name))

        return f"{os.path.splitext(name)[0]}.mkv"

    def _clean_cap_dot_season_episode(self) -> str:
        name = self._clean_after_resolution(self.name)
        name = self._clean_suffixes(name)

        match = re.match(r".*cap (\d{1,2})(\d{2}).*", name, flags=re.IGNORECASE)
        assert match is not None, f"could not match cap number in {name}"

        show_name = name.split(" - ")[0].strip()
        season = match.group(1)
        episode = match.group(2)

        return whitespaces_clean(f"{show_name} - S{int(season):02d}E{int(episode):02d}.mkv")

    #############################
    ###### CLEANING METHODS #####
    #############################

    def _fix_spacing(self, name: str) -> str:
        name, ext = os.path.splitext(name)
        name = name.replace("_", " ").replace(".", " ").strip()
        return f"{name}{ext}"

    def _clean_after_resolution(self, name: str) -> str:
        # remove everything after resolution except the extension
        return re.sub(r" ?\d+p.*\.(\w{3})", r".\1", name, flags=re.IGNORECASE)

    def _clean_suffixes(self, name: str) -> str:
        file_name = name.replace(" (1)", "")
        file_name = file_name.replace(" (TV)", "")
        file_name = re.sub(r"v\d$", "", file_name, flags=re.IGNORECASE)
        return file_name
