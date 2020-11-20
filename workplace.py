from typing import List, Union, Sequence, Dict
import random

from library import *

from funcs import *

refinery_TYPEID = [UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH]

# DP
class Workplace:
    """handles jobs for workers"""
    location: BaseLocation
    target_miners: List[Unit]  # Target for minders
    target_gasers: List[Unit]  # Target for gasers
    target_builders: Point2DI  # Target for builders

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

    def on_step(self, bot: IDABot,):
        if len(self.refineries) < 2:
            self.build_refinery(bot)

    def __init__(self, position: BaseLocation, bot: IDABot):
        """
        """
        self.location = position
        self.workers = []
        self.miners = []
        self.gasers = []
        self.builders = []
        self.refineries = {}
        self.others = []
        self.under_attack = False

        self.target_miners = get_mineral_fields(bot, position)
        self.target_gasers = []

    # DP
    def update_workers(self, bot: IDABot):
        for worker in self.workers:
            if worker in self.builders and not builder_currently_building(bot, worker):
                if self.wants_gasers:
                    for refinery, units in self.refineries.items():
                        if refinery.is_completed and len(units) < 3:
                            self.gasers.append(worker)
                            self.refineries[refinery].append(worker)
                            worker.right_click(refinery)
                elif self.wants_miners:
                    self.miners.append(worker)
                    worker.right_click(random.choice(self.target_miners))
                else:
                    self.others.append(worker)
                    #do smthing :)
            elif self.wants_gasers and worker in self.miners:
                for refinery, units in self.refineries.items():
                    if refinery.is_completed and len(units) < 3:
                        self.miners.remove(worker)
                        self.gasers.append(worker)
                        self.refineries[refinery].append(worker)
                        worker.right_click(refinery)
            else:
                self.miners.append(worker)
                worker.right_click(random.choice(self.target_miners))

        # DP

    def build_refinery(self, bot: IDABot):
        """Builds a refinery at base location, then calls for collection"""
        refinery = UnitType(UNIT_TYPEID.TERRAN_REFINERY, bot)
        geysers_list = get_my_geysers(bot)

        for geyser in geysers_list:
            if not currently_building(bot, UNIT_TYPEID.TERRAN_REFINERY) and \
                    get_refinery(bot, geyser) is None and \
                    can_afford(bot, refinery):
                if self.get_suitable_builder() is not None:
                    worker = self.get_suitable_builder()

                worker.build_target(refinery, geyser)



    # DP
    def get_suitable_builder(self):
        """returns a suitable miner (worker)"""
        for unit in self.miners:
            if not unit.is_carrying_minerals:
                self.miners.remove(unit)
                self.builders.append(unit)
                return unit
        else:
            return random.choice(self.miners)


    def get_units(self, bot: IDABot):
        """Get all units in troop."""
        return list(filter(lambda unit: self.has_unit(unit),
                           bot.get_my_units()))

    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        if unit in self.miners + self.gasers + self.others:
            return True
        else:
            return False


    def is_worker_collecting_gas(self, bot: IDABot, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        def squared_distance(unit_1, unit_2):
            p1 = unit_1.position
            p2 = unit_2.position
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for refinery in get_my_refineries(bot):
            if refinery.is_completed and squared_distance(worker, refinery) < 2 ** 2:
                return True


    def __iadd__(self, units: Union[Unit, Sequence[Unit]]):
        """Adds unit to workplace. Note: It's called via workplace += unit."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            print("hej!", unit)
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
                self.workers.append(unit)

                if self.wants_gasers:

                    for refinery, units in self.refineries.items():

                        if refinery.is_completed and len(units) < 3:
                            self.gasers.append(unit)
                            self.refineries[refinery].append(unit)
                            unit.right_click(refinery)

                elif self.wants_miners:
                    self.miners.append(unit)
                    unit.right_click(random.choice(self.target_miners))

            elif unit.unit_type.unit_typeid in refinery_TYPEID:
                self.refineries[unit] = []
                self.target_gasers.append(unit)

            else:
                self.others.append(unit)


# All troops!
workplaces = []


# ZW
def create_workplace(bot: IDABot, location: BaseLocation):
    """Create"""
    workplaces.append(Workplace(bot, location))


# ZW
def worker_seeks_workplace(pos: Point2D) -> Workplace:
    """Checks the closest workplace to a position"""
    closest = None
    distance = 0
    for workplace in workplaces:
        if not closest or distance < workplace.position.location.dist(pos):
            closest = workplace
            distance = workplace.location.position.dist(pos)
    return closest
