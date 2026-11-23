import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "gaze-switch"


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "gaze-switch"


@dataclass
class Config:
    camera_index: int = 0
    frame_width: int = 640
    dwell_ms: int = 450
    margin_deg: float = 4.0
    smoothing: float = 0.35
    sample_fps: int = 15
    move_pointer: bool = True
    restore_pointer: bool = True
    min_face_confidence: float = 0.5

    @classmethod
    def load(cls) -> "Config":
        path = config_dir() / "config.json"
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text())
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})

    def save(self) -> Path:
        path = config_dir() / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))
        return path


@dataclass
class Calibration:
    centers: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Calibration":
        path = data_dir() / "calibration.json"
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text())
        centers = {k: tuple(v) for k, v in raw.get("centers", {}).items()}
        return cls(centers=centers)

    def save(self) -> Path:
        path = data_dir() / "calibration.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"centers": self.centers}, indent=2))
        return path
