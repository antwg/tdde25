from library import *
from math import sqrt
from typing import Union, List, Callable

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

grounded_command_center_TYPEID = [UNIT_TYPEID.TERRAN_COMMANDCENTER,
                                  UNIT_TYPEID.TERRAN_ORBITALCOMMAND,
                                  UNIT_TYPEID.TERRAN_PLANETARYFORTRESS]

supply_TYPEID = [UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
                 UNIT_TYPEID.TERRAN_SUPPLYDEPOTLOWERED]

on_target_builds_TYPEID = [
    UNIT_TYPEID.TERRAN_REFINERY,
    UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.TERRAN_TECHLAB,
    UNIT_TYPEID.TERRAN_REACTOR
]


# Get distance from this point to the next
Point2D.distance = lambda self, other: sqrt((self.x - other.x)**2
                                            + (self.y - other.y)**2)
# Translate a point to Integers point
Point2D.to_i = lambda self: Point2DI(int(self.x), int(self.y))
# Translate a Integer point to regular
Point2DI.to_f = lambda self: Point2D(self.x, self.y)


def find_unit_with_id(bot: IDABot, unit_id: int):
    for unit in bot.get_my_units():
        if unit.id == unit_id:
            return unit
    return None


def find_my_units_with_type(searched_type: UNIT_TYPEID, bot: IDABot):
    found_units = []
    for unit in bot.get_my_units():
        if unit.unit_typr.unit_typeid == searched_type:
            found_units.append(unit)
    return found_units


def find_my_units_with_types(searched_types: List[UNIT_TYPEID], bot: IDABot):
    found_units = []
    for unit in bot.get_my_units():
        if unit.unit_type.unit_typeid in searched_types:
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


def find_closest_unit_to(units: List[Unit], point: Point2D):
    closest = 0
    found = None
    for unit in units:
        if not found or closest > unit.position.distance(point):
            closest = unit.position.distance(point)
            found = unit
    return found


def find_closest_mineralfield(bot: IDABot, point: Point2D):
    return find_closest_unit_to(find_all_mineralfields(bot), point)


def find_base_location_on_point(bot: IDABot, point0: Union[Point2D, Point2DI]):
    point = point0 if isinstance(point0, Point2D) else point0.to_f

    for base_location in bot.base_location_manager.base_locations:
        if base_location.contains_position(point):
            return base_location
    return None


def find_units_base_location(bot: IDABot, unit: Unit):
    return find_base_location_on_point(bot, unit.position)


def get_provided_supply(bot: IDABot):
    supply = 0
    for unit in find_my_units_with_types(supply_TYPEID, bot):
        supply += unit.supply_provided
    return supply


# TODO: Finish function
def get_closest_target():
    pass


def produce_unit(bot: IDABot, unit: Unit, ut: UnitType, where_func: Callable) -> bool:
    where = where_func(bot, unit, ut)
    if not where:
        unit.train(ut)
        return True
    elif isinstance(where, Unit):
        unit.build_target(ut, where)
        return True
    elif isinstance(where, Point2DI):
        unit.build(ut, where)
        return True
    elif isinstance(where, Point2D):
        unit.build(ut, where.to_i)
        return True
    else:
        return False
