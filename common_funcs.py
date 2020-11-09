from library import *
from math import sqrt
from typing import Union, List


minerals_TYPEID = [UNIT_TYPEID.NEUTRAL_MINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_MINERALFIELD450,
                   UNIT_TYPEID.NEUTRAL_MINERALFIELD750,
                   UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_LABMINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD,
                   UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD750,
                   UNIT_TYPEID.NEUTRAL_LABMINERALFIELD750,
                   UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD750,
                   UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD750,
                   UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD750]

refineries_TYPEID = [UNIT_TYPEID.TERRAN_REFINERY,
                     UNIT_TYPEID.TERRAN_REFINERYRICH,
                     UNIT_TYPEID.AUTOMATEDREFINERY,
                     UNIT_TYPEID.INFESTEDREFINERY]


# Get distance from this point to the next
Point2D.distance = lambda self, other: sqrt((self.x - other.x)**2
                                            + (self.y - other.y)**2)
# Translate a point to Integers point
Point2D.to_i = lambda self: Point2DI(int(self.x), int(self.y))
# Translate a Integer point to regular
Point2DI.to_f = lambda self: Point2D(self.x, self.y)


def find_my_units_with_type(searched_type: UNIT_TYPEID, bot: IDABot):
    found_units = []
    for unit in bot.get_my_units():
        if unit.unit_typr.unit_typeid == searched_type:
            found_units.append(unit)
    return found_units


def find_my_units_with_types(searched_types: List[UNIT_TYPEID], bot: IDABot):
    found_units = []
    for unit in bot.get_my_units():
        if unit.unit_typr.unit_typeid in searched_types:
            found_units.append(unit)
    return found_units


def find_all_units_with_type(searched_type: UNIT_TYPEID, bot: IDABot):
    found_units = []
    for unit in bot.get_all_units():
        if unit.unit_typr.unit_typeid == searched_type:
            found_units.append(unit)
    return found_units


def find_all_mineralfields(bot: IDABot):
    found_units = []
    for unit in bot.get_all_units():
        if unit.unit_type.unit_typeid in minerals_TYPEID:
            found_units.append(unit)
    return found_units


def find_closest_mineralfield(bot: IDABot, point: Point2D):
    minerals = find_all_mineralfields(bot)

    if minerals:
        closest_mineral = minerals[0]
        closest_distance = point.distance(minerals[0].position)
        for mineral in minerals[1:]:
            if point.distance(mineral.position) < closest_distance:
                closest_distance = point.distance(mineral.position)
                closest_mineral = mineral
        return closest_mineral
    else:
        return None


def find_base_location_on_point(bot: IDABot, point0: Union[Point2D, Point2DI]):
    point = point0 if isinstance(point0, Point2D) else point0.to_f

    for base_location in bot.base_location_manager.base_locations:
        if base_location.contains_position(point):
            return base_location
    return None

