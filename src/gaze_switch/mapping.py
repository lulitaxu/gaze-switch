from .pose import angular_distance


def pick_monitor(pose: tuple, centers: dict, current: str, margin_deg: float) -> str:
    if not centers:
        return current
    ranked = sorted(centers.items(), key=lambda kv: angular_distance(pose, kv[1]))
    best_name, best_center = ranked[0]
    if best_name == current:
        return current
    if current not in centers:
        return best_name
    current_distance = angular_distance(pose, centers[current])
    best_distance = angular_distance(pose, best_center)
    if best_distance + margin_deg < current_distance:
        return best_name
    return current
