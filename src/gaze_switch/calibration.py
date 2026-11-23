import statistics
import time

import cv2

from .config import Calibration, Config
from .monitors import Monitor
from .pose import HeadPoseTracker


def _collect(tracker, camera, seconds: float = 1.6, fps: int = 15) -> tuple:
    samples = []
    frames = max(1, int(seconds * fps))
    for _ in range(frames):
        ok, frame = camera.read()
        if not ok:
            continue
        pose = tracker.estimate(frame)
        if pose is not None:
            samples.append(pose)
        time.sleep(1.0 / fps)
    if len(samples) < 5:
        return None
    return (
        statistics.median(s[0] for s in samples),
        statistics.median(s[1] for s in samples),
    )


def run_calibration(monitors: list, config: Config) -> Calibration:
    camera = cv2.VideoCapture(config.camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"could not open camera {config.camera_index}")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    tracker = HeadPoseTracker(config.min_face_confidence)
    calibration = Calibration()
    try:
        for monitor in monitors:
            input(
                f"Look at the center of monitor {monitor.name} "
                f"({monitor.width}x{monitor.height} at {monitor.x},{monitor.y}), "
                "then press Enter..."
            )
            center = _collect(tracker, camera, fps=config.sample_fps)
            if center is None:
                raise RuntimeError(
                    f"no face detected while calibrating {monitor.name}; "
                    "check lighting and camera angle, then retry"
                )
            calibration.centers[monitor.name] = center
            print(f"  recorded yaw {center[0]:.1f}, pitch {center[1]:.1f}")
    finally:
        tracker.close()
        camera.release()
    path = calibration.save()
    print(f"Calibration saved to {path}")
    return calibration
