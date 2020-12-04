from typing import Union, Sequence, Dict
import random
import math
from library import *
from copy import deepcopy


from funcs import *


# DP
from scai_backbone import refineries_TYPEIDS, minerals_TYPEIDS


class Workplace:
    """handles jobs for workers"""
    location: BaseLocation  # The BaseLocation the workplace represent

    #  ___Job_list___
    # jobs are roles that a unit can have within a workplace

    # SCVs:
    workers: List[Unit]  # SCVs
    miners: List[Unit]  # Workers who collect minerals
    gasers: List[Unit]  # Workers who collect gas
    builders: List[Unit]  # Workers who construct

    # Buildings:
    command_centers: List[Unit]  # All command centers (probably just one)
    refineries: Dict[Unit, List[Unit]]  # The list contains all its gas collectors
    barracks: List[Unit]  # All barracks
    factories: List[Unit]  # All factories

    # Other:
    others: List[Unit]  # All other units in this workplace
    # ---------------

    # Max number of buildings per workplace (base location)
    max_number_of_barracks: int = 2
    max_number_of_factories: int = 1

    under_attack: bool  # If workplace is under attack or not

    mineral_fields: List[Unit]  # All discovered mineral fields in workplace
    geysers: List[Unit]         # All discovered geysers in workplace

    builders_targets: Dict[Unit, tuple]  # Key is builder and Tuple is (what: UnitType, where: Point2DI)

    def on_step(self, bot: IDABot) -> None:
        """Called each on_Step() of IDABot."""
        self.update_workers(bot)
        self.build_supply_depot(bot)
        self.build_barrack(bot)
        self.build_factory(bot)
        self.build_refinery(bot)

    def on_idle_my_unit(self, unit: Unit, bot: IDABot) -> None:
        """Called each time for a worker that is idle in this workplace."""
        if unit in self.miners and self.mineral_fields:
            unit.right_click(random.choice(self.mineral_fields))
        elif unit in self.gasers:
            for refinery, gasers in self.refineries.items():
                if unit in gasers:
                    unit.right_click(refinery)
                    break

    def __init__(self, location: BaseLocation, bot: IDABot):
        """Called when a new workplace is created. Note that a workplace
        is created from a BaseLocation and there should be max one at each.
        """
        self.location = location
        self.workers = []
        self.miners = []
        self.mineral_fields = []
        self.geysers = []
        self.gasers = []
        self.builders = []
        self.builders_targets = {}
        self.refineries = {}
        self.others = []
        self.under_attack = False
        self.barracks = []
        self.factories = []

    # DP
    def get_scout(self) -> Union[Unit, None]:
        """Returns a suitable scout (worker)"""
        worker = self.get_suitable_worker_and_remove()
        if worker:
            add_scout(worker)
        return worker

    # ZW
    def add_miner(self, worker: Unit) -> None:
        """Adds a miner and handles necessary operations."""
        worker.stop()
        self.miners.append(worker)

    # ZW
    def remove_miner(self, worker: Unit) -> None:
        """Removes a miner and handles necessary operations."""
        if worker in self.miners:
            self.miners.remove(worker)

    # ZW
    def add_gaser(self, worker: Unit, refinery: Unit) -> None:
        """Adds a gas collector and handles necessary operations."""
        worker.stop()
        self.gasers.append(worker)
        self.refineries[refinery].append(worker)

    # ZW
    def remove_gaser(self, worker: Unit) -> None:
        """Removes a gas collector and handles necessary operations."""
        self.gasers.remove(worker)
        for refinery, gasers in self.refineries.items():
            if worker in gasers:
                self.refineries[refinery].remove(worker)

    # ZW
    def add_builder(self, worker: Unit) -> None:
        """Adds a builder and handles necessary operations."""
        self.builders.append(worker)

    # ZW
    def remove_builder(self, worker: Unit) -> None:
        """Removes a builder and handles necessary operations."""
        self.builders.remove(worker)
        if worker in self.builders_targets:
            del self.builders_targets[worker]

    # ZW
    def free_worker(self, worker: Unit) -> None:
        """Remove the job of a worker (although remains a worker)."""
        if worker in self.miners:
            self.remove_miner(worker)
        elif worker in self.gasers:
            self.remove_gaser(worker)
        elif worker in self.builders:
            self.remove_builder(worker)

    # ZW
    def assign_worker_job(self, worker: Unit) -> None:
        """Assign a worker without a job to a suitable one."""
        if self.wants_gasers:
            for refinery, units in self.refineries.items():
                if len(units) < 3:
                    self.free_worker(worker)
                    self.add_gaser(worker, refinery)
                    break
        else:
            self.free_worker(worker)
            self.add_miner(worker)

    # DP
    def update_workers(self, bot: IDABot) -> None:
        """Updates all workers and redistribute jobs if needed."""
        lazy_builders = []
        for builder in self.builders:
            if builder.has_target and builder.target.unit_type.unit_typeid in minerals_TYPEIDS:
                lazy_builders.append(builder)
        for builder in lazy_builders:
            self.assign_worker_job(builder)

        for worker in self.workers:
            if self.wants_gasers and worker in self.miners:
                for refinery, units in self.refineries.items():
                    if len(units) < 3:
                        self.remove_miner(worker)
                        self.add_gaser(worker, refinery)

    # DP
    def get_suitable_builder(self) -> Union[Unit, None]:
        """Returns a suitable miner (worker)"""
        for unit in self.miners:
            if not unit.is_carrying_minerals:
                return unit
        return None

    def get_suitable_worker_and_remove(self) -> Union[Unit, None]:
        """Returns a suitable worker and removes it from the workplace."""
        worker = self.get_suitable_builder()
        if worker:
            self.remove(worker)
        return worker

    def get_units(self) -> List[Unit]:
        """Get all units in workplace."""
        return self.workers + self.others + self.barracks + self.factories

    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    # AW
    def build_supply_depot(self, bot: IDABot) -> None:
        """Builds a supply depot when necessary."""
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot)

        if (bot.current_supply / bot.max_supply) >= 0.8 \
                and bot.max_supply < 200 \
                and can_afford(bot, supply_depot) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_SUPPLYDEPOT) \
                and not self.is_building_unittype(supply_depot):
            location = self.building_location_finder(bot, supply_depot)
            self.have_worker_construct(supply_depot, location)

    # AW
    def build_barrack(self, bot: IDABot) -> None:
        """Builds a barrack when necessary."""
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot)

        if can_afford(bot, barrack) \
                and len(self.barracks) < self.max_number_of_barracks \
                and not self.is_building_unittype(barrack)\
                and len(self.miners) > 5:

            location = self.building_location_finder(bot, barrack)
            self.have_worker_construct(barrack, location)

    # ZW
    def build_refinery(self, bot: IDABot) -> None:
        """Builds a refinery at base location if possible."""
        if len(self.geysers) > len(self.refineries):
            refinery_type = UnitType(UNIT_TYPEID.TERRAN_REFINERY, bot)

            if not self.is_building_unittype(refinery_type) \
                    and can_afford(bot, refinery_type):

                for geyser in self.geysers:
                    geyser_occupied = False
                    for refinery in self.refineries:
                        if refinery.position.squared_dist(geyser.position) < 1:
                            geyser_occupied = True
                            break

                    if not geyser_occupied:
                        self.have_worker_construct(refinery_type, geyser)
                        break

    # DP
    def build_factory(self, bot: IDABot) -> None:
        """Builds a factory when necessary."""
        factory = UnitType(UNIT_TYPEID.TERRAN_FACTORY, bot)

        if can_afford(bot, factory) \
                and len(self.factories) < self.max_number_of_factories \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_FACTORY) \
                and not self.is_building_unittype(factory)\
                and len(self.miners) > 5:
            location = self.building_location_finder(bot, factory)
            self.have_worker_construct(factory, location)

    def upgrade_factory(self, bot: IDABot, unit):
        """Upgrades an existing factory with a techlab"""
        factory_techlab = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, bot)
        unit.train(factory_techlab)


    def building_location_finder(self, bot: IDABot, unit_type) -> Point2D:
        """Finds a suitable location to build a unit of given type"""
        home_base = self.location.position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        if unit_type == UnitType(UNIT_TYPEID.TERRAN_FACTORY, bot):
            return bot.building_placer.get_build_location_near(home_base_2di, unit_type, 40)
        elif unit_type == UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot):
            return bot.building_placer.get_build_location_near(home_base_2di, unit_type, 35)
        elif unit_type == UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot):
            return bot.building_placer.get_build_location_near(home_base_2di, unit_type, 5)
        else:
            raise Exception("Found location is bad.")

    # ZW
    def add(self, units: Union[Unit, Sequence[Unit]]) -> None:
        """Adds unit to workplace."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if self.has_unit(unit):
                continue

            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
                self.workers.append(unit)

                goto_gaser = None
                if self.wants_gasers:
                    for refinery, units in self.refineries.items():
                        if refinery.is_completed and len(units) < 3:
                            goto_gaser = refinery

                if goto_gaser:
                    self.add_gaser(unit, goto_gaser)
                else:
                    self.add_miner(unit)

            elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BARRACKS:
                self.add_barracks(unit)

            elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_FACTORY:
                self.add_factory(unit)

            elif unit.unit_type.unit_typeid in refineries_TYPEIDS:
                self.add_refinery(unit)

            else:
                self.others.append(unit)

    # ZW
    def remove(self, units: Union[Unit, Sequence[Unit]]) -> None:
        """Removes unit(s) from current job(s) in current workplace"""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if not self.has_unit(unit):
                continue

            if unit in self.workers:
                self.workers.remove(unit)

            if unit in self.builders:
                self.remove_builder(unit)

            if unit in self.miners:
                self.remove_miner(unit)

            if unit in self.gasers:
                self.remove_gaser(unit)

            if unit in self.others:
                self.others.remove(unit)

            if unit in self.barracks:
                self.barracks.remove(unit)

            if unit in self.factories:
                self.factories.remove(unit)

    # DP
    def add_refinery(self, refinery) -> None:
        """Adds a refinery to the workplace (needs to be finished)."""
        self.refineries[refinery] = []

    # ZW
    def remove_refinery(self, refinery) -> None:
        """Removes a refinery from the workplace."""
        free_workers = self.refineries[refinery]
        del self.refineries[refinery]
        for worker in free_workers:
            self.free_worker(worker)
            self.assign_worker_job(worker)

    def has_build_target(self, building: Unit) -> bool:
        """Check if workplace is trying to construct given unit."""
        for target in self.builders_targets.values():
            if building.unit_type == target[0] and building.tile_position == target[1]:
                return True
        return False

    def on_building_completed(self, building: Unit) -> None:
        """Called when a new building has been constructed."""
        # print("done:", building)
        for builder, target in self.builders_targets.items():
            if target[1] == building.tile_position \
                    and target[0] == building.unit_type:
                # print("builder done:", builder)
                self.remove_builder(builder)
                self.assign_worker_job(builder)
                break
        # print("miss!")

    # ZW
    def have_worker_construct(self, building: UnitType,
                              position: Union[Point2DI, Unit]) -> None:
        """Order workplace to try to construct building at given position."""
        worker = self.get_suitable_builder()

        if worker:
            if isinstance(position, Point2DI):
                build = lambda: worker.build(building, position)
                target = (building, position)
            elif isinstance(position, Unit):
                build = lambda: worker.build_target(building, position)
                target = (building, position.tile_position)
            else:
                print("'I can't build here!'-The building can't be constructed")
                target = None
                build = None

            if target:
                self.free_worker(worker)
                self.add_builder(worker)
                build()
                self.builders_targets[worker] = target

    def is_building_unittype(self, ut: UnitType) -> bool:
        """Check if workplace is trying to construct unittype already."""
        for target in self.builders_targets.values():
            if target[0] == ut:
                return True
        return False

    def add_barracks(self, barrack) -> None:
        """Adds a barrack to the workplace."""
        self.barracks.append(barrack)
        
    def add_factory(self, factory) -> None:
        """Adds a factory to the workplace."""
        self.factories.append(factory)

    def builders_targets_of_type(self, ut: UnitType) -> Dict[Unit, tuple]:
        """Return all builder targets of given unitType"""
        found = {}
        for builder, builder_target in self.builders_targets.items():
            if ut == builder_target[0]:
                found[builder] = builder_target
        return found

    @property
    def miners_capacity(self) -> int:
        """How many miners the workplace requires."""
        return 2 * len(self.mineral_fields)

    @property
    def gasers_capacity(self) -> int:
        """How many gasers the workplace requires."""
        return 3 * len(self.refineries)

    @property
    def scv_capacity(self) -> int:
        """How many scvs the workplace requires."""
        return self.miners_capacity + self.gasers_capacity

    @property
    def wants_miners(self) -> int:
        """How many miners the workplace is missing."""
        if not self.under_attack:
            return max(self.miners_capacity - len(self.miners)
                       - len(self.builders), 0)
        else:
            return 0

    @property
    def wants_gasers(self) -> int:
        """How many gasers the workplace is missing."""
        if not self.under_attack:
            return max(self.gasers_capacity - len(self.gasers), 0)
        else:
            return 0

    @property
    def wants_scvs(self) -> int:
        """How many scvs the workplace is missing."""
        return self.wants_miners + self.wants_gasers

    @property
    def has_enough_scvs(self) -> bool:
        """If the workplace needs any more scvs."""
        return self.wants_scv <= 0

    def str_unit(self, worker: Unit) -> str:
        """Create a string for a worker to be more informative."""
        return str(worker) + ":" + str(worker.id) + "  on " + str(workplaces.index(self))


# All scouts
scouts = []

# All workplaces!
workplaces = []


# DP
def add_scout(scout: Unit) -> None:
    """Adds a scout to scouts list"""
    scouts.append(scout)


# DP
def remove_scout(scout: Unit) -> None:
    """removes a scout from scouts list"""
    scouts.remove(scout)


# DP
def create_workplace(bot: IDABot, location: BaseLocation) -> Workplace:
    """Create and remember a new workplace at given location."""
    workplaces.append(Workplace(bot, location))
    return workplaces[-1]


# DP, ZW
def closest_workplace(pos: Point2D) -> Workplace:
    """Checks the closest workplace to a position"""
    closest = [None, None]
    distance = [0, 0]
    for workplace in workplaces:
        if workplace.wants_scvs:
            if not closest[0] or distance[0] > workplace.location.position.dist(pos):
                closest[0] = workplace
                distance[0] = workplace.location.position.dist(pos)
        else:
            if not closest[1] or distance[1] > workplace.location.position.dist(pos):
                closest[1] = workplace
                distance[1] = workplace.location.position.dist(pos)

    return closest[0] if closest[0] else closest[1]


# ZW
def scv_seeks_workplace(pos: Point2D) -> Workplace:
    """Checks the closest workplace to a position"""
    closest = [None, None]
    distance = [0, 0]
    for workplace in workplaces:
        if workplace.wants_scvs > 0:
            if not closest[0] or distance[0] > workplace.location.position.dist(pos) \
                    / workplace.wants_scvs:
                closest[0] = workplace
                distance[0] = workplace.location.position.dist(pos) \
                              / workplace.wants_scvs
        else:
            if not closest[1] or distance[1] > workplace.location.position.dist(pos):
                closest[1] = workplace
                distance[1] = workplace.location.position.dist(pos)

    return closest[0] if closest[0] else closest[1]

