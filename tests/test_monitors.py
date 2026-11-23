import json

from gaze_switch.monitors import Monitor, parse_hyprland, parse_xrandr

XRANDR = """Screen 0: minimum 320 x 200, current 4480 x 1440, maximum 16384 x 16384
eDP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 344mm x 194mm
HDMI-1 connected 2560x1440+1920+0 (normal left inverted right x axis y axis) 597mm x 336mm
DP-1 disconnected (normal left inverted right x axis y axis)
"""


def test_parse_xrandr():
    monitors = parse_xrandr(XRANDR)
    assert [m.name for m in monitors] == ["eDP-1", "HDMI-1"]
    assert monitors[0].primary is True
    assert monitors[1].primary is False
    assert monitors[1].x == 1920
    assert monitors[1].center == (1920 + 1280, 720)


def test_parse_hyprland():
    payload = json.dumps(
        [
            {
                "name": "eDP-1",
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "focused": True,
                "disabled": False,
            },
            {
                "name": "HDMI-A-1",
                "x": 1920,
                "y": 0,
                "width": 2560,
                "height": 1440,
                "focused": False,
                "disabled": False,
            },
            {
                "name": "DP-2",
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "focused": False,
                "disabled": True,
            },
        ]
    )
    monitors = parse_hyprland(payload)
    assert [m.name for m in monitors] == ["eDP-1", "HDMI-A-1"]
    assert monitors[0].primary is True


def test_monitor_contains():
    monitor = Monitor("X", 100, 100, 800, 600)
    assert monitor.contains(100, 100)
    assert monitor.contains(899, 699)
    assert not monitor.contains(900, 700)
    assert not monitor.contains(99, 300)
