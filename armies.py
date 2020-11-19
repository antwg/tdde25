from typing import List, Union, Sequence

from library import *

siege_tanks_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SIEGETANK,
    UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]


# ZW
class Troop:
    """A collection of military units."""
    target: Point2D  # Common target for all units in troop

    marines: List[Unit]  # All marines in this troop
    tanks: List[Unit]    # All siege tanks in this troop
    others: List[Unit]   # All other units in this troop

    marines_capacity: int = 8  # How many marines this troop is asking for
    tanks_capacity: int = 2    # How many tanks this troop is asking for

    under_attack: bool  # If troop is under attack or not

    has_enough = property(lambda self: len(self.marines)
                                       >= self.marines_capacity
                                       and len(self.tanks)
                                       >= self.tanks_capacity)

    wants_marines = property(lambda self: self.marines_capacity
                                          - len(self.marines)
                                          if not self.under_attack else 0)
    wants_tanks = property(lambda self: self.tanks_capacity
                                        - len(self.tanks)
                                        if not self.under_attack else 0)

    def __init__(self, position: Point2D):
        """Called when a new troop is being created. Note that no units are
        required for making a troop, rather it is when units are made.
        """
        self.target = position
        self.marines = []
        self.tanks = []
        self.others = []
        self.under_attack = False

    def get_units(self):
        """Get all units in troop."""
        return self.marines + self.tanks + self.others

    def move_units(self, position: Point2D):
        """Moves troop and all its units."""
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

    def __iadd__(self, units: Union[Unit, Sequence[Unit]]):
        """Adds unit to troop. Note: It's called via troop += unit."""
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


# All troops!
troops = []


# ZW
def create_troop(point: Point2D):
    """Create"""
    troops.append(Troop(point))


# ZW
def marine_seeks_troop(position: Point2D) -> Troop:
    closest = None
    distance = 0
    for troop in troops:
        if not closest or troop.target.dist(position) * max(troop.wants_marines, 0.1) < distance:
            closest = troop
            distance = troop.target.dist(position)
    return closest


# ZW
def tank_seeks_troop(position: Point2D) -> Troop:
    closest = None
    distance = 0
    for troop in troops:
        if not closest or troop.target.dist(position) * max(troop.wants_tanks, 0.1) < distance:
            closest = troop
            distance = troop.target.dist(position)
    return closest
