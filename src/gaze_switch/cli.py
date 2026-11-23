import argparse
import sys

from . import __version__
from .calibration import run_calibration
from .config import Config, config_dir, data_dir
from .daemon import Daemon
from .monitors import detect_backend, get_monitors


def _cmd_monitors(_args) -> int:
    backend = detect_backend()
    print(f"session backend: {backend}")
    for monitor in get_monitors():
        flag = " (focused/primary)" if monitor.primary else ""
        print(
            f"{monitor.name}: {monitor.width}x{monitor.height} "
            f"at {monitor.x},{monitor.y}{flag}"
        )
    return 0


def _cmd_calibrate(_args) -> int:
    config = Config.load()
    monitors = get_monitors()
    if len(monitors) < 2:
        print("gaze-switch needs at least two monitors to be useful", file=sys.stderr)
        return 1
    run_calibration(monitors, config)
    return 0


def _cmd_run(args) -> int:
    config = Config.load()
    daemon = Daemon(config, dry_run=args.dry_run)
    print(
        f"gaze-switch running on {len(daemon.monitors)} monitors "
        f"via {daemon.switcher.name}; Ctrl+C to stop"
    )
    daemon.run()
    return 0


def _cmd_paths(_args) -> int:
    print(f"config: {config_dir()}")
    print(f"data:   {data_dir()}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="gaze-switch",
        description="Look at a monitor, keyboard focus follows.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("monitors", help="list connected monitors and the session backend")
    sub.add_parser("calibrate", help="record where you look for each monitor")
    run_parser = sub.add_parser("run", help="run the focus-switching daemon")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print switch decisions without moving focus",
    )
    sub.add_parser("paths", help="show config and data directories")

    args = parser.parse_args(argv)
    handlers = {
        "monitors": _cmd_monitors,
        "calibrate": _cmd_calibrate,
        "run": _cmd_run,
        "paths": _cmd_paths,
    }
    try:
        return handlers[args.command](args)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
