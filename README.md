# hue

Control Philips Hue lights from the command line.

Turn lights/rooms on/off, set brightness/colour temperature/colour, activate
scenes, and list what exists. Targets are **names**, not ids: `hue on desk`,
`hue set living-room --bri 50`.

## Install

```bash
# Copy the script somewhere on your PATH
cp hue ~/bin/
chmod +x ~/bin/hue

# Or symlink
ln -s "$PWD/hue" ~/bin/hue
```

### Homebrew

```bash
brew install ekinertac/tap/hue
```

## Commands

```
hue pair [--bridge IP]                        Pair with the bridge (90s window)
hue lights [--json]                           List all lights
hue rooms [--json]                            List all rooms
hue scenes [ROOM] [--json]                    List scenes (optionally by room)
hue status [TARGET...] [--json]               Show state of targets or everything
hue on TARGET...                              Turn target(s) on
hue off TARGET...                             Turn target(s) off
hue toggle TARGET...                          Toggle target(s)
hue set TARGET... [--bri N] [--ct K] [--color C] [--on|--off] [--transition MS]
hue scene NAME [--room ROOM]                  Activate a scene
```

Global flags: `--bridge`, `--key`, `--timeout`, `--json`, `-q`/`--quiet`, `--version`.

### Examples

```bash
# First-time setup
hue pair --bridge 192.168.1.100

# Turn things on/off
hue on "ekin office"
hue off "desk left"
hue toggle "living room"

# Set brightness and colour
hue set "ekin office" --bri 80
hue set "bedroom" --bri 30 --ct 2200
hue set "desk left" --color coral

# Activate a scene
hue scene bright --room "ekin office"

# List everything
hue lights
hue rooms --json | jq '.[] | {name, on}'
```

## Targets

Targets are matched **case-insensitively** against room names first, then light
names, then zone names. The special name `all` targets every room.

If a name matches multiple targets (e.g. "Desk Left" and "Desk Right" both
contain "desk"), the command fails with a suggestion. Use a unique name or a
UUID (`hue lights --json` shows ids).

## Colours

- **Brightness**: 1–100 percent.
- **Colour temperature**: Kelvin 2000–6500 (warm → cool).
- **Colour**: any CSS named colour (`coral`, `steelblue`, ...) or `#rrggbb`.

## Output

- Human output is an aligned table on stdout.
- `--json` outputs a JSON array of trimmed resource objects (id, name, type, on,
  brightness, color_temperature, color, room). Same shape for every command so
  `jq` recipes transfer.
- Errors go to stderr. Quiet mode (`-q`) suppresses normal output.

## Config

The application key is stored at `~/.config/hue/config.json` (mode 0600).

Override via environment:
- `HUE_BRIDGE` — bridge IP
- `HUE_CONFIG` — alternate config path

## Exit codes

| Code | Meaning                                 |
|------|-----------------------------------------|
| 0    | OK                                      |
| 1    | Bridge unreachable / HTTP error / timeout |
| 2    | Usage (argparse)                        |
| 3    | Target or scene not found / ambiguous   |
| 4    | Not paired / key rejected               |
| 5    | Pair timed out (link button not pressed) |

## Requirements

- Python 3.10+
- A Philips Hue bridge on the same LAN
- No external dependencies (stdlib only)

## Non-goals

No schedules, no sensors, no entertainment streaming, no bridge discovery UI,
no Windows support.