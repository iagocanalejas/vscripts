# VScript

Run a series of commands to a given file.

```sh
python vscript.py <path>
    extract[=0]
    atempo[=25.0]
    delay[=1.0]
    hasten[=1.0]
```

# DownloadYT

Adds a watcher into the given file and download all the URLs found in it.

```sh
python downloadyt.py 
    -f, --file <path> (./todo.txt)
    -o, --out <path> (./out)

```

# Commands

Individual callable commands

### Extract

```sh
python extract.py <path> --track=0 (int)
```

### Atempo

```sh
python atempo.py <path> --rate=25.0 (float)
```

### Delay

```sh
python delay.py <path> --delay=1.0 (float)
```

### Hasten

```sh
python hasten.py <path> --hasten=1.0 (float)
```