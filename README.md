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

# Reencode

```sh
# reencode a file using HandBrakeCLI with the given quality.
python scripts/reencode.py FILE_OR_FOLDER ]
	-q, --quality [1080p|2160p|AV1]
```

# DownloadFile

Adds a watcher into the given file and download all the URLs found in it.

```sh
python scripts/downloafile.py \
    -f, --file PATH \
    -o, --out PATH
```

# Subtitles

For each file in <path> tries to find the matching subtitle file in <path> and in '<path>/subs' and append the
subtitle file to the video one.

```sh
python scripts/subtitles.py PATH
```
