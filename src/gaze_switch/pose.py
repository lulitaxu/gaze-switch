import math

import cv2
import numpy as np

_MODEL_POINTS = np.array(
    [
        (0.0, 0.0, 0.0),
        (0.0, -63.6, -12.5),
        (-43.3, 32.7, -26.0),
        (43.3, 32.7, -26.0),
        (-28.9, -28.9, -24.1),
        (28.9, -28.9, -24.1),
    ],
    dtype=np.float64,
)

_LANDMARK_IDS = (1, 199, 33, 263, 61, 291)


class HeadPoseTracker:
    def __init__(self, min_confidence: float = 0.5):
        import mediapipe as mp

        self._mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
        )

    def estimate(self, frame) -> tuple:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._mesh.process(rgb)
        if not result.multi_face_landmarks:
            return None
        landmarks = result.multi_face_landmarks[0].landmark
        image_points = np.array(
            [(landmarks[i].x * w, landmarks[i].y * h) for i in _LANDMARK_IDS],
            dtype=np.float64,
        )
        focal = float(w)
        camera_matrix = np.array(
            [[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]], dtype=np.float64
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)
        ok, rvec, _ = cv2.solvePnP(
            _MODEL_POINTS, image_points, camera_matrix, dist_coeffs
        )
        if not ok:
            return None
        rmat, _ = cv2.Rodrigues(rvec)
        angles, *_ = cv2.RQDecomp3x3(rmat)
        pitch, yaw, _roll = (float(a) for a in angles)
        return (yaw, pitch)

    def close(self) -> None:
        self._mesh.close()


def smooth(previous, current, alpha: float) -> tuple:
    if previous is None:
        return current
    return (
        previous[0] + alpha * (current[0] - previous[0]),
        previous[1] + alpha * (current[1] - previous[1]),
    )


def angular_distance(a: tuple, b: tuple) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
