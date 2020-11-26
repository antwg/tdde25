from typing import Union, Sequence, Dict
import random

from library import *

from funcs import *
from armies import *

refinery_TYPEID = [UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH]


# DP
class Workplace:
    """handles jobs for workers"""
    location: BaseLocation
    target_miners: List[Unit]  # Target for minders

    workers: List[Unit]  # All workers in this workplace
    miners: List[Unit]  # All miners in this workplace
    gasers: List[Unit]  # All gas collectors in this workplace
    builders: List[Unit]  # All builders in this workplace
    refineries: Dict[Unit, List[Unit]]  #
    barracks: List[Unit]
    others: List[Unit]  # All other units in this workplace

    scv_capacity = property(lambda self: self.miners_capacity
                                         + self.gasers_capacity)

    miners_capacity = property(lambda self: 2 * len(self.miners_targets))  # How many miners this workplace is asking for
    gasers_capacity = property(lambda self: 3 * len(self.refineries))  # How many gasers this workplace is asking for
    max_number_of_barracks: int = 2

    under_attack: bool  # If workplace is under attack or not
    miners_targets: List[Unit]
    builders_targets: Dict[Unit, tuple]  # Tuple is (what: UnitType, where: Point2D)

    has_enough = property(lambda self: len(self.miners)
                                       >= self.miners_capacity
                                       and len(self.gasers)
                                       >= self.gasers_capacity)

    wants_scvs = property(lambda self: self.wants_gasers + self.wants_miners)

    wants_miners = property(lambda self: self.miners_capacity
                                         - len(self.miners)
                                        if not self.under_attack else 0)

    wants_gasers = property(lambda self: self.gasers_capacity
                                        - len(self.gasers)
                                        if not self.under_attack else 0)

    def on_step(self, bot: IDABot):
        """"""
        self.build_barrack(bot)
        self.build_supply_depot(bot)
        if len(self.refineries) < 2:
            self.build_refinery(bot)
        self.expansion(bot)

    def __init__(self, location: BaseLocation, bot: IDABot):
        """
        """
        self.location = location
        self.workers = []
        self.miners = []
        self.miners_targets = get_mineral_fields(bot, location)
        self.gasers = []
        self.builders = []
        self.builders_targets = {}
        self.refineries = {}
        self.others = []
        self.under_attack = False
        self.barracks = []

    # ZW
    def add_miner(self, worker: Unit):
        self.miners.append(worker)
        worker.right_click(
            random.choice(self.miners_targets))

    # ZW
    def remove_miner(self, worker: Unit):
        self.miners.remove(worker)

    # ZW
    def add_gaser(self, worker: Unit, refinery: Unit):
        self.gasers.append(worker)
        self.refineries[refinery].append(worker)
        worker.right_click(refinery)

    # ZW
    def remove_gaser(self, worker: Unit):
        self.gasers.remove(worker)
        for refinery, gasers in self.refineries.items():
            if worker in gasers:
                self.refineries[refinery].remove(worker)

    # ZW
    def add_builder(self, worker: Unit):
        self.builders.append(worker)

    # ZW
    def remove_builder(self, worker: Unit):
        self.builders.remove(worker)
        if worker in self.builders_targets:
            del self.builders_targets[worker]

    # ZW
    def free_worker(self, worker: Unit):
        if worker in self.miners:
            self.remove_miner(worker)
        elif worker in self.gasers:
            self.remove_gaser(worker)
        elif worker in self.builders:
            self.remove_builder(worker)

    # ZW
    def assign_worker_job(self, worker: Unit):
        if self.wants_gasers:
            for refinery, units in self.refineries.items():
                if len(units) < 3:
                    self.free_worker(worker)
                    self.add_gaser(worker, refinery)

        else:
            self.free_worker(worker)
            self.add_miner(worker)

    # DP
    def update_workers(self, bot: IDABot):
        for worker in self.workers:
            if self.wants_gasers and worker in self.miners:
                for refinery, units in self.refineries.items():
                    if len(units) < 3:
                        self.remove_miner(worker)
                        self.add_gaser(worker, refinery)

    # DP
    def get_suitable_builder(self):
        """Returns a suitable miner (worker)"""
        for unit in self.miners:
            if not unit.is_carrying_minerals:
                return unit
        return None

    def get_units(self):
        """Get all units in troop."""
        return self.workers + self.others

    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    def build_supply_depot(self, bot: IDABot):  # AW
        """Builds a supply depot when necessary."""
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot)

        if (bot.current_supply / bot.max_supply) >= 0.8\
                and bot.max_supply < 200\
                and bot.minerals >= 100\
                and not currently_building(bot, UNIT_TYPEID.TERRAN_SUPPLYDEPOT)\
                and supply_depot not in self.builders_targets.values():
            location = bot.building_location_finder(supply_depot)
            self.have_worker_construct(supply_depot, location)

    def build_barrack(self, bot: IDABot):  # AW
        """Builds a barrack when necessary."""
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot)

        if bot.minerals >= barrack.mineral_price\
                and len(get_my_type_units(bot, UNIT_TYPEID.TERRAN_BARRACKS)) <\
                self.max_number_of_barracks\
                and not currently_building(bot, UNIT_TYPEID.TERRAN_BARRACKS) \
                and not self.is_building_unittype(barrack):

            location = bot.building_location_finder(barrack)
            # print(bot.currently_building(UNIT_TYPEID.TERRAN_BARRACKS))

            self.have_worker_construct(barrack, location)
            # print('building barrack')

    # DP
    def build_refinery(self, bot: IDABot):
        """Builds a refinery at base location, then calls for collection."""
        refinery = UnitType(UNIT_TYPEID.TERRAN_REFINERY, bot)
        geysers_list = get_my_geysers(bot)
        for geyser in geysers_list:
            if not currently_building(bot, UNIT_TYPEID.TERRAN_REFINERY) and \
                    get_refinery(bot, geyser) is None and \
                    can_afford(bot, refinery) \
                    and not self.is_building_unittype(refinery):
                self.have_worker_construct(refinery, geyser)

    def building_location_finder(self, bot: IDABot, unit_type):
        """Finds a suitable location to build a unit of given type"""
        home_base = self.location.position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        location = bot.building_placer.get_build_location_near(home_base_2di,
                                                               unit_type)
        if bot.building_placer.can_build_here_with_spaces(location.x, location.y,
                                                          unit_type, 5):
            return location
        else:
            raise Exception


    def expansion(self, bot: IDABot):  # AW
        """Builds new command center when needed"""
        marines = UNIT_TYPEID.TERRAN_MARINE
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, bot)
        location = bot.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position

        if len(get_my_type_units(bot, marines)) >= \
                len(workplaces) * 8\
                and can_afford(bot, command_center_type)\
                and not currently_building(bot, command_center)\
                and self.get_units(bot):

            worker = self.get_suitable_builder()
            Unit.build(worker, command_center_type, location)
            create_troop(bot.choke_points(len(bot.base_location_manager.
                                               get_occupied_base_locations(PLAYER_SELF))))

            create_workplace(bot.base_location_manager.get_next_expansion(PLAYER_SELF), bot)

    def __iadd__(self, units: Union[Unit, Sequence[Unit]]):
        """Adds unit to workplace. Note: It's called via workplace += unit."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if self.has_unit(unit):
                continue

            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
                self.workers.append(unit)

                if self.wants_gasers:
                    for refinery, units in self.refineries.items():
                        if refinery.is_completed and len(units) < 3:
                            self.add_gaser(unit, refinery)

                self.add_miner(unit)

            else:
                self.others.append(unit)

    def add_refinery(self, refinery):
        self.refineries[refinery] = []

    # ZW
    def remove_refinery(self, refinery):
        free_workers = self.refineries[refinery]
        del self.refineries[refinery]
        for worker in free_workers:
            self.assign_worker_job(worker)

    def on_building_completed(self, building: Unit):
        for builder, target in self.builders_targets.items():
            if target[1] == building.tile_position \
                    and target[0] == building.unit_type:
                self.remove_builder(builder)
                self.assign_worker_job(builder)
                break

    # ZW
    def have_worker_construct(self, building: UnitType, position: Union[Point2DI, Unit]):
        worker = self.get_suitable_builder()

        if worker:
            if isinstance(position, Point2DI):
                worker.build(building, position)
                target = (building, position)
            elif isinstance(position, Unit):
                worker.build_target(building, position)
                target = (building, position.tile_position)
            else:
                print("'I can't build here!' - The building can't be constructed")
                target = None

            if target:
                self.free_worker(worker)
                self.add_builder(worker)
                self.builders_targets[worker] = target

    def is_building_unittype(self, barrack) -> bool:
        for target in self.builders_targets.values():
            if target[0] == barrack:
                return True
        return False

    def add_barracks(self, barrack):
        self.barracks.append(barrack)


# All workplaces!
workplaces = []


# DP
def create_workplace(bot: IDABot, location: BaseLocation):
    """Create"""
    workplaces.append(Workplace(bot, location))


# DP, ZW
def closest_workplace(pos: Point2D) -> Workplace:
    """Checks the closest workplace to a position"""
    closest = None
    distance = 0
    for workplace in workplaces:
        if not closest or distance > workplace.location.position.dist(pos):
            closest = workplace
            distance = workplace.location.position.dist(pos)

    return closest


# ZW
def scv_seeks_workplace(pos: Point2D) -> Workplace:
    """Checks the closest workplace to a position"""
    closest = None
    distance = 0
    for workplace in workplaces:
        if not closest or distance > workplace.location.position.dist(pos) \
                * workplace.wants_scvs:
            closest = workplace
            distance = workplace.location.position.dist(pos) \
                       * workplace.wants_scvs

    return closest


# DP
def closest_workplace_building(pos: Point2DI) -> Workplace:
    """Checks the closest workplace to a buildings position"""
    pos2d = Point2D(float(pos.x), float(pos.y))
    closest = None
    distance = 0
    for workplace in workplaces:
        if not closest or distance > workplace.location.position.dist(pos2d):
            closest = workplace
            distance = workplace.location.position.dist(pos2d)

    return closest
