from typing import Union, Sequence

from library import *

from scai_backbone import siege_tanks_TYPEIDS

from workplace import *
global bunker_marine


# ZW
class Troop:
    """A collection of military units."""
    # __target: Point2D  - Common target for all units in troop

    # marines: List[Unit] - All marines in this troop
    # tanks: List[Unit]   - All siege tanks in this troop
    # bunkers: Dict[Unit, List[Unit]]  - All bunkers in this troop and the marines within
    # others: List[Unit]  - All other units in this troop

    # reached_target: List[Unit]  - All units that have reached target

    marines_capacity: int = 8  # How many marines this troop is asking for
    tanks_capacity: int = 2    # How many tanks this troop is asking for

    target_radius: int = 7  # How close a unit must be to a target to be there

    # tanks_siege: List[Unit]   - All siege tanks in siegemode in this troop

    # __order: Callable  - A function that moves unit as demanded
    # under_attack: bool  - If troop is under attack or not
    # is_attackers: bool  - If troop is attacking or not

    # ---------- EVENTS ----------
    # These are functions triggered by different events. Most are
    # triggered by MyAgent

    def __init__(self, position: Point2D, is_attackers: bool = False):
        """Called when a new troop is being created. Note that no units are
        required for making a troop, rather it is why they need to be created.
        """
        self.__target = None
        self.__order = self.__march_order
        self.marines = []
        self.tanks = []
        self.tanks_siege = []
        self.bunkers = {}
        self.others = []
        self.not_reached_target = []
        self.under_attack = False
        self.is_attackers = is_attackers

        if is_attackers:
            self.marines_capacity = 12
            self.tanks_capacity = 4

        self.set_target(position)

    def on_step(self, bot: IDABot):
        """Called each on_step() of IDABot."""
        if self.under_attack:
            pass
        elif not self.is_attackers:
            if not self.bunkers.keys():
                self.build_bunker(bot, self.target_pos)

    def on_idle(self, unit: Unit, bot: IDABot):
        """Called each time a member is idle."""
        if unit in self.not_reached_target:
            if self.nearby_target(unit):
                self.on_member_reach_target(unit)
                self.not_reached_target.remove(unit)
            elif unit in self.tanks_siege:
                # TODO: HAVE SIEGE TANKS UNMORPH
                # unit.ability(ABILITY_ID.MORPH_UNSIEGE)
                self.tanks_siege.remove(unit)
            else:
                self.unit_execute_order(unit)

    def on_member_reach_target(self, unit: Unit):
        """A member reaches target for first time."""
        if unit in self.tanks and unit not in self.tanks_siege:
            # TODO: HAVE SIEGE TANKS MORPH
            # unit.ability(ABILITY_ID.MORPH_SIEGEMODE)
            self.tanks_siege.append(unit)
        elif unit in self.marines:
            for bunker, occupants in self.bunkers.items():
                if len(occupants) < 4:
                    unit.right_click(bunker)
                    self.bunkers[bunker].append(unit)

    # --------- ORDERS ---------
    # Handles how units advance to target and how the execution of it.

    def __march_order(self, unit: Unit) -> None:
        """Have a member attack given position."""
        unit.attack_move(self.__target)

    def march_units(self, position: Point2D) -> None:
        """Have troop and all its units attack given position."""
        self.__order = self.__march_order
        self.set_target(position)
        self.all_execute_orders()

    def __move_order(self, unit: Unit) -> None:
        """Moves a unit to given position."""
        unit.move(self.__target)

    def move_units(self, position: Point2D) -> None:
        """Moves troop and all its units to given position."""
        self.__order = self.__move_order
        self.set_target(position)
        self.all_execute_orders()

    def __attack_order(self, unit: Unit) -> None:
        """Have a unit attack target."""
        unit.attack_unit(self.__target)

    def attack_units(self, target: Unit) -> None:
        """Have all units attack given unit."""
        self.__order = self.__attack_order
        self.set_target(target)
        self.all_execute_orders()

    def all_execute_orders(self):
        """Have all members execute order."""
        for trooper in self.get_units():
            self.__order(trooper)

    def unit_execute_order(self, trooper: Unit):
        """Have a member execute order."""
        self.__order(trooper)

    # ---------- BASIC HANDLERS ----------
    # Handles basic functions as adding and removing units

    def add(self, units: Union[Unit, Sequence[Unit]]) -> None:
        """Adds unit(s) to troop."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
                self.marines.append(unit)
            elif unit.unit_type.unit_typeid in siege_tanks_TYPEIDS:
                self.tanks.append(unit)
                if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SIEGETANKSIEGED:
                    self.tanks_siege.append(unit)
            elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BUNKER:
                self.bunkers[unit] = []
                self.have_soldiers_enter(unit)
            else:
                self.others.append(unit)

            self.not_reached_target.append(unit)

    def remove(self, unit: Unit) -> None:
        """Handles units that are to be removed from troop."""
        if unit in self.marines:
            self.marines.remove(unit)
        elif unit in self.tanks:
            self.tanks.remove(unit)
        elif unit in self.bunkers:
            if unit.is_alive and self.bunkers[unit]:
                unit.ability(ABILITY_ID.UNLOADALL)
            del self.bunkers[unit]
        elif unit in self.others:
            self.others.remove(unit)

    def get_units(self) -> List[Unit]:
        """Get all units in troop."""
        return (self.marines
                + self.tanks
                + self.others
                + list(self.bunkers.keys()))

    def has_unit(self, unit: Unit) -> bool:
        """Check if troop has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    def set_target(self, target: Union[Point2D, Unit]):
        """Sets target of troop."""
        self.__target = target
        self.not_reached_target = self.get_units()

        for bunker in self.bunkers:
            if not self.nearby_target(bunker):
                self.remove(bunker)

    # ---------- MISC ----------
    # Other needed functions

    def build_bunker(self, bot: IDABot, location) -> None:  # AW
        """Builds a bunker when necessary."""
        bunker = UnitType(UNIT_TYPEID.TERRAN_BUNKER, bot)
        workplace = closest_workplace(location)

        if can_afford(bot, bunker) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_BUNKER)\
                and bot.have_one(UNIT_TYPEID.TERRAN_BARRACKS) \
                and not workplace.is_building_unittype(bunker)\
                and not self.bunkers:
            position = bot.building_placer.get_build_location_near(
                location.to_i(), bunker)
            workplace.have_worker_construct(bunker, position)

    # ZW
    def nearby_target(self, at: Union[Unit, Point2D]) -> bool:
        """Check if a unit is nearby target."""
        if isinstance(at, Unit):
            return at.position.dist(self.target_pos) <= self.target_radius
        elif isinstance(at, Point2D):
            return at.dist(self.target_pos) <= self.target_radius
        else:
            raise Exception("Can't do that!")

    # AW
    def have_soldiers_enter(self, bunker: Unit) -> None:
        """Have marines enter bunker."""
        for marine in self.marines[:4]:
            marine.right_click(bunker)
            self.bunkers[bunker].append(marine)

    # ---------- PROPERTIES ----------
    # Values that are trivial calculations but important for the object

    @property
    def satisfied(self):
        """Return True if the troop wants more units."""
        return self.wants_marines <= 0 and self.wants_tanks <= 0

    @property
    def have_all_reached_target(self):
        """Returns true if all members are close to target."""
        return not self.not_reached_target

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

    @property
    def target_pos(self) -> Point2D:
        """Returns the target position."""
        return self.__target if isinstance(self.__target, Point2D) \
            else self.__target.position

# ========== END OF TROOP ==========


# All troops!
defenders = []
attackers = []


# ZW
def create_troop_defending(point: Point2D):
    """Create a new troop with given target that are suppose to defend."""
    defenders.append(Troop(point))


# ZW
def create_troop_attacking(point: Point2D):
    """Creates a new troop with given target that are suppose to attack."""
    attackers.append(Troop(point, True))


# ZW
def all_troops():
    """Returns all troops."""
    return attackers + defenders


# ZW
def marine_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Find closest troop requiring a marine most."""
    closest = [None, None, None]
    distance = [0, 0, 0]

    for troop in all_troops():
        if troop.wants_marines > 0 and not troop.is_attackers:
            if not closest[0] or troop.target_pos.dist(position) / troop.wants_marines < distance[0]:
                closest[0] = troop
                distance[0] = troop.target_pos.dist(position)
        elif troop.wants_marines > 0:
            if not closest[1] or troop.target_pos.dist(position) / troop.wants_marines < distance[1]:
                closest[1] = troop
                distance[1] = troop.target_pos.dist(position)
        else:
            if not closest[2] or troop.target_pos.dist(position) < distance[2]:
                closest[2] = troop
                distance[2] = troop.target_pos.dist(position)

    return closest[0] if closest[0] else closest[1] if closest[1] else closest[2]


# ZW
def tank_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Find closest troop requiring a tank most."""
    closest = [None, None, None]
    distance = [0, 0, 0]

    for troop in all_troops():
        if troop.wants_tanks > 0 and not troop.is_attackers:
            if not closest[0] or troop.target_pos.dist(position) / troop.wants_tanks < distance[0]:
                closest[0] = troop
                distance[0] = troop.target_pos.dist(position)
        elif troop.wants_tanks > 0:
            if not closest[1] or troop.target_pos.dist(position) / troop.wants_tanks < distance[1]:
                closest[1] = troop
                distance[1] = troop.target_pos.dist(position)
        else:
            if not closest[2] or troop.target_pos.dist(position) < distance[2]:
                closest[2] = troop
                distance[2] = troop.target_pos.dist(position)

    return closest[0] if closest[0] else closest[1] if closest[1] else closest[2]


# ZW
def bunker_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Return suitable troop for bunker."""
    for troop in all_troops():
        if not troop.is_attackers and troop.nearby_target(position):
            return troop
    return None


# ZW
def find_unit_troop(unit: Unit) -> Union[Troop, None]:
    """Return the troop this unit is in. If not any then null."""
    for troop in all_troops():
        if troop.has_unit(unit):
            return troop
    return None


def closest_troop(pos: Point2D) -> Union[Troop, None]:
    """Finds the closest troop to a position"""
    closest = None
    distance = 0
    for troop in all_troops():
        if not closest or distance > troop.target_pos.dist(pos):
            closest = troop
            distance = troop.target_pos.dist(pos)

    return closest
