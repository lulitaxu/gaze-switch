import json
import os
import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Monitor:
    name: str
    x: int
    y: int
    width: int
    height: int
    primary: bool = False

    @property
    def center(self) -> tuple:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


def detect_backend() -> str:
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


_XRANDR_RE = re.compile(
    r"^(?P<name>\S+) connected (?P<primary>primary )?"
    r"(?P<w>\d+)x(?P<h>\d+)\+(?P<x>-?\d+)\+(?P<y>-?\d+)"
)


def parse_xrandr(text: str) -> list:
    monitors = []
    for line in text.splitlines():
        m = _XRANDR_RE.match(line.strip())
        if not m:
            continue
        monitors.append(
            Monitor(
                name=m.group("name"),
                x=int(m.group("x")),
                y=int(m.group("y")),
                width=int(m.group("w")),
                height=int(m.group("h")),
                primary=bool(m.group("primary")),
            )
        )
    return monitors


def parse_hyprland(text: str) -> list:
    monitors = []
    for entry in json.loads(text):
        if entry.get("disabled"):
            continue
        monitors.append(
            Monitor(
                name=entry["name"],
                x=int(entry["x"]),
                y=int(entry["y"]),
                width=int(entry["width"]),
                height=int(entry["height"]),
                primary=bool(entry.get("focused")),
            )
        )
    return monitors


def _run(args: list) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def get_monitors(backend: str = None) -> list:
    backend = backend or detect_backend()
    if backend == "hyprland":
        return parse_hyprland(_run(["hyprctl", "monitors", "-j"]))
    if backend in ("x11", "wayland"):
        return parse_xrandr(_run(["xrandr", "--query"]))
    raise RuntimeError(f"unsupported session backend: {backend}")
