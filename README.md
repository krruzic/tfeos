# Twenty Forty Eight OS

A modular LED matrix operating system for Raspberry Pi with RGB LED panels. Applications are dynamically loaded and configured through a web interface.

## Overview

The system displays applications on a 64x32 LED matrix. Each application provides scenes (visual output), configuration options via a JSON DSL, and metadata. A web interface allows configuring apps without code changes.

The main menu shows installed applications as 16x16 icons in a 2x3 grid with page indicators.

## Development (Emulator)
```bash
poetry install
poetry run python -m tfeos.main --no-matrix
```

The emulator opens a browser window at `http://localhost:8888` showing the LED matrix.

Access the web interface at `http://localhost:8000`

## Raspberry Pi Deployment

Install the matrix library:
```bash
sudo apt-get update
sudo apt-get install -y git python3-dev python3-pillow cython3
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make build-python
sudo make install-python
```

Install and run the OS:
```bash
poetry install --no-dev
sudo poetry run python -m tfeos.main
```

## Creating Applications

Place apps in `applications/`. Each app needs:
- `metadata.json` - name, version, icon, description, author
- `dsl.json` - configuration schema
- `config.json` - current configuration
- `app.py` - Application class with scenes

See `applications/clock/` for an example.

## Credits

- `https://github.com/gidger/rpi-led-nhl-scoreboard/` for most of the NHL scoreboard code
