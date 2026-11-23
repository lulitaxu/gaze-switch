# gaze-switch

Look at a monitor. Keyboard focus follows.

gaze-switch watches your head direction through your webcam, works out which
monitor you are looking at, and moves keyboard focus (and optionally the
pointer) to that screen. No clicking, no keyboard shortcut, no reaching for
the mouse just to type in the window you are already looking at.

Built for Linux. The commercial equivalents ship for macOS and Windows only.

## How it works

1. **Head pose, not eye tracking.** MediaPipe Face Mesh finds your face and
   OpenCV `solvePnP` turns the landmarks into a yaw/pitch direction. Head
   direction is far more reliable than consumer-webcam eyeball tracking, and
   it is what actually changes when you turn to another monitor.
2. **Calibration over guessing.** You look at each monitor once, for about
   two seconds. gaze-switch records your personal yaw/pitch center per
   monitor, so seating position, camera placement and monitor angles are all
   baked into the profile instead of assumed.
3. **Deliberate switching.** A switch needs the new monitor to win by a
   configurable angular margin and stay the winner for a dwell period
   (default 450 ms). Glances at a notification do not steal your keyboard.
4. **Focus memory.** The daemon remembers the last active window on each
   monitor and refocuses exactly that window. The pointer returns to where
   you left it on that screen, not just the center.

Everything runs on your machine. Frames are processed in memory and never
stored, recorded or sent anywhere.

## Requirements

- Linux with **X11** or **Hyprland** (other Wayland compositors restrict
  programmatic focus and pointer control; see Limitations)
- 2 or more monitors
- A webcam
- Python 3.10+
- X11: `xdotool` and `xrandr` on PATH
- Hyprland: `hyprctl` on PATH (ships with Hyprland)

## Install

```sh
pipx install ./gaze-switch        # from a clone of this repo
# or
pip install --user ./gaze-switch
```

## Usage

```sh
gaze-switch monitors     # check that your monitors are detected
gaze-switch calibrate    # look at each monitor when prompted
gaze-switch run          # start switching
gaze-switch run --dry-run   # print decisions without moving focus
```

Run it at login with the bundled user service:

```sh
mkdir -p ~/.config/systemd/user
cp systemd/gaze-switch.service ~/.config/systemd/user/
systemctl --user enable --now gaze-switch
```

## Configuration

`~/.config/gaze-switch/config.json` (created on first save, all keys optional):

| Key | Default | Meaning |
| --- | --- | --- |
| `camera_index` | `0` | webcam device index |
| `dwell_ms` | `450` | how long a look must hold before focus switches |
| `margin_deg` | `4.0` | how decisively a monitor must win before it is a candidate |
| `smoothing` | `0.35` | pose smoothing factor, higher is snappier and noisier |
| `move_pointer` | `true` | move the pointer along with focus |
| `restore_pointer` | `true` | return the pointer to its last spot per monitor |
| `sample_fps` | `15` | camera sampling rate |

Calibration lives in `~/.local/share/gaze-switch/calibration.json`. Re-run
`gaze-switch calibrate` after moving your camera or monitors.

## Limitations

- Generic Wayland compositors (GNOME, KDE on Wayland) do not let a normal
  client move focus or warp the pointer, so they are not supported yet.
  Hyprland works because `hyprctl` exposes both.
- Head pose follows where your face points. Reading a side monitor with your
  eyes only, face forward, will not (and should not) switch.
- Low light hurts face detection. If switches get unreliable at night, it is
  the camera, not the math.

## Development

```sh
pip install -e ".[dev]"
pytest
```

Layout: `monitors.py` detects displays, `pose.py` estimates head direction,
`mapping.py` is the pure decision logic, `switcher.py` holds the X11 and
Hyprland backends, `daemon.py` runs the loop.

## License

MIT, see `LICENSE`.
