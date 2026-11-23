import json
import subprocess

from .monitors import detect_backend


def _run(args: list, check: bool = False) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}")
    return result.stdout.strip()


class X11Switcher:
    name = "x11"

    def active_window(self):
        out = _run(["xdotool", "getactivewindow"])
        return out or None

    def window_monitor(self, window_id, monitors):
        out = _run(["xdotool", "getwindowgeometry", "--shell", window_id])
        values = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = int(value)
        if "X" not in values or "Y" not in values:
            return None
        cx = values["X"] + values.get("WIDTH", 0) // 2
        cy = values["Y"] + values.get("HEIGHT", 0) // 2
        for monitor in monitors:
            if monitor.contains(cx, cy):
                return monitor.name
        return None

    def focus_window(self, window_id) -> None:
        _run(["xdotool", "windowactivate", "--sync", window_id])

    def pointer_location(self) -> tuple:
        out = _run(["xdotool", "getmouselocation", "--shell"])
        values = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = int(value)
        return (values.get("X", 0), values.get("Y", 0))

    def move_pointer(self, x: int, y: int) -> None:
        _run(["xdotool", "mousemove", "--sync", str(x), str(y)])


class HyprlandSwitcher:
    name = "hyprland"

    def _clients(self) -> list:
        return json.loads(_run(["hyprctl", "clients", "-j"]) or "[]")

    def active_window(self):
        out = _run(["hyprctl", "activewindow", "-j"])
        if not out:
            return None
        data = json.loads(out)
        return data.get("address")

    def window_monitor(self, window_id, monitors):
        for client in self._clients():
            if client.get("address") == window_id:
                for monitor in monitors:
                    if monitor.name == client.get("monitor"):
                        return monitor.name
        return None

    def focus_window(self, window_id) -> None:
        _run(["hyprctl", "dispatch", "focuswindow", f"address:{window_id}"])

    def focus_monitor(self, monitor_name: str) -> None:
        _run(["hyprctl", "dispatch", "focusmonitor", monitor_name])

    def pointer_location(self) -> tuple:
        out = _run(["hyprctl", "cursorpos"])
        parts = out.replace(",", " ").split()
        if len(parts) != 2:
            return (0, 0)
        return (int(float(parts[0])), int(float(parts[1])))

    def move_pointer(self, x: int, y: int) -> None:
        _run(["hyprctl", "dispatch", "movecursor", str(x), str(y)])


def make_switcher(backend: str = None):
    backend = backend or detect_backend()
    if backend == "hyprland":
        return HyprlandSwitcher()
    if backend == "x11":
        return X11Switcher()
    raise RuntimeError(
        f"no switch backend for session '{backend}'; X11 and Hyprland are supported"
    )
