# VScript

```sh
# install VScripts
pip install .

# run a series of commands to a given file.
vscripts do PATH \
    [extract[=0]] \
    [atempo[=25.0,23.976]]] \
    [atempo-with] \
	[atempo-video[=23.976]] \
    [delay[=1.0]] \
    [hasten[=1.0]] \
    [append[=LAST_OUTPUT]] \
    [subs PATH]
```

```sh
# inspect a file and adds metadata to it.
vscripts do PATH inspect [--force-detection]
```

# Subtitles

For each file in <path> tries to find the matching subtitle file in <path> and in '<path>/subs' and append the
subtitle file to the video one.

```sh
python scripts/subtitles.py PATH
```

# Utilities

```sh
TEST_ENV=true python -m pytest -n auto
TEST_ENV=true coverage run -m pytest
coverage report -m
```
