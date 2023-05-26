# VScript

```sh
python extract.py <path> <command> <arguments>
```

# Commands

### Atempo

```sh
python vscript.py atempo <path> \
    --rate=25 (float)
```

### Extract

```sh
python vscript.py extract <path> \
    --track=0 (int)
```

### Delay

```sh
python vscript.py delay <path> \
    --delay=1.0 (float)
```

### Hasten

```sh
python vscript.py hasten <path> \
    --hasten=1.0 (float)
```

# DownloadYT
Adds a watcher into the given file and download all the URLs found in it.

```sh
python downloadyt.py 
    -f, --file <path> (./todo.txt)
    -o, --out <path> (./out)

```