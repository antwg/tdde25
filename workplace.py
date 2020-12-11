from typing import Union, Sequence, Dict
import random
import math
from library import *
from copy import deepcopy

from extra import *
from funcs import *

from scai_backbone import *


# DP
class Workplace:
    """handles jobs for workers"""
    location: BaseLocation  # The BaseLocation the workplace represent

    #  ___Job_list___
    # Jobs are roles that a unit can have within a workplace

    # SCVs:
    miners: List[Unit]  # Workers who collect minerals
    gasers: List[Unit]  # Workers who collect gas
    builders: List[Unit]  # Workers who construct

    # Buildings:
    command_centers: List[Unit]  # All command centers (probably just one)
    refineries: Dict[Unit, List[Unit]]  # The list contains all its gas collectors
    barracks: List[Unit]  # All barracks
    factories: List[Unit]  # All factories

    # Others:
    others: List[Unit]  # All other units in this workplace
    # ---------------

    # Unit lists for units in special states
    workers: List[Unit]  # All SCVs in a workplace
    factories_with_techlab: List[Unit]  # All factories with a techlab, must be in factories

    # Important information
    under_attack: int  # If workplace is under attack or not
    was_under_attack: bool  # If workplace was attacked this frame

    # Class constants
    safe_distance: int = 40
    under_attack_wait: int = 200

    # ---------- EVENTS ----------
    # These are functions triggered by different events. Most are
    # triggered from MyAgent

    def on_step(self, bot: IDABot) -> None:
        """Called each on_Step() of IDABot."""
        if self.under_attack:
            if not self.was_under_attack:
                self.was_under_attack = True
                print(workplaces.index(self), ": Were under attack!")

            self.under_attack -= 1
        elif self.was_under_attack:
            self.was_under_attack = False
            print(workplaces.index(self), ": All is safe...")

        self.update_workers(bot)

        if self.command_centers:
            self.build_supply_depot(bot)
            self.build_barrack(bot)
            self.build_factory(bot)
            self.build_refinery(bot)
            self.build_engineering_bay(bot)
            self.build_armory(bot)
        else:
            self.build_command_center(bot)

    def on_idle_my_unit(self, unit: Unit, bot: IDABot) -> None:
        """Called each time for a worker that is idle in this workplace."""
        if self.scv_capacity < len(self.workers):
            new_workplace = scv_seeks_workplace(unit.position)
            if new_workplace != self:
                self.remove(unit)
                new_workplace.add(unit)
                return

        if unit in self.miners and self.mineral_fields:
            unit.right_click(random.choice(self.mineral_fields))
        elif unit in self.gasers:
            for refinery, gasers in self.refineries.items():
                if unit in gasers:
                    unit.right_click(refinery)
                    break
        elif unit in self.factories_with_techlab:
            bot.should_train_tanks.append(unit)
        elif unit in self.factories:
            if has_addon(bot, unit, UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB,
                                             bot)):
                self.factories_with_techlab.append(unit)
            else:
                self.upgrade_factory(unit, bot)
        elif unit in self.barracks:
            bot.should_train_marines.append(unit)
        elif unit in self.command_centers:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
                self.upgrade_command_center(unit, bot)
            elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_ORBITALCOMMAND:
                if unit.energy == unit.max_energy:
                    interest = random.choice(get_all_hidden_bases(bot))
                    if interest:
                        unit.ability(ABILITY_ID.EFFECT_SCAN, interest.position)

    def on_building_completed(self, building: Unit) -> None:
        """Called when a new building has been constructed."""
        for builder, target in self.builders_targets.items():
            if target[1] == building.tile_position \
                    and target[0] == building.unit_type:
                self.remove_builder(builder)
                self.assign_worker_job(builder)
                break

    def on_damaged_member(self, unit: Unit, bot: IDABot) -> None:
        """Called each time a unit in the workplace loses life (might be dead)."""
        if not self.under_attack:
            self.under_attack = self.under_attack_wait

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
        self.under_attack = 0
        self.was_under_attack = False
        self.command_centers = []
        self.barracks = []
        self.factories = []
        self.factories_with_techlab = []

        for unit in bot.remember_these:
            if unit.minerals_left_in_mineralfield > 0 \
                    and unit.unit_type.is_mineral \
                    and location.contains_position(unit.position) \
                    and unit not in self.mineral_fields:
                self.add_mineral_field(unit)

            if unit.gas_left_in_refinery > 0 and unit.unit_type.is_geyser \
                    and location.contains_position(unit.position):
                self.add_geyser(unit)

    # ---------- JOB: MINER ----------
    # Methods relevant for SCVs that gathers minerals in workplace.

    mineral_fields: List[Unit]  # All discovered mineral fields in workplace

    # ZW
    def add_miner(self, worker: Unit) -> None:
        """Adds a miner and handles necessary operations."""
        if worker.has_target and worker.target not in self.mineral_fields:
            worker.stop()
        self.miners.append(worker)

    # ZW
    def remove_miner(self, worker: Unit) -> None:
        """Removes a miner and handles necessary operations."""
        if worker in self.miners:
            self.miners.remove(worker)

    @property
    def miners_capacity(self) -> int:
        """How many miners the workplace requires."""
        return 2 * len(self.mineral_fields)

    @property
    def wants_miners(self) -> int:
        """How many miners the workplace is missing."""
        if not self.under_attack:
            return max(self.miners_capacity - len(self.miners)
                       - len(self.builders), 0)
        else:
            return 0

    # ---------- JOB: GASER ----------
    # Methods relevant for SCVs that gathers gas in workplace.

    geysers: List[Unit]  # All discovered geysers in workplace

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

    def is_gaser_in_refinery(self, worker: Unit) -> bool:
        """Return True if the gaser is 'inside' of a refinery."""
        for refinery, occupants in self.refineries.items():
            if worker in occupants \
                    and refinery.position.squared_dist(worker.position) \
                    < (refinery.radius + worker.radius + 0.1)**2:
                return True

        return False

    @property
    def wants_gasers(self) -> int:
        """How many gasers the workplace is missing."""
        if not self.under_attack:
            return max(self.gasers_capacity - len(self.gasers), 0)
        else:
            return 0

    @property
    def gasers_capacity(self) -> int:
        """How many gasers the workplace requires."""
        return 3 * len(self.refineries)

    # ---------- JOB: BUILDER ----------
    # Methods relevant for SCVs that are requested to build for workplace.

    builders_targets: Dict[Unit, tuple]  # Key is builder and Tuple is (what: UnitType, where: Point2DI)

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

    def builders_targets_of_type(self, ut: UnitType) -> Dict[Unit, tuple]:
        """Return all builder targets of given unitType."""
        found = {}
        for builder, builder_target in self.builders_targets.items():
            if ut == builder_target[0]:
                found[builder] = builder_target
        return found

    def has_build_target(self, building: Unit) -> bool:
        """Check if workplace is trying to construct given unit."""
        for target in self.builders_targets.values():
            if building.unit_type == target[0] and building.tile_position\
                    == target[1]:
                return True
        return False

    def is_building_unittype(self, ut: UnitType) -> bool:
        """Check if workplace is trying to construct unittype already."""
        for target in self.builders_targets.values():
            if target[0] == ut:
                return True
        return False

    # ---------- GROUP: WORKER ----------
    # Methods relevant for all SCVs in workplace

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
        if self.wants_gasers and len(self.gasers) < len(self.miners):
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
            if builder.has_target and builder.target.unit_type.unit_typeid \
                    in minerals_TYPEIDS \
                    or builder.is_idle:
                lazy_builders.append(builder)
        for builder in lazy_builders:
            self.assign_worker_job(builder)

        for worker in self.workers:
            if len(self.gasers) < len(self.miners) \
                    and self.wants_gasers and worker in self.miners:
                for refinery, units in self.refineries.items():
                    if len(units) < 3:
                        self.remove_miner(worker)
                        self.add_gaser(worker, refinery)
                        break
            elif len(self.gasers) > 1 + len(self.miners) \
                    and self.wants_miners \
                    and worker in self.gasers \
                    and not self.is_gaser_in_refinery(worker):
                self.remove_gaser(worker)
                self.add_miner(worker)

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
            worker.stop()
            self.remove(worker)
        return worker

    @property
    def scv_capacity(self) -> int:
        """How many scvs the workplace requires."""
        return self.miners_capacity + self.gasers_capacity

    @property
    def wants_scvs(self) -> int:
        """How many scvs the workplace is missing."""
        return self.wants_miners + self.wants_gasers

    @property
    def has_enough_scvs(self) -> bool:
        """If the workplace needs any more scvs."""
        return self.wants_scvs <= 0

    # ---------- BUILD ----------
    # Methods that builds structures.

    # AW
    def build_supply_depot(self, bot: IDABot) -> None:
        """Builds a supply depot when necessary."""
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot)

        if (bot.current_supply / bot.max_supply) >= 0.8 \
                and bot.max_supply < 200 \
                and can_afford(bot, supply_depot) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_SUPPLYDEPOT)\
                and not self.is_building_unittype(supply_depot):
            location = self.building_location_finder(bot, supply_depot)
            self.have_worker_construct(supply_depot, location)

    # AW
    def build_barrack(self, bot: IDABot) -> None:
        """Builds a barrack when necessary."""
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot)

        if workplaces[0] == self:
            if can_afford(bot, barrack) \
                    and bot.have_one(UNIT_TYPEID.TERRAN_SUPPLYDEPOT) \
                    and len(self.barracks) < self.max_number_of_barracks \
                    and not self.is_building_unittype(barrack)\
                    and len(self.miners) > 5:

                location = self.building_location_finder(bot, barrack)
                self.have_worker_construct(barrack, location)

        else:
            if can_afford(bot, barrack) \
                    and bot.have_one(UNIT_TYPEID.TERRAN_SUPPLYDEPOT) \
                    and len(self.barracks) < self.small_number_of_barracks \
                    and not self.is_building_unittype(barrack)\
                    and len(self.miners) > 5:

                location = self.building_location_finder(bot, barrack)
                self.have_worker_construct(barrack, location)

    def build_engineering_bay(self, bot: IDABot) -> None:
        """Builds an engineering bay."""
        engineering_bay = UnitType(UNIT_TYPEID.TERRAN_ENGINEERINGBAY, bot)
        if can_afford(bot, engineering_bay) \
                and len(workplaces) >= 2 \
                and not bot.have_one(engineering_bay) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_ENGINEERINGBAY)\
                and not self.is_building_unittype(engineering_bay):
            if bot.side() == 'right':
                location = bot.building_placer.get_build_location_near(
                    Point2DI(110, 23), engineering_bay)
            else:
                location = bot.building_placer.get_build_location_near(
                    Point2DI(41, 148), engineering_bay)

            self.have_worker_construct(engineering_bay, location)

    def build_armory(self, bot: IDABot) -> None:
        """Builds a armory."""
        armory = UnitType(UNIT_TYPEID.TERRAN_ARMORY, bot)
        if can_afford(bot, armory) \
                and len(workplaces) >= 3 \
                and bot.have_one(UNIT_TYPEID.TERRAN_FACTORY) \
                and not bot.have_one(armory) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_ARMORY)\
                and not self.is_building_unittype(armory):
            if bot.side() == 'right':
                location = bot.building_placer.get_build_location_near(
                    Point2DI(110, 23), armory)
            else:
                location = bot.building_placer.get_build_location_near(
                    Point2DI(41, 148), armory)

            self.have_worker_construct(armory, location)

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

    # ZW
    def build_command_center(self, bot: IDABot) -> None:
        """Builds a command center when necessary."""
        command_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, bot)

        if can_afford(bot, command_type) \
                and not self.command_centers \
                and not self.is_building_unittype(command_type):
            if len(self.workers) > 0:
                position = self.location.depot_position
                self.have_worker_construct(command_type, position)

    def upgrade_command_center(self, cc: Unit, bot: IDABot) -> None:
        """Have given command center upgrade."""
        if cc.is_idle  and not self.wants_scvs:

            if workplaces.index(self) == 0 \
                    and bot.minerals > 400 \
                    and bot.have_one(UNIT_TYPEID.TERRAN_BARRACKS):
                cc.ability(ABILITY_ID.MORPH_ORBITALCOMMAND)
            elif bot.minerals > 400 and bot.gas > 400 \
                    and bot.have_one(UNIT_TYPEID.TERRAN_FACTORY):
                cc.ability(ABILITY_ID.MORPH_PLANETARYFORTRESS)

    # DP
    def build_factory(self, bot: IDABot) -> None:
        """Builds a factory when necessary."""
        factory = UnitType(UNIT_TYPEID.TERRAN_FACTORY, bot)
        factory_techlab = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, bot)

        if workplaces[0] == self:
            if can_afford(bot, factory) \
                    and bot.have_one(UNIT_TYPEID.TERRAN_BARRACKS) \
                    and len(self.factories) < self.max_number_of_factories \
                    and not currently_building(bot, UNIT_TYPEID.TERRAN_FACTORY) \
                    and not self.is_building_unittype(factory)\
                    and len(self.miners) > 5:
                location = self.building_location_finder(bot, factory_techlab)
                self.have_worker_construct(factory, location)

    # DP
    def upgrade_factory(self, factory: Unit, bot: IDABot) -> None:
        """Have given factory build a techlab on it."""
        factory_techlab = UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, bot)
        if can_afford(bot, factory_techlab):
            factory.train(factory_techlab)

    def building_location_finder(self, bot: IDABot, unit_type: UnitType) -> Point2D:
        """Finds a suitable location to build a unit of given type"""
        home_base = self.location.position.to_i()
        if unit_type == UnitType(UNIT_TYPEID.TERRAN_FACTORY, bot) or \
                unit_type == UnitType(UNIT_TYPEID.TERRAN_FACTORYTECHLAB, bot):
            return bot.building_placer.get_build_location_near(home_base,
                                                               unit_type, 39)
        elif unit_type == UnitType(UNIT_TYPEID.TERRAN_BARRACKS, bot):
            return bot.building_placer.get_build_location_near(home_base,
                                                               unit_type, 35)
        elif unit_type == UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, bot):
            return bot.building_placer.get_build_location_near(home_base,
                                                               unit_type, 20)
        else:
            raise Exception("Found location is bad.")

    # ---------- HANDLERS ----------
    # Methods that builds structures.

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

            elif unit.unit_type.unit_typeid in grounded_command_centers_TYPEIDS:
                self.command_centers.append(unit)

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

            if unit in self.command_centers:
                self.command_centers.remove(unit)

    def get_units(self) -> List[Unit]:
        """Get all units in workplace."""
        return (self.workers
                + self.others
                + self.barracks
                + self.factories
                + self.command_centers)

    def has_unit(self, unit: Unit) -> bool:
        """Check if workplace has unit."""
        return unit in self.get_units()

    # ZW
    def add_mineral_field(self, mineral_field: Unit):
        """Add a mineral_field to the workplace."""
        if mineral_field.minerals_left_in_mineralfield > 0 \
                and not any(map(lambda mf: mineral_field == mf,
                                self.mineral_fields)):
            self.mineral_fields.append(mineral_field)

    # ZW
    def add_geyser(self, geyser: Unit):
        """Add a geyser to the workplace."""
        if geyser.gas_left_in_refinery \
                and not any(map(lambda g: geyser == g,
                                self.mineral_fields)):
            self.geysers.append(geyser)

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

    def add_barracks(self, barrack: Unit) -> None:
        """Adds a barrack to the workplace."""
        self.barracks.append(barrack)
        
    def add_factory(self, factory: Unit) -> None:
        """Adds a factory to the workplace."""
        self.factories.append(factory)

    # ---------- PROPERTIES ----------
    # Values that are trivial calculations but important for the object

    @property
    def max_number_of_barracks(self) -> int:
        """return the max number of barracks"""
        return min(1 * len(workplaces), 6)

    @property
    def max_number_of_factories(self) -> int:
        """Return the max number of factories"""
        return min((1 * len(workplaces)), 2)

    @property
    def small_number_of_barracks(self) -> int:
        """return number of barracks for base expansions"""
        return 1

    # ---------- MISC ----------
    # Other needed functions.

    # DP
    def get_scout(self) -> Union[Unit, None]:
        """Returns a suitable scout (worker)"""
        worker = self.get_suitable_worker_and_remove()
        if worker:
            add_scout(worker)
        return worker

    def flush_units(self) -> List[Unit]:
        """Remove all but a few workers (not structures)."""
        free = []
        i = 0
        while i < len(self.get_units()):
            unit = self.get_units()[i]
            if not unit.unit_type.is_building and unit not in self.builders \
                    and not self.is_gaser_in_refinery(unit):
                if unit not in self.workers or len(self.workers) > 3:
                    self.remove(unit)
                    unit.stop()
                    free.append(unit)
                    continue

            i += 1
        return free

    def within_proximity(self, pos: Point2D) -> bool:
        """Return True if the point is within the proximity of the base."""
        return pos.squared_dist(self.location.position) < self.safe_distance**2

    def str_worker(self, worker: Unit) -> str:
        """Create a string for a worker to be more informative."""
        return (str(worker) + ":" + str(worker.id) + "  on "
                + str(workplaces.index(self)))


# ========== END OF WORKPLACE ==========

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
    closest = [None, None]
    distance = [0, 0]
    for workplace in workplaces:
        if workplace.wants_scvs > 0:
            if not closest[0] or distance[0] > workplace.location.position.dist(pos)\
                    / workplace.wants_scvs:
                closest[0] = workplace
                distance[0] = workplace.location.position.dist(pos) \
                    / workplace.wants_scvs
        else:
            if not closest[1] or distance[1] > workplace.location.position.dist(pos):
                closest[1] = workplace
                distance[1] = workplace.location.position.dist(pos)

    return closest[0] if closest[0] else closest[1]


# ZW
def find_unit_workplace(unit: Unit) -> Union[Workplace, None]:
    for workplace in workplaces:
        if workplace.has_unit(unit):
            return workplace
    return None
