from typing import Iterator

from library import *


def get_closest_unit(units: Iterator[Unit], position: Point2D):
    """Get closest unit in ist to position."""
    distance = 0
    closest = None
    for unit in units:
        if not closest or distance > unit.position.dist(position):
            distance = unit.position.dist(position)
            closest = unit
    return closest
