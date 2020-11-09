from typing import List, Union, Sequence

from library import *

siege_tanks_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SIEGETANK,
    UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]


class Troop:
    target: Point2D

    marines: List[int]
    tanks: List[int]
    others: List[int]

    marines_capacity: int = 8
    tanks_capacity: int = 2

    has_enough = property(lambda self: len(self.marines)
                                        >= self.marines_capacity
                                       and len(self.tanks)
                                        >= self.tanks_capacity)

    wants_marines = property(lambda self: len(self.marines)
                                          < self.marines_capacity)
    wants_tanks = property(lambda self: len(self.tanks)
                                          < self.tanks_capacity)

    def __init__(self, position: Point2D):
        self.target = position

    def get_units(self, bot: IDABot):
        return filter(lambda unit: self.has_unit(unit),
                      bot.get_my_units())

    def move_units(self, bot: IDABot, position: Point2D):
        for trooper in self.get_units(bot):
            trooper.move(position)
        self.target = position

    def has_unit(self, unit: Unit) -> bool:
        if unit.id in self.marines + self.tanks + self.others:
            return True
        else:
            False

    def __add__(self, units: Union[Unit, Sequence[Unit]]):
        if isinstance(units, Unit):
            units = list(units)

        for unit in units:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
                self.marines.append(unit.id)
            elif unit.unit_type.unit_typeid in siege_tanks_TYPEIDS:
                self.others.append(unit.id)
            else:
                self.others.append(unit.id)


troops = []
