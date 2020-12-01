from typing import Union, Sequence, Dict
import random
import math
from library import *

from funcs import *
from armies import *

refinery_TYPEID = [UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH]


# DP
class Workplace:
    """handles jobs for workers"""
    location: BaseLocation

    workers: List[Unit]  # All workers in this workplace
    miners: List[Unit]  # All miners in this workplace
    gasers: List[Unit]  # All gas collectors in this workplace
    builders: List[Unit]  # All builders in this workplace
    refineries: Dict[Unit, List[Unit]]  #
    barracks: List[Unit]
    factories: List[Unit]
    others: List[Unit]  # All other units in this workplace

    scv_capacity = property(lambda self: self.miners_capacity
                                         + self.gasers_capacity)

    miners_capacity = property(
        lambda self: 2 * len(self.mineral_fields))  # How many miners this workplace is asking for
    gasers_capacity = property(lambda self: 3 * len(self.refineries))  # How many gasers this workplace is asking for
    max_number_of_barracks: int = 2
    max_number_of_factories: int = 2

    under_attack: bool  # If workplace is under attack or not

    mineral_fields: List[Unit]  # All mineral fields in workplace
    geysers: List[Unit]  # All geysers in workplace
    builders_targets: Dict[Unit, tuple]  # Tuple is (what: UnitType, where: Point2D)

    has_enough = property(lambda self: (len(self.miners) + len(self.builders))
                                       >= self.miners_capacity
                                       and len(self.gasers)
                                       >= self.gasers_capacity)

    wants_scvs = property(lambda self: self.wants_gasers + self.wants_miners)

    wants_miners = property(lambda self: self.miners_capacity > \
                                         len(self.miners) + len(self.builders)
                                        if not self.under_attack else 0)

    wants_gasers = property(lambda self: self.gasers_capacity \
                                        - len(self.gasers)
                                        if not self.under_attack else 0)

    def on_step(self, bot: IDABot):
        """"""
        self.update_workers(bot)

        self.build_supply_depot(bot)
        self.build_barrack(bot)
        self.build_factory(bot)
        self.build_refinery(bot)

    def on_idle_my_unit(self, unit: Unit, bot: IDABot):
        if unit in self.miners:
            unit.right_click(random.choice(self.mineral_fields))
        elif unit in self.gasers:
            for refinery, gasers in self.refineries.items():
                if unit in gasers:
                    unit.right_click(refinery)
                    break

    def __init__(self, location: BaseLocation, bot: IDABot):
        """
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
    def get_scout(self):
        """Returns a suitable scout (worker)"""
        worker = self.get_suitable_worker_and_remove()
        if worker:
            add_scout(worker)
        return worker

    # ZW
    def add_miner(self, worker: Unit):
        worker.stop()
        # print(self.str_unit(worker), ": miner added")
        self.miners.append(worker)

    # ZW
    def remove_miner(self, worker: Unit):
        if worker in self.miners:
            self.miners.remove(worker)

    # ZW
    def add_gaser(self, worker: Unit, refinery: Unit):
        worker.stop()
        # print(self.str_unit(worker), ": gaser added")
        self.gasers.append(worker)
        self.refineries[refinery].append(worker)

    # ZW
    def remove_gaser(self, worker: Unit):
        # print(self.str_unit(worker), ": gaser removed")
        self.gasers.remove(worker)
        for refinery, gasers in self.refineries.items():
            if worker in gasers:
                self.refineries[refinery].remove(worker)

    # ZW
    def add_builder(self, worker: Unit):
        # print(self.str_unit(worker), ": builder added")
        self.builders.append(worker)

    # ZW
    def remove_builder(self, worker: Unit):
        # print(self.str_unit(worker), ": builder removed")
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
                    break
        else:
            self.free_worker(worker)
            self.add_miner(worker)

    # DP
    def update_workers(self, bot: IDABot):
        """Updates all workers"""
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
    def get_suitable_builder(self):
        """Returns a suitable miner (worker)"""
        for unit in self.miners:
            if not unit.is_carrying_minerals:
                return unit
        return None

    def get_suitable_worker_and_remove(self):
        worker = self.get_suitable_builder()
        if worker:
            self -= worker
        return worker

    def get_units(self):
        """Get all units in troop."""
        return self.workers + self.others + self.barracks + self.factories

    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    def build_supply_depot(self, bot: IDABot):  # AW
        """Builds a supply depot when necessary."""
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot)

        if (bot.current_supply / bot.max_supply) >= 0.8 \
                and bot.max_supply < 200 \
                and can_afford(bot, supply_depot) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_SUPPLYDEPOT) \
                and not self.is_building_unittype(supply_depot):
            location = self.building_location_finder(bot, supply_depot)
            self.have_worker_construct(supply_depot, location)

    def build_barrack(self, bot: IDABot):  # AW
        """Builds a barrack when necessary."""
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot)

        if can_afford(bot, barrack) \
                and len(self.barracks) < self.max_number_of_barracks \
                and not self.is_building_unittype(barrack)\
                and len(self.miners) > 5:

            location = self.building_location_finder(bot, barrack)
            # print(bot.currently_building(UNIT_TYPEID.TERRAN_BARRACKS))

            self.have_worker_construct(barrack, location)
            # print('building barrack')

    # ZW
    def build_refinery(self, bot: IDABot):
        """Builds a refinery at base location, then calls for collection."""
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

    def build_factory(self, bot: IDABot):  # DP
        """Builds a barrack when necessary."""
        factory = UnitType(UNIT_TYPEID.TERRAN_FACTORY, bot)
        factory_with_upgrade = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, bot)

        if can_afford(bot, factory) \
                and len(self.factories) < self.max_number_of_factories \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_FACTORY) \
                and not self.is_building_unittype(factory)\
                and len(self.miners) > 5:
            location = self.building_location_finder(bot, factory)
            # print(bot.currently_building(UNIT_TYPEID.TERRAN_BARRACKS))

            self.have_worker_construct(factory, location)
            # print('building barrack')

    def building_location_finder(self, bot: IDABot, unit_type):
        """Finds a suitable location to build a unit of given type"""
        home_base = self.location.position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        location = bot.building_placer.get_build_location_near(home_base_2di,
                                                               unit_type)
        if bot.building_placer.can_build_here_with_spaces(location.x, location.y,
                                                          unit_type, 10):
            return location
        else:
            print("building not built")
            raise Exception

    def __iadd__(self, units: Union[Unit, Sequence[Unit]]):
        """Adds unit to workplace. Note: It's called via workplace += unit."""
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

            elif unit.unit_type.unit_typeid in refinery_TYPEID:
                self.add_refinery(unit)

            else:
                self.others.append(unit)

        return self

    def __isub__(self, units: Union[Unit, Sequence[Unit]]):
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

        return self

    def add_refinery(self, refinery):
        self.refineries[refinery] = []

    # ZW
    def remove_refinery(self, refinery):
        free_workers = self.refineries[refinery]
        del self.refineries[refinery]
        for worker in free_workers:
            self.assign_worker_job(worker)

    def has_build_target(self, building: Unit) -> bool:
        for target in self.builders_targets.values():
            if building.unit_type == target[0] and building.tile_position == target[1]:
                return True
        return False

    def on_building_completed(self, building: Unit):
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
    def have_worker_construct(self, building: UnitType, position: Union[Point2DI, Unit]):
        worker = self.get_suitable_builder()

        if worker:
            if isinstance(position, Point2DI):
                build = lambda: worker.build(building, position)
                target = (building, position)
            elif isinstance(position, Unit):
                build = lambda: worker.build_target(building, position)
                target = (building, position.tile_position)
            else:
                print("'I can't build here!' - The building can't be constructed")
                target = None
                build = None

            if target:
                # print(worker, ":", target)
                self.free_worker(worker)
                self.add_builder(worker)
                build()
                # orders_for_units[worker.id] = build
                self.builders_targets[worker] = target

    def is_building_unittype(self, barrack) -> bool:
        for target in self.builders_targets.values():
            if target[0] == barrack:
                return True
        return False

    def add_barracks(self, barrack):
        self.barracks.append(barrack)
        
    def add_factory(self, factory):
        self.factories.append(factory)

    def builders_targets_of_type(self, ut: UnitType) -> Dict[Unit, tuple]:
        """Return all builder targets of given unitType"""
        found = {}
        for builder, builder_target in self.builders_targets.items():
            if ut == builder_target[0]:
                found[builder] = builder_target
        return found

    def str_unit(self, worker: Unit):
        return str(worker) + ":" + str(worker.id) + "  on " + str(workplaces.index(self))


# All scouts
scouts = []


# All workplaces!
workplaces = []


# DP
def add_scout(scout: Unit) -> None:
    scouts.append(scout)


# DP
def remove_scout(scout: Unit) -> None:
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

