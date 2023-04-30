# Commands

## VScript

```sh
python extract.py <path> <command> \
    --rate=25 (float)
    --track=0 (int)
    --delay=1.0 (float)
    --hasten=1.0 (float)

    |command|
        - atempo
        - extract
        - delay
        - hasten
```

## Atempo

```sh
python atempo.py <path> \
    --rate=25 (float)
```

## Extract

```sh
python extract.py <path> \
    --track=0 (int)
```

## Delay

```sh
python delay.py <path> \
    --delay=1.0 (float)
```

## Hasten

```sh
python hasten.py <path> \
    --hasten=1.0 (float)
```
