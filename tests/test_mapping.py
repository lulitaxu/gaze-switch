from gaze_switch.mapping import pick_monitor

CENTERS = {"HDMI-1": (-18.0, 2.0), "DP-1": (16.0, 1.0), "eDP-1": (0.0, 14.0)}


def test_picks_nearest_center():
    assert pick_monitor((-17.0, 3.0), CENTERS, "DP-1", 4.0) == "HDMI-1"


def test_stays_when_pose_matches_current():
    assert pick_monitor((15.0, 0.0), CENTERS, "DP-1", 4.0) == "DP-1"


def test_margin_blocks_borderline_switch():
    assert pick_monitor((2.0, 2.0), CENTERS, "DP-1", 30.0) == "DP-1"


def test_unknown_current_snaps_to_nearest():
    assert pick_monitor((0.0, 13.0), CENTERS, "UNKNOWN", 4.0) == "eDP-1"


def test_empty_centers_keeps_current():
    assert pick_monitor((0.0, 0.0), {}, "DP-1", 4.0) == "DP-1"
