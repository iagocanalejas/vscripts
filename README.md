# VScript

```sh
# run a series of commands to a given file.
python scripts/vscript.py PATH \
    [extract[=0]] \
    [atempo[=25.0]]] \
	[atempo-video[=23.976]] \
    [delay[=1.0]] \
    [hasten[=1.0]] \
    [append[=LAST_OUTPUT]] \
    [subs PATH]
```

# Subtitles

For each file in <path> tries to find the matching subtitle file in <path> and in '<path>/subs' and append the
subtitle file to the video one.

```sh
python scripts/subtitles.py PATH
```
