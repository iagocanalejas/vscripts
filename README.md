# VScript

Run a series of commands to a given file.

```sh
python vscript.py <path>
    extract[=0]
    atempo[=25.0]
	atempo-video[=23.976]
    delay[=1.0]
    hasten[=1.0]
    append[=LAST_OUTPUT]
    subs
```

# DownloadYT

Adds a watcher into the given file and download all the URLs found in it.

```sh
python downloadyt.py
    -f, --file <path> (./todo.txt)
    -o, --out <path> (./out)

```

# Subtitles

For each file in <path> tries to find the matching subtitle file in <path> and in '<path>/subs'.

```sh
python subtitles.py <path>
```
