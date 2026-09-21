# hue: plan

Single-file, zero-dependency Python 3 CLI for the Philips Hue bridge on the LAN. Same shape as `cfreg` and `exrate`: one script, stdlib only, no prompts, `--json` for pipes. Binary name `hue` (short, typeable, matches `hue on desk`).

## Scope (v0.1)

Turn lights/rooms on/off, set brightness/colour temperature/colour, activate scenes, list what exists, pair with the bridge. Nothing else. No schedules, no sensors, no entertainment streaming, no bridge discovery UI beyond one cloud lookup.

## Decisions

- **API: CLIP v2** (`https://<bridge>/clip/v2/resource/...`, header `hue-application-key`). v1 is deprecated and v2 is verified working on this bridge (6 lights, 4 rooms, 35 scenes, 5 grouped_lights). Only `pair` uses the v1 `POST /api` endpoint because that is the only way to mint a key.
- **TLS**: bridge cert is self-signed by Signify. v0.1 skips verification (`ssl._create_unverified_context`) and says so in the file header. Pinning the Signify root CA is a later step; the threat model is a home LAN.
- **Targets by name, not id.** `hue on "ekin office"` resolves case-insensitively against rooms first, then lights, then zones. Ambiguous or unknown names fail with exit 3 and list the closest matches (`difflib.get_close_matches`). `all` targets every light. UUIDs are also accepted so `--json` output round-trips.
- **Verb-first, not noun-verb.** `hue on desk` beats `hue light on desk` for a tool typed a dozen times a day with two nouns total. Listing commands are the plural nouns (`lights`, `rooms`, `scenes`).
- **Scenes are room-scoped.** Names repeat across rooms (four "Bright", three "Sleepy"). `hue scene bright` fails as ambiguous unless `--room` is given or only one room has it.
- **Config file, not env var.** Key lives at `~/.config/hue/config.json` (`{"bridge": "192.168.1.100", "key": "..."}`, mode 0600). `pair` writes it. `--bridge`/`--key` and `HUE_BRIDGE`/`HUE_CONFIG` override for scripts. The key never goes on the command line in docs.
- **Brightness in percent (1-100)**, colour temperature in Kelvin (2000-6500), colour as CSS name or `#rrggbb` converted to CIE xy. Users think in these units; the bridge's mirek and xy are implementation detail.
- **Percent output only, no ANSI colour swatches.** Terminal colour is a nice-to-have with TTY/NO_COLOR gating cost; skip for v0.1.

## Commands

```
hue pair [--bridge IP]                        poll for link button up to 90s, write config
hue lights [--json]                           name, on/off, brightness %, reachable, room
hue rooms [--json]                            name, light count, any_on/all_on
hue scenes [ROOM] [--json]                    scene names grouped by room
hue status [TARGET] [--json]                  detail for one target, or everything
hue on TARGET... [--json]
hue off TARGET... [--json]
hue toggle TARGET... [--json]                 per target: flip its any_on
hue set TARGET... [--bri N] [--ct K] [--color C] [--on|--off] [--transition MS] [--json]
hue scene NAME [--room ROOM] [--json]
```

Global flags: `--bridge`, `--key`, `--timeout SEC` (default 5), `--json`, `-q/--quiet`, `--version`, `-h/--help`.

`on`/`off`/`toggle` are sugar for `set` with one flag; they share the resolver and the output path.

## Output

- Human: aligned table on stdout, one line per target after a mutation (`Ekin Office: on, 3 lights`). Reflects the state read back from the bridge after the PUT, not the request.
- `--json`: the v2 resource objects, trimmed to id, name, type, on, brightness, color_temperature, color, room. Same shape for every command so `jq` recipes transfer.
- Errors on stderr, one line, with the fix: `No target named "desk". Did you mean: Desk Left, Desk Right?`
- No output on `-q` except errors.

## Exit codes

| code | meaning |
|---|---|
| 0 | ok |
| 1 | bridge unreachable / HTTP error / timeout |
| 2 | usage (argparse) |
| 3 | target or scene not found / ambiguous |
| 4 | not paired (no config) or key rejected (401); message says `run hue pair` |
| 5 | pair timed out (link button not pressed) |

## File layout

```
philips-hue-cli/
  hue            single executable, ~500 lines, sections: header, config, http, resolve, commands, main
  test_hue.py    stdlib unittest; fake bridge via a recorded fixture dict, no network
  README.md
  plan.md
```

`hue` header block: responsibility, v2 endpoints used, the TLS shortcut and its ceiling, config path, exit code table.

## Implementation steps

1. Skeleton: argparse with all subcommands, `--version`, help text with three examples at the top, exit-code mapping. Every subcommand prints "not implemented" and exits 1. (30 min)
2. HTTP layer: one `request(method, path, body)` on `urllib` with the unverified SSL context, timeout, and error translation (connection refused, 401, 404, v2 `errors[]`). Config load/save. (30 min)
3. `pair`: v1 POST loop, 2s interval, 90s cap, writes config 0600. (20 min)
4. Read commands: `lights`, `rooms`, `scenes`, `status`. One `snapshot()` that fetches light, room, zone, grouped_light, scene, device in six calls and joins them by `rid` into plain dicts. Everything else reads from the snapshot. (1 h)
5. Resolver: name → list of (rtype, rid, grouped_light rid) with case-insensitive exact match, then close-match suggestions. (30 min)
6. Mutations: `set` builds one v2 body (`on`, `dimming.brightness`, `color_temperature.mirek`, `color.xy`, `dynamics.duration`), PUTs to `grouped_light` for rooms/zones and `light` for lights, then re-reads for output. `on`/`off`/`toggle` call it. (1 h)
7. `scene`: resolve by name within room scope, PUT `recall.action=active`. (20 min)
8. Colour conversion: CSS colour table (147 names, inline dict) + sRGB → CIE xy (gamma correct, standard matrix). Kelvin ↔ mirek. (30 min)
9. Tests: fixture recorded from the real bridge (`snapshot()` output, ids scrubbed), unit tests for resolver ambiguity, scene scoping, colour math, exit codes, `--json` shape. (1 h)
10. README from the cfreg template, `brew` formula in `ekinertac/tap`, install via `ln -s` for now. (30 min)

Total: about 6 hours.

## Non-goals, written down so they stay out

- Interactive picker of any kind.
- Discovery beyond `https://discovery.meethue.com` fallback in `pair` when `--bridge` is omitted.
- Effects, dynamic scenes, entertainment areas, sensors, motion, schedules, rules.
- Long-lived daemon or SSE event stream.
- Windows support (bridge cert handling differs; nobody asked).
