# VScript

```sh
# install VScripts
pip install .
```

### Basic Usage

```sh
vscripts do PATH extract generate-subs translate=es append
# this command will:
# 1. extract audio from PATH video file
# 2. generate subtitles for the extracted audio
# 3. translate the generated subtitles to Spanish
# 4. append the generated subtitles to the original video file
```

```sh
vscripts do PATH extract atempo delay=2 append
# this command will:
# 1. extract audio from PATH video file
# 2. change the audio tempo
# 3. delay the audio by 2 seconds
# 4. append the modified audio back to the original video file
```

```sh
vscripts do PATH inspect [--force-detection]
# this command will:
# 1. inspect the video file at PATH
# 2. if --force-detection is provided, it will force re-detection ignoring metadata
# 3. add all the found metadata to the video file
```

### Available Commands

```sh
append=PATH
append-subs=PATH
atempo=OG_RATE,NEW_RATE
atempo-with=FACTOR
atempo-video=FACTOR
extract=TRACK_INDEX
dissect
delay=SECONDS
hasten=SECONDS
inspect
reencode=PRESET
generate-subs
translate=TARGET_LANG
```

# Subtitles

For each file in <path> tries to find the matching subtitle file in <path> and in '<path>/subs' and append the
subtitle file to the video one.

```sh
python scripts/subtitles.py PATH
```

# Utilities

```sh
python -m pytest -n auto
coverage run -m pytest
coverage report -m
```

```

```
