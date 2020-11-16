from typing import List, Union, Sequence, Dict
import random

from library import *

from funcs import *

refinery_TYPEID = [UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH]

# DP
class Workplace:
    """handles jobs for workers"""
    target_miners: List[Unit]  # Target for minders
    target_builders: Point2DI

    workers: List[Unit]  # All workers in this workplace
    miners: List[Unit]  # All miners in this workplace
    gasers: List[Unit]  # All gas collectors in this workplace
    builders: List[Unit]  # All builders in this workplace
    refineries: Dict[Unit, List[Unit]]  #

    others: List[int]  # All other units in this workplace

    miners_capacity = property(lambda self: 2 * len(self.target_miners))  # How many miners this workplace is asking for
    gasers_capacity = property(lambda self: 3 * len(self.target_gasers))  # How many gasers this workplace is asking for

    under_attack: bool  # If workplace is under attack or not

    has_enough = property(lambda self: len(self.miners)
                                       >= self.miners_capacity
                                       and len(self.gasers)
                                       >= self.gasers_capacity)

    wants_miners = property(lambda self: self.miners_capacity
                                         - len(self.miners)
                                        if not self.under_attack else 0)

    wants_gasers = property(lambda self: self.gasers_capacity
                                        - len(self.gasers)
                                        if not self.under_attack else 0)

    def on_step(self, bot: IDABot):
        self.refinery_finished(bot)

    def __init__(self, position: BaseLocation, bot: IDABot):
        """
        """
        self.target_miners = get_mineral_fields(position)

        self.workers = []
        self.miners = []
        self.gasers = []
        self.builders = []
        self.refineries = {}
        self.others = []
        self.under_attack = False


    def refinery_finished(self, bot: IDABot):
        for refinery in get_my_refineries(bot):
            if refinery.is_completed and refinery not in self.refineries:
                self.refineries[refinery]



    def get_units(self, bot: IDABot):
        """Get all units in troop."""
        return list(filter(lambda unit: self.has_unit(unit),
                           bot.get_my_units()))



    def move_units(self, bot: IDABot, position: BaseLocation):
        """Moves troop and all its units."""
        if self.target != position:
            for trooper in self.get_units(bot):
                trooper.move(position)
            self.target = position


        # DP
    def build_refinery(self, bot: IDABot):
        """Builds a refinery at base location, then calls for collection"""
        refinery = UnitType(UNIT_TYPEID.TERRAN_REFINERY, bot)
        geysers_list = get_my_geysers(bot)

        for geyser in geysers_list:
            worker = random.choice(get_my_workers(bot))
            if not currently_building(bot, UNIT_TYPEID.TERRAN_REFINERY) and \
                    get_refinery(bot, geyser) is None and \
                    bot.can_afford(refinery):
                worker.build_target(refinery, geyser)


    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        if unit in self.miners + self.gasers + self.others:
            return True
        else:
            return False

    def __iadd__(self, units: Union[Unit, Sequence[Unit]]):
        """Adds unit to workplace. Note: It's called via workplace += unit."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
                self.workers.append(unit)
                if self.wants_gasers:
                    for refinery, units in self.refineries.items():
                        if refinery.is_completed and len(units) < 3:
                            self.gasers.append(unit)
                            self.refineries[refinery]
                            unit.right_click(refinery)
                elif self.wants_miner:
                    self.miners.append(unit)
                    unit.right_click(self.target_miners)
            else:
                self.others.append(unit)


# All troops!
workplaces = []


# ZW
def create_workplace(point: BaseLocation):
    """Create"""
    workplaces.append(Workplace(point))


# ZW
def worker_seeks_workplace(position: BaseLocation) -> Workplace:
    closest = None
    distance = 0
    for workplace in workplaces:
        if not closest or distance < workplace.target.dist(position):
            closest = workplace
            distance = workplace.target.dist(position)
    return closest