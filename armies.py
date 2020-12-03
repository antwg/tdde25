from typing import Union, Sequence

from library import *

from scai_backbone import siege_tanks_TYPEIDS

from workplace import *
global bunker_marine


# ZW
class Troop:
    """A collection of military units."""
    # target: Point2D - Common target for all units in troop

    # marines: List[Unit] - All marines in this troop
    # tanks: List[Unit]   - All siege tanks in this troop
    # others: List[Unit]  - All other units in this troop

    marines_capacity: int = 8  # How many marines this troop is asking for
    tanks_capacity: int = 2    # How many tanks this troop is asking for

    # under_attack: bool  - If troop is under attack or not

    def __init__(self, position: Point2D):
        """Called when a new troop is being created. Note that no units are
        required for making a troop, rather it is why they are created.
        """
        self.target = position
        self.marines = []
        self.tanks = []
        self.others = []
        self.under_attack = False

    def get_units(self) -> List[Unit]:
        """Get all units in troop."""
        return self.marines + self.tanks + self.others

    def move_units(self, position: Point2D) -> None:
        """Moves troop and all its units to given position."""
        if self.target != position:
            for trooper in self.get_units():
                trooper.move(position)
            self.target = position

    def has_unit(self, unit: Unit) -> bool:
        """Check if troop has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    def build_bunker(self, bot: IDABot, location):  # AW
        """Builds a supply depot when necessary."""
        bunker = UnitType(UNIT_TYPEID.TERRAN_BUNKER, bot)
        workplace = closest_workplace(location)

        if can_afford(bot, bunker) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_BUNKER)\
                and bunker not in workplace.builders_targets.values():
            position = bot.building_placer.get_build_location_near(
                Point2DI(int(location.x), int(location.y)), bunker)
            worker = workplace.get_suitable_builder()
            if worker is not None:
                worker.build(bunker, position)
            else:
                self.build_bunker(bot, location)

    def add(self, units: Union[Unit, Sequence[Unit]]) -> None:
        """Adds unit(s) to troop."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
                self.marines.append(unit)
                unit.move(self.target)
            elif unit.unit_type.unit_typeid in siege_tanks_TYPEIDS:
                self.others.append(unit)
                unit.move(self.target)
            else:
                self.others.append(unit)
                unit.move(self.target)

    def remove(self, unit: Unit) -> None:
        """Handles units that are to be removed from troop."""
        if unit in self.marines:
            self.marines.remove(unit)
        elif unit in self.tanks:
            self.tanks.remove(unit)
        elif unit in self.others:
            self.others.remove(unit)

    @property
    def wants_marines(self) -> int:
        """Return required amount of marines to satisfy capacity."""
        return max(self.marines_capacity - len(self.marines), 0) \
            if not self.under_attack else 0

    @property
    def wants_tanks(self) -> int:
        """Return required amount of tanks to satisfy capacity."""
        return max(self.tanks_capacity - len(self.tanks), 0) \
            if not self.under_attack else 0

    @property
    def has_enough(self) -> bool:
        """Check if the capacity is satisfied for all unit types."""
        return 0 >= self.wants_marines and 0 >= self.wants_tanks


# All troops!
troops = []


# ZW
def create_troop(point: Point2D):
    """Create a new troop with given target."""
    troops.append(Troop(point))


# ZW
def marine_seeks_troop(position: Point2D) -> Troop:
    """Find closest troop requiring a marine most."""
    closest = [None, None]
    distance = [0, 0]
    for troop in troops:
        if troop.wants_marines > 0:
            if not closest[0] or troop.target.dist(position) / troop.wants_marines < distance[0]:
                closest[0] = troop
                distance[0] = troop.target.dist(position)
        else:
            if not closest[1] or troop.target.dist(position) < distance[1]:
                closest[1] = troop
                distance[1] = troop.target.dist(position)

    return closest[0] if closest[0] else closest[1]


# ZW
def tank_seeks_troop(position: Point2D) -> Troop:
    """Find closest troop requiring a tank most."""
    closest = None
    distance = 0
    for troop in troops:
        if not closest or troop.target.dist(position) / max(troop.wants_tanks, 0.1) < distance:
            closest = troop
            distance = troop.target.dist(position)
    return closest


# ZW
def find_unit_troop(unit: Unit) -> Union[Troop, None]:
    for troop in troops:
        if troop.has_unit(unit):
            return troop
    return None

def closest_troop(pos: Point2D):
    """Checks the closest troop to a position"""
    closest = None
    distance = 0
    for troop in troops:
        if not closest or distance > troop.target.dist(pos):
            closest = troop
            distance = troop.target.dist(pos)

    return closest
