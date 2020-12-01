from typing import Iterator, List, Optional

from library import *

terran_buildings_ids = [
    UNIT_TYPEID.TERRAN_COMMANDCENTER, UNIT_TYPEID.TERRAN_ORBITALCOMMAND,
    UNIT_TYPEID.TERRAN_PLANETARYFORTRESS, UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
    UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.TERRAN_BARRACKS, UNIT_TYPEID.TERRAN_BARRACKSREACTOR,
    UNIT_TYPEID.TERRAN_BARRACKSREACTOR, UNIT_TYPEID.TERRAN_BUNKER,
    UNIT_TYPEID.TERRAN_ENGINEERINGBAY, UNIT_TYPEID.TERRAN_FACTORY,
    UNIT_TYPEID.TERRAN_FACTORYREACTOR, UNIT_TYPEID.TERRAN_FACTORYTECHLAB,
    UNIT_TYPEID.TERRAN_MISSILETURRET, UNIT_TYPEID.TERRAN_SENSORTOWER,
    UNIT_TYPEID.TERRAN_GHOSTACADEMY, UNIT_TYPEID.TERRAN_ARMORY,
    UNIT_TYPEID.TERRAN_STARPORT, UNIT_TYPEID.TERRAN_STARPORTREACTOR,
    UNIT_TYPEID.TERRAN_STARPORTTECHLAB, UNIT_TYPEID.TERRAN_FUSIONCORE,
    UNIT_TYPEID.TERRAN_TECHLAB, UNIT_TYPEID.TERRAN_REACTOR
]


def get_closest_unit(units: Iterator[Unit], position: Point2D):
    """Get closest unit in ist to position."""
    distance = 0
    closest = None
    for unit in units:
        if not closest or distance > unit.position.dist(position):
            distance = unit.position.dist(position)
            closest = unit
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


# DP
def get_start_base_minerals(bot: IDABot):
    """Returns list of minerals (units) within starting base"""
    # Base location can be changed later on, making it work with expansions
    start_location = bot.base_location_manager \
        .get_player_starting_base_location(PLAYER_SELF)
    return start_location.minerals


# ZW
def get_my_type_units(bot: IDABot, searched_type: UnitTypeID):
    """Get all owned units with given unit type."""
    units = []
    for unit in bot.get_my_units():
        if unit.unit_type.unit_typeid == searched_type:
            units.append(unit)
    return units


# DP
def get_my_geysers(bot: IDABot):
    """Returns list of all geysers player has access to"""
    base_locations = bot.base_location_manager.get_occupied_base_locations(PLAYER_SELF)
    geysers_base_list = []
    gey_list = []
    for base in base_locations:
        geysers_base_list.append(base.geysers)
        for geysers in geysers_base_list:
            gey_list += geysers

    return gey_list


# DP
def get_refineries_base(bot: IDABot, base_location: BaseLocation):
    """Returns list of refineries in base location"""
    ref = []
    for geyser in get_geysers(bot, base_location):
        if get_refinery(bot, geyser) is not None:
            ref.append(get_refinery(bot, geyser))
    return ref


# ZW
def can_afford(bot: IDABot, unit_type: UnitType) -> bool:
    """Returns whenever a unit is affordable. """
    return bot.minerals >= unit_type.mineral_price \
        and bot.gas >= unit_type.gas_price \
        and bot.max_supply - bot.current_supply \
        >= unit_type.supply_required


def get_my_workers(bot: IDABot):
    """Makes a list of workers"""
    workers = []
    for unit in bot.get_my_units():
        if unit.unit_type.is_worker:
            workers.append(unit)
    return workers


def get_my_refineries(bot: IDABot):
    """ Returns a list of all refineries (list of Unit) """
    refineries = []
    for unit in bot.get_my_units():
        if unit.unit_type.is_refinery:
            refineries.append(unit)
    return refineries


def get_refinery(bot: IDABot, geyser: Unit) -> Optional[Unit]:
    """
    Returns: A refinery which is on top of unit `geyser` if any, None otherwise
    """

    def squared_distance(p1: Point2D, p2: Point2D) -> float:
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    for unit in bot.get_my_units():
        if unit.unit_type.is_refinery and squared_distance(unit.position, geyser.position) < 1:
            return unit

    return None


def currently_building(bot: IDABot, unit_type): #AW
    """"Checks if a unit is being built"""
    value = 0
    for unit in bot.get_my_units():
        if unit.unit_type.unit_typeid == unit_type\
                and not unit.is_completed:
            value = value + 1
    if value >= 1:
        return True
    else:
        return False


def builder_currently_building(bot: IDABot, builder):
    """return true if builder is building, false otherwise."""
    for buildingID in terran_buildings_ids:
        if builder.is_constructing(UnitType(buildingID, bot)):
            return True
    return False


def currently_building(bot:IDABot, unit_type): #AW
    """"Checks if a unit is currently being built"""
    return any([unit.build_percentage < 1 for unit in
                get_my_type_units(bot, unit_type)])