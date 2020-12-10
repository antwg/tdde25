from math import ceil, floor
from typing import Iterator, List, Optional, Union

from library import *

terran_buildings_ids = [
    UNIT_TYPEID.TERRAN_COMMANDCENTER, UNIT_TYPEID.TERRAN_ORBITALCOMMAND,
    UNIT_TYPEID.TERRAN_PLANETARYFORTRESS, UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
    UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.TERRAN_BARRACKS, UNIT_TYPEID.TERRAN_BUNKER,
    UNIT_TYPEID.TERRAN_ENGINEERINGBAY, UNIT_TYPEID.TERRAN_FACTORY,
    UNIT_TYPEID.TERRAN_MISSILETURRET, UNIT_TYPEID.TERRAN_SENSORTOWER,
    UNIT_TYPEID.TERRAN_GHOSTACADEMY, UNIT_TYPEID.TERRAN_ARMORY,
    UNIT_TYPEID.TERRAN_STARPORT, UNIT_TYPEID.TERRAN_FUSIONCORE,
    UNIT_TYPEID.TERRAN_TECHLAB, UNIT_TYPEID.TERRAN_REACTOR
]


def get_closest_unit(units: Iterator[Unit], position: Point2D) -> Unit:
    """Get closest unit in ist to position."""
    return get_closest([(unit.position, unit) for unit in units], position)


def get_closest(items: List[tuple], position: Point2D):
    """Get closest object in tuples to given point where the tuples first
    element is it's position and the second is the object.
    """
    distance = 0
    closest = None
    for item in items:
        if not closest or distance > position.squared_dist(item[0]):
            distance = position.squared_dist(item[0])
            if distance == 0:
                return item[1]
            closest = item[1]
    return closest


def get_geysers(bot: IDABot, base_location: BaseLocation) -> List[Unit]: #Kurssidan
    """ Given a base_location, this method will find and return a list of
        all geysers for that base """
    geysers = []
    for geyser in base_location.geysers:
        for unit in bot.get_all_units():
            if unit.unit_type.is_geyser \
                    and geyser.tile_position.x == unit.tile_position.x \
                    and geyser.tile_position.y == unit.tile_position.y:
                geysers.append(unit)
    return geysers


def get_mineral_fields(bot: IDABot, base_location: BaseLocation) -> List[Unit]: #Kurssidan
    """ Given a base_location, this method will find and return a list of
    all mineral fields (Unit) for that base """
    mineral_fields = []
    for mineral_field in base_location.mineral_fields:
        for unit in bot.get_all_units():
            if unit.unit_type.is_mineral \
                    and mineral_field.tile_position.x == unit.tile_position.x \
                    and mineral_field.tile_position.y == unit.tile_position.y:
                mineral_fields.append(unit)
    return mineral_fields


# ZW
def get_my_types_units(bot: IDABot, searched_types: List[UnitTypeID]):
    """Get all owned units with oe of the given unit types."""
    units = []
    for unit in bot.get_my_units():
        if unit.unit_type.unit_typeid in searched_types:
            units.append(unit)
    return units


# ZW
def get_my_type_units(bot: IDABot, searched_type: UnitTypeID):
    """Get all owned units with given unit type."""
    units = []
    for unit in bot.get_my_units():
        if unit.unit_type.unit_typeid == searched_type:
            units.append(unit)
    return units


# ZW
def can_afford(bot: IDABot, unit_type: UnitType) -> bool:
    """Returns whenever a unit is affordable. """
    return bot.minerals >= unit_type.mineral_price \
        and bot.gas >= unit_type.gas_price \
        and bot.max_supply - bot.current_supply \
        >= unit_type.supply_required


def get_refinery(bot: IDABot, geyser: Unit) -> Optional[Unit]:
    """
    Returns: A refinery which is on top of unit `geyser` if any, None otherwise
    """

    def squared_distance(p1: Point2D, p2: Point2D) -> float:
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    for unit in bot.get_my_units():
        if unit.unit_type.is_refinery and squared_distance(unit.position,
                                                           geyser.position) < 1:
            return unit

    return None


def currently_building(bot:IDABot, unit_type):  # AW
    """Checks if a unit is currently being built"""
    return any([not unit.is_completed for unit in
                get_my_type_units(bot, unit_type)])
