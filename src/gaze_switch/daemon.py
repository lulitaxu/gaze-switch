import signal
import time

import cv2

from .config import Calibration, Config
from .mapping import pick_monitor
from .monitors import Monitor, get_monitors
from .pose import HeadPoseTracker, smooth
from .switcher import make_switcher


class Daemon:
    def __init__(self, config: Config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.monitors = get_monitors()
        self.by_name = {m.name: m for m in self.monitors}
        calibration = Calibration.load()
        if not calibration.centers:
            raise RuntimeError("no calibration found; run `gaze-switch calibrate` first")
        self.centers = {
            name: center
            for name, center in calibration.centers.items()
            if name in self.by_name
        }
        if not self.centers:
            raise RuntimeError("calibration does not match any connected monitor")
        self.switcher = make_switcher()
        self.last_window = {}
        self.pointer_memory = {}
        self.current = None
        self.candidate = None
        self.candidate_since = 0.0
        self.pose = None
        self.running = False

    def _track_active_window(self) -> None:
        window = self.switcher.active_window()
        if not window:
            return
        monitor = self.switcher.window_monitor(window, self.monitors)
        if monitor:
            self.last_window[monitor] = window
            self.current = monitor

    def _switch_to(self, target_name: str) -> None:
        target = self.by_name[target_name]
        if self.config.move_pointer and self.current in self.by_name:
            self.pointer_memory[self.current] = self.switcher.pointer_location()
        if self.dry_run:
            print(f"would switch focus to {target_name}")
            self.current = target_name
            return
        window = self.last_window.get(target_name)
        if window:
            self.switcher.focus_window(window)
        elif hasattr(self.switcher, "focus_monitor"):
            self.switcher.focus_monitor(target_name)
        if self.config.move_pointer:
            if self.config.restore_pointer and target_name in self.pointer_memory:
                x, y = self.pointer_memory[target_name]
            else:
                x, y = target.center
            self.switcher.move_pointer(x, y)
        self.current = target_name

    def step(self, tracker, camera) -> None:
        ok, frame = camera.read()
        if not ok:
            return
        raw = tracker.estimate(frame)
        if raw is None:
            return
        self.pose = smooth(self.pose, raw, self.config.smoothing)
        self._track_active_window()
        if self.current is None:
            return
        target = pick_monitor(
            self.pose, self.centers, self.current, self.config.margin_deg
        )
        now = time.monotonic()
        if target == self.current:
            self.candidate = None
            return
        if target != self.candidate:
            self.candidate = target
            self.candidate_since = now
            return
        if (now - self.candidate_since) * 1000 >= self.config.dwell_ms:
            self._switch_to(target)
            self.candidate = None

    def run(self) -> None:
        camera = cv2.VideoCapture(self.config.camera_index)
        if not camera.isOpened():
            raise RuntimeError(f"could not open camera {self.config.camera_index}")
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        tracker = HeadPoseTracker(self.config.min_face_confidence)
        self.running = True

        def stop(_signum, _frame):
            self.running = False

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        interval = 1.0 / max(1, self.config.sample_fps)
        try:
            while self.running:
                started = time.monotonic()
                self.step(tracker, camera)
                elapsed = time.monotonic() - started
                if elapsed < interval:
                    time.sleep(interval - elapsed)
        finally:
            tracker.close()
            camera.release()
