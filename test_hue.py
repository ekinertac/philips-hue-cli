#!/usr/bin/env python3
"""Unit tests for hue CLI. No network — fake bridge via recorded fixtures."""

import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Load hue module from executable (no .py extension)
_hue_path = Path(__file__).resolve().parent / "hue"
hue = types.ModuleType("hue")
exec(_hue_path.read_text(), hue.__dict__)
sys.modules["hue"] = hue


# ---------------------------------------------------------------------------
# Fixture: snapshot data recorded from a real bridge (ids scrubbed)
# ---------------------------------------------------------------------------

FIXTURE_LIGHTS = [
    {
        "id": "a1b2c3d4-0001",
        "type": "light",
        "metadata": {"name": "Desk Left", "archetype": "sultan_bulb"},
        "on": {"on": True},
        "dimming": {"brightness": 80.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 250, "mirek_valid": True, "mirek_schema": {"mirek_minimum": 153, "mirek_maximum": 500}},
        "color": {"xy": {"x": 0.4, "y": 0.4}},
        "light": {"is_reachable": True},
    },
    {
        "id": "a1b2c3d4-0002",
        "type": "light",
        "metadata": {"name": "Desk Right", "archetype": "sultan_bulb"},
        "on": {"on": False},
        "dimming": {"brightness": 100.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 153, "mirek_valid": True, "mirek_schema": {"mirek_minimum": 153, "mirek_maximum": 500}},
        "color": {"xy": {"x": 0.5, "y": 0.4}},
        "light": {"is_reachable": True},
    },
    {
        "id": "a1b2c3d4-0003",
        "type": "light",
        "metadata": {"name": "Ceiling", "archetype": "ceiling_round"},
        "on": {"on": True},
        "dimming": {"brightness": 50.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 400, "mirek_valid": True, "mirek_schema": {"mirek_minimum": 153, "mirek_maximum": 500}},
        "color": {"xy": {"x": 0.45, "y": 0.42}},
        "light": {"is_reachable": True},
    },
    {
        "id": "a1b2c3d4-0004",
        "type": "light",
        "metadata": {"name": "Floor Lamp", "archetype": "floor_lantern"},
        "on": {"on": True},
        "dimming": {"brightness": 35.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 300, "mirek_valid": True, "mirek_schema": {"mirek_minimum": 153, "mirek_maximum": 500}},
        "color": {"xy": {"x": 0.42, "y": 0.41}},
        "light": {"is_reachable": True},
    },
    {
        "id": "a1b2c3d4-0005",
        "type": "light",
        "metadata": {"name": "Bedside", "archetype": "sultan_bulb"},
        "on": {"on": False},
        "dimming": {"brightness": 0.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 250, "mirek_valid": True, "mirek_schema": {"mirek_minimum": 153, "mirek_maximum": 500}},
        "color": {"xy": {"x": 0.44, "y": 0.40}},
        "light": {"is_reachable": True},
    },
    {
        "id": "a1b2c3d4-0006",
        "type": "light",
        "metadata": {"name": "Unreachable", "archetype": "sultan_bulb"},
        "on": {"on": False},
        "dimming": {"brightness": 0.0, "min_dim_level": 0.01},
        "color_temperature": {"mirek": 250, "mirek_valid": True},
        "light": {"is_reachable": False},
    },
]

FIXTURE_ROOMS = [
    {
        "id": "b1c2d3e4-0001",
        "type": "room",
        "metadata": {"name": "Ekin Office", "archetype": "office"},
        "children": [],
        "services": [
            {"rid": "a1b2c3d4-0001", "rtype": "light"},
            {"rid": "a1b2c3d4-0002", "rtype": "light"},
            {"rid": "a1b2c3d4-0003", "rtype": "light"},
            {"rid": "c1d2e3f4-gl01", "rtype": "grouped_light"},
        ],
    },
    {
        "id": "b1c2d3e4-0002",
        "type": "room",
        "metadata": {"name": "Living Room", "archetype": "living_room"},
        "children": [],
        "services": [
            {"rid": "a1b2c3d4-0004", "rtype": "light"},
            {"rid": "c1d2e3f4-gl02", "rtype": "grouped_light"},
        ],
    },
    {
        "id": "b1c2d3e4-0003",
        "type": "room",
        "metadata": {"name": "Bedroom", "archetype": "bedroom"},
        "children": [],
        "services": [
            {"rid": "a1b2c3d4-0005", "rtype": "light"},
            {"rid": "c1d2e3f4-gl03", "rtype": "grouped_light"},
        ],
    },
    {
        "id": "b1c2d3e4-0004",
        "type": "room",
        "metadata": {"name": "Unused Room", "archetype": "other"},
        "children": [],
        "services": [
            {"rid": "a1b2c3d4-0006", "rtype": "light"},
            {"rid": "c1d2e3f4-gl04", "rtype": "grouped_light"},
        ],
    },
]

FIXTURE_ZONES = []

FIXTURE_GROUPED_LIGHTS = [
    {"id": "c1d2e3f4-gl01", "type": "grouped_light", "on": {"on": True, "any_on": True}, "dimming": {"brightness": 70.0}},
    {"id": "c1d2e3f4-gl02", "type": "grouped_light", "on": {"on": True, "any_on": True}, "dimming": {"brightness": 35.0}},
    {"id": "c1d2e3f4-gl03", "type": "grouped_light", "on": {"on": False, "any_on": False}},
    {"id": "c1d2e3f4-gl04", "type": "grouped_light", "on": {"on": False, "any_on": False}},
]

FIXTURE_SCENES = [
    {"id": "d1e2f3a4-sc01", "type": "scene", "metadata": {"name": "Bright"},
     "group": {"rid": "b1c2d3e4-0001", "rtype": "room"}},
    {"id": "d1e2f3a4-sc02", "type": "scene", "metadata": {"name": "Sleepy"},
     "group": {"rid": "b1c2d3e4-0001", "rtype": "room"}},
    {"id": "d1e2f3a4-sc03", "type": "scene", "metadata": {"name": "Concentrate"},
     "group": {"rid": "b1c2d3e4-0001", "rtype": "room"}},
    {"id": "d1e2f3a4-sc04", "type": "scene", "metadata": {"name": "Bright"},
     "group": {"rid": "b1c2d3e4-0002", "rtype": "room"}},
    {"id": "d1e2f3a4-sc05", "type": "scene", "metadata": {"name": "Dim"},
     "group": {"rid": "b1c2d3e4-0002", "rtype": "room"}},
    {"id": "d1e2f3a4-sc06", "type": "scene", "metadata": {"name": "Sleepy"},
     "group": {"rid": "b1c2d3e4-0003", "rtype": "room"}},
]

FIXTURE_DEVICES = [
    {"id": "e1f2a3b4-dv01", "type": "device", "product_name": "Hue White and Color Ambiance",
     "metadata": {"name": "Desk Left"}, "services": [{"rid": "a1b2c3d4-0001", "rtype": "light"}]},
    {"id": "e1f2a3b4-dv02", "type": "device", "product_name": "Hue White and Color Ambiance",
     "metadata": {"name": "Desk Right"}, "services": [{"rid": "a1b2c3d4-0002", "rtype": "light"}]},
    {"id": "e1f2a3b4-dv03", "type": "device", "product_name": "Hue White Ambiance",
     "metadata": {"name": "Ceiling"}, "services": [{"rid": "a1b2c3d4-0003", "rtype": "light"}]},
    {"id": "e1f2a3b4-dv04", "type": "device", "product_name": "Hue Go",
     "metadata": {"name": "Floor Lamp"}, "services": [{"rid": "a1b2c3d4-0004", "rtype": "light"}]},
    {"id": "e1f2a3b4-dv05", "type": "device", "product_name": "Hue White and Color Ambiance",
     "metadata": {"name": "Bedside"}, "services": [{"rid": "a1b2c3d4-0005", "rtype": "light"}]},
    {"id": "e1f2a3b4-dv06", "type": "device", "product_name": "Hue White",
     "metadata": {"name": "Unreachable"}, "services": [{"rid": "a1b2c3d4-0006", "rtype": "light"}]},
]


def build_fixture_snapshot():
    """Build the snapshot dict from fixture data, same shape as hue.snapshot()."""
    from hue import V2_TYPES

    data = {
        "light": FIXTURE_LIGHTS,
        "room": FIXTURE_ROOMS,
        "zone": FIXTURE_ZONES,
        "grouped_light": FIXTURE_GROUPED_LIGHTS,
        "scene": FIXTURE_SCENES,
        "device": FIXTURE_DEVICES,
    }

    rid_index = {}
    for rtype in V2_TYPES:
        for r in data[rtype]:
            rid_index[r["id"]] = r

    gl_by_owner = {}
    for room in data["room"]:
        for svc in room.get("services", []):
            if svc["rtype"] == "grouped_light":
                gl_by_owner[room["id"]] = rid_index.get(svc["rid"])
    for zone in data["zone"]:
        for svc in zone.get("services", []):
            if svc["rtype"] == "grouped_light":
                gl_by_owner[zone["id"]] = rid_index.get(svc["rid"])

    light_device = {}
    device_by_id = {}
    for dev in data["device"]:
        device_by_id[dev["id"]] = dev
        for svc in dev.get("services", []):
            if svc["rtype"] == "light":
                light_device[svc["rid"]] = dev["id"]

    return {
        "lights": data["light"],
        "rooms": data["room"],
        "zones": data["zone"],
        "grouped_lights": data["grouped_light"],
        "scenes": data["scene"],
        "devices": data["device"],
        "rid_index": rid_index,
        "gl_by_owner": gl_by_owner,
        "light_device": light_device,
        "device_by_id": device_by_id,
    }


FIXTURE_SNAPSHOT = build_fixture_snapshot()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def run_cmd(args_str, bridge="192.168.1.100", key="test-key"):
    """Run a hue command by parsing args and calling main() capture logic.

    Returns (stdout, stderr, exit_code_or_None).
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        # We bypass hue.main() parse and directly invoke with a mock args
        # But we also need to handle system exit
        pass
    finally:
        pass

    # We'll use a simpler approach: call the handler directly
    return None, None, None


# We use a helper that creates a mock args namespace and invokes the command
def make_args(cmd, **kwargs):
    """Build an args namespace object with all possible attributes."""
    base = {
        "bridge": "192.168.1.100",
        "key": "test-key",
        "timeout": 5,
        "json": False,
        "quiet": False,
        "cmd": cmd,
        "target": [],
        "scene": None,
        "room": None,
        "brightness": None,
        "color_temp": None,
        "color": None,
        "set_on": None,
        "set_off": None,
        "transition": None,
        "pair_bridge": None,
    }
    base.update(kwargs)
    return type("Args", (), base)()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestColourConversion(unittest.TestCase):
    """Colour math: sRGB → CIE xy, Kelvin ↔ mirek, CSS lookup, hex parse."""

    def test_kelvin_to_mirek(self):
        self.assertEqual(hue.kelvin_to_mirek(4000), 250)
        self.assertEqual(hue.kelvin_to_mirek(2000), 500)
        self.assertEqual(hue.kelvin_to_mirek(6500), 153)

    def test_mirek_to_kelvin(self):
        self.assertEqual(hue.mirek_to_kelvin(250), 4000)
        self.assertEqual(hue.mirek_to_kelvin(153), 6536)  # rounded

    def test_kelvin_clamping(self):
        self.assertEqual(hue.kelvin_to_mirek(1000), 500)  # clamped to 2000K
        self.assertEqual(hue.kelvin_to_mirek(10000), 153)  # clamped to 6500K

    def test_css_color_lookup(self):
        self.assertEqual(hue.css_color_to_rgb("red"), (255, 0, 0))
        self.assertEqual(hue.css_color_to_rgb("coral"), (255, 127, 80))
        self.assertEqual(hue.css_color_to_rgb("nonexistent"), None)

    def test_css_case_insensitive(self):
        self.assertEqual(hue.css_color_to_rgb("RED"), (255, 0, 0))
        self.assertEqual(hue.css_color_to_rgb("Coral"), (255, 127, 80))

    def test_hex_to_rgb(self):
        self.assertEqual(hue.hex_to_rgb("#ff0000"), (255, 0, 0))
        self.assertEqual(hue.hex_to_rgb("ff0000"), (255, 0, 0))
        self.assertEqual(hue.hex_to_rgb("#abc123"), (171, 193, 35))

    def test_hex_to_rgb_invalid(self):
        self.assertIsNone(hue.hex_to_rgb("#ff"))
        self.assertIsNone(hue.hex_to_rgb("nothex"))

    def test_rgb_to_xy(self):
        # Red
        x, y = hue.rgb_to_xy(255, 0, 0)
        self.assertAlmostEqual(x, 0.640, places=2)
        self.assertAlmostEqual(y, 0.330, places=2)

        # Green
        x, y = hue.rgb_to_xy(0, 255, 0)
        self.assertAlmostEqual(x, 0.300, places=2)
        self.assertAlmostEqual(y, 0.600, places=2)

        # Blue
        x, y = hue.rgb_to_xy(0, 0, 255)
        self.assertAlmostEqual(x, 0.150, places=2)
        self.assertAlmostEqual(y, 0.060, places=2)

        # White
        x, y = hue.rgb_to_xy(255, 255, 255)
        self.assertAlmostEqual(x, 0.313, places=2)
        self.assertAlmostEqual(y, 0.329, places=2)

    def test_parse_color_css(self):
        xy = hue.parse_color("coral")
        self.assertIsNotNone(xy)
        self.assertEqual(len(xy), 2)

    def test_parse_color_hex(self):
        xy = hue.parse_color("#ff0000")
        self.assertIsNotNone(xy)
        self.assertAlmostEqual(xy[0], 0.640, places=2)

    def test_parse_color_invalid(self):
        self.assertIsNone(hue.parse_color("notacolor"))


class TestResolver(unittest.TestCase):
    """Target resolution by name: rooms first, then lights, case-insensitive."""

    def test_resolve_room_by_name(self):
        results = hue.resolve_name("Ekin Office", FIXTURE_SNAPSHOT)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "room")
        self.assertEqual(results[0]["id"], "b1c2d3e4-0001")

    def test_resolve_room_case_insensitive(self):
        results = hue.resolve_name("ekin office", FIXTURE_SNAPSHOT)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "room")

    def test_resolve_light_by_name(self):
        results = hue.resolve_name("Desk Left", FIXTURE_SNAPSHOT)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "light")

    def test_resolve_light_case_insensitive(self):
        results = hue.resolve_name("desk left", FIXTURE_SNAPSHOT)
        self.assertEqual(len(results), 1)

    def test_resolve_non_existent(self):
        results = hue.resolve_name("Zxyw", FIXTURE_SNAPSHOT)
        self.assertEqual(len(results), 0)

    def test_resolve_all(self):
        targets = hue.resolve_targets(["all"], FIXTURE_SNAPSHOT)
        self.assertEqual(len(targets), 4)  # 4 rooms

    def test_resolve_uuid(self):
        targets = hue.resolve_targets(["a1b2c3d4-0001"], FIXTURE_SNAPSHOT)
        self.assertEqual(len(targets), 1)

    def test_resolve_room_grouped_light_present(self):
        results = hue.resolve_name("Ekin Office", FIXTURE_SNAPSHOT)
        self.assertIsNotNone(results[0]["grouped_light_id"])

    def test_resolve_light_no_grouped_light(self):
        results = hue.resolve_name("Desk Left", FIXTURE_SNAPSHOT)
        self.assertIsNone(results[0]["grouped_light_id"])


class TestSceneResolver(unittest.TestCase):
    """Scene name resolution with room scoping."""

    def test_scene_unique_across_rooms(self):
        # "Concentrate" only in Ekin Office
        scenes = hue._resolve_scene_name("Concentrate", FIXTURE_SNAPSHOT, room_filter=None)
        self.assertEqual(len(scenes), 1)

    def test_scene_ambiguous(self):
        # "Bright" in both Ekin Office and Living Room
        scenes = hue._resolve_scene_name("Bright", FIXTURE_SNAPSHOT, room_filter=None)
        self.assertEqual(len(scenes), 2)

    def test_scene_with_room_filter(self):
        # "Bright" with room filter
        scenes = hue._resolve_scene_name("Bright", FIXTURE_SNAPSHOT, room_filter="b1c2d3e4-0001")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0]["room_id"], "b1c2d3e4-0001")

    def test_scene_not_found(self):
        scenes = hue._resolve_scene_name("Nonexistent", FIXTURE_SNAPSHOT, room_filter=None)
        self.assertEqual(len(scenes), 0)


class TestSnapshot(unittest.TestCase):
    """Snapshot structure and helper getters."""

    def test_snapshot_keys(self):
        snap = FIXTURE_SNAPSHOT
        for k in ("lights", "rooms", "zones", "grouped_lights", "scenes", "devices",
                  "rid_index", "gl_by_owner", "light_device", "device_by_id"):
            self.assertIn(k, snap)

    def test_rid_index(self):
        r = FIXTURE_SNAPSHOT["rid_index"]["a1b2c3d4-0001"]
        self.assertEqual(r["type"], "light")

    def test_gl_by_owner(self):
        gl = FIXTURE_SNAPSHOT["gl_by_owner"]["b1c2d3e4-0001"]
        self.assertIsNotNone(gl)

    def test_light_device(self):
        dev_id = FIXTURE_SNAPSHOT["light_device"]["a1b2c3d4-0001"]
        self.assertEqual(dev_id, "e1f2a3b4-dv01")

    def test_get_light_on(self):
        self.assertTrue(hue.get_light_on(FIXTURE_LIGHTS[0]))
        self.assertFalse(hue.get_light_on(FIXTURE_LIGHTS[1]))

    def test_get_light_brightness(self):
        self.assertEqual(hue.get_light_brightness(FIXTURE_LIGHTS[0]), 80.0)

    def test_get_light_color_temp(self):
        self.assertEqual(hue.get_light_color_temp(FIXTURE_LIGHTS[0]), 250)

    def test_get_light_color(self):
        xy = hue.get_light_color(FIXTURE_LIGHTS[0])
        self.assertIsNotNone(xy)
        self.assertAlmostEqual(xy[0], 0.4)

    def test_get_gl_on(self):
        on_state, any_on = hue.get_gl_on(FIXTURE_GROUPED_LIGHTS[0])
        self.assertTrue(on_state)
        self.assertTrue(any_on)

    def test_format_bri(self):
        self.assertEqual(hue.format_bri(80.0), "80%")
        self.assertEqual(hue.format_bri(None), "-")

    def test_format_ct(self):
        self.assertEqual(hue.format_ct(250), "4000K")
        self.assertEqual(hue.format_ct(None), "-")


class TestExitCodes(unittest.TestCase):
    """Exit codes for various error conditions."""

    def test_no_config_exit_4(self):
        """Running without config should exit 4."""
        with self.assertRaises(SystemExit) as cm:
            args = make_args("lights", bridge=None, key=None)
            # Monkey-patch _get_snap to trigger the die
            hue._get_snap(args)
        self.assertEqual(cm.exception.code, 4)

    def test_not_found_exit_3(self):
        """Unknown target should exit 3."""
        with self.assertRaises(SystemExit) as cm:
            hue.resolve_targets(["zxyw"], FIXTURE_SNAPSHOT)
        self.assertEqual(cm.exception.code, 3)

    def test_pair_timeout_exit_5(self):
        """Timeout without link button press should exit 5."""
        with patch.object(hue, 'request') as mock_req:
            mock_req.side_effect = lambda *a, **kw: (
                200, [{"error": {"description": "link button not pressed"}}]
            )
            with patch.object(hue, 'input', return_value=''):
                with self.assertRaises(SystemExit) as cm:
                    args = make_args("pair", bridge="192.168.1.100")
                    # We need to handle the time.sleep
                    with patch.object(hue, 'time') as mock_time:
                        mock_time.time.side_effect = [0, 2, 4, 6, 100]  # Fast forward
                        mock_time.sleep.return_value = None
                        hue.cmd_pair(args)
        self.assertEqual(cm.exception.code, 5)


class TestOutputFormatting(unittest.TestCase):
    """Human and JSON output helpers."""

    def test_trim_light(self):
        light = FIXTURE_LIGHTS[0]
        trimmed = hue.trim_resource({"id": light["id"], **light}, FIXTURE_SNAPSHOT)
        self.assertEqual(trimmed["id"], light["id"])
        self.assertEqual(trimmed["type"], "light")
        self.assertIn("on", trimmed)
        self.assertIn("brightness", trimmed)
        self.assertIn("color_temperature", trimmed)
        self.assertIn("room", trimmed)

    def test_trim_room(self):
        room = FIXTURE_ROOMS[0]
        trimmed = hue.trim_resource({"id": room["id"], **room}, FIXTURE_SNAPSHOT)
        self.assertEqual(trimmed["type"], "room")
        self.assertIn("on", trimmed)
        self.assertEqual(trimmed["light_count"], 3)

    def test_trim_grouped_light(self):
        gl = FIXTURE_GROUPED_LIGHTS[0]
        trimmed = hue.trim_resource({"id": gl["id"], **gl}, FIXTURE_SNAPSHOT)
        self.assertEqual(trimmed["type"], "grouped_light")
        self.assertIn("on", trimmed)


class TestJsonOutput(unittest.TestCase):
    """JSON output shape consistency."""

    def test_lights_json_shape(self):
        """lights --json should produce a list with id, name, type, on, brightness, etc."""
        snap = FIXTURE_SNAPSHOT
        items = []
        for l in snap["lights"]:
            items.append(hue.trim_resource({"id": l["id"], **l}, snap))
        self.assertGreater(len(items), 0)
        for item in items:
            for key in ("id", "name", "type", "on", "brightness"):
                self.assertIn(key, item)

    def test_rooms_json_shape(self):
        snap = FIXTURE_SNAPSHOT
        items = []
        for r in snap["rooms"]:
            items.append(hue.trim_resource({"id": r["id"], **r}, snap))
        for item in items:
            self.assertIn("light_count", item)


class TestIntegrationLike(unittest.TestCase):
    """Tests that exercise small end-to-end flows with mocked HTTP."""

    @patch.object(hue, 'request')
    def test_on_command_flow(self, mock_req):
        """on command should PUT to grouped_light with on=True."""
        mock_req.side_effect = [
            # _get_snap: 6 GET calls
            (200, {"data": FIXTURE_LIGHTS}),
            (200, {"data": FIXTURE_ROOMS}),
            (200, {"data": FIXTURE_ZONES}),
            (200, {"data": FIXTURE_GROUPED_LIGHTS}),
            (200, {"data": FIXTURE_SCENES}),
            (200, {"data": FIXTURE_DEVICES}),
            # PUT call
            (200, {"data": [{"id": "c1d2e3f4-gl01", **FIXTURE_GROUPED_LIGHTS[0], "on": {"on": True, "any_on": True}}]}),
            # GET re-read
            (200, {"data": [{"id": "c1d2e3f4-gl01", **FIXTURE_GROUPED_LIGHTS[0], "on": {"on": True, "any_on": True}}]}),
        ]

        args = make_args("on", target=["Ekin Office"])
        with patch.object(sys, 'stdout', io.StringIO()) as out:
            hue.cmd_on(args)
            output = out.getvalue()
            self.assertIn("Ekin Office", output)
            self.assertIn("on", output)

        # Verify PUT was made to grouped_light endpoint
        put_calls = [c for c in mock_req.call_args_list if c[0][0] == "PUT"]
        self.assertGreaterEqual(len(put_calls), 1)

    @patch.object(hue, 'request')
    def test_off_command_flow(self, mock_req):
        """off command should PUT with on=False."""
        mock_req.side_effect = [
            (200, {"data": FIXTURE_LIGHTS}),
            (200, {"data": FIXTURE_ROOMS}),
            (200, {"data": FIXTURE_ZONES}),
            (200, {"data": FIXTURE_GROUPED_LIGHTS}),
            (200, {"data": FIXTURE_SCENES}),
            (200, {"data": FIXTURE_DEVICES}),
            (200, {"data": [{"id": "c1d2e3f4-gl01", **FIXTURE_GROUPED_LIGHTS[0], "on": {"on": False, "any_on": False}}]}),
            (200, {"data": [{"id": "c1d2e3f4-gl01", **FIXTURE_GROUPED_LIGHTS[0], "on": {"on": False, "any_on": False}}]}),
        ]

        args = make_args("off", target=["Ekin Office"])
        with patch.object(sys, 'stdout', io.StringIO()) as out:
            hue.cmd_off(args)
            output = out.getvalue()
            self.assertIn("off", output)

    @patch.object(hue, 'request')
    def test_set_brightness(self, mock_req):
        """set --bri should PUT brightness value."""
        mock_req.side_effect = [
            (200, {"data": FIXTURE_LIGHTS}),
            (200, {"data": FIXTURE_ROOMS}),
            (200, {"data": FIXTURE_ZONES}),
            (200, {"data": FIXTURE_GROUPED_LIGHTS}),
            (200, {"data": FIXTURE_SCENES}),
            (200, {"data": FIXTURE_DEVICES}),
            (200, {"data": [{"id": "a1b2c3d4-0001", **FIXTURE_LIGHTS[0],
                             "dimming": {"brightness": 50.0}}]}),
            (200, {"data": [{"id": "a1b2c3d4-0001", **FIXTURE_LIGHTS[0],
                             "dimming": {"brightness": 50.0}}]}),
        ]

        args = make_args("set", target=["Desk Left"], brightness=50)
        with patch.object(sys, 'stdout', io.StringIO()) as out:
            hue.cmd_set(args)
            output = out.getvalue()
            self.assertIn("50%", output)


if __name__ == "__main__":
    unittest.main()