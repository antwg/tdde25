import time
import random
from typing import List

from scai_backbone import *
from debug import *
from extra import *
from armies import *
from funcs import *

job_dict = {}


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_game_start(self)
        create_troop(Point2D(35, 123))

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        print_debug(self, job_dict)
        #print_debug(self)
        #self.get_coords()
        self.build_barrack()
        self.build_supply_depot()
        self.mine_minerals()
        self.train_scv()
        self.build_refinery()
        self.gather_gas()
        self.train_marine()
        self.defence()
        self.expansion()

    # DP
    def mine_minerals(self):
        """Makes workers mine at starting base"""
        for unit in self.get_my_workers():
            if unit.is_idle and not self.is_worker_collecting_gas(unit):
                mineral = random.choice(self.get_start_base_minerals())
                unit.right_click(mineral)
                self.add_to_job(unit, mineral)

    def get_my_workers(self):
        """Makes a list of workers"""
        workers = []
        for unit in self.get_my_units():
            if unit.unit_type.is_worker:
                workers.append(unit)
        return workers

    def get_my_refineries(self):
        """ Returns a list of all refineries (list of Unit) """
        refineries = []
        for unit in self.get_my_units():
            if unit.unit_type.is_refinery:
                refineries.append(unit)
        return refineries

    def is_worker_collecting_gas(self, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        def squared_distance(unit_1, unit_2):
            p1 = unit_1.position
            p2 = unit_2.position
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for refinery in self.get_my_refineries():
            if refinery.is_completed and squared_distance(worker, refinery) < 2 ** 2:
                return True

    def get_refinery(self, geyser: Unit) -> Optional[Unit]:
        """
        Returns: A refinery which is on top of unit `geyser` if any, None otherwise
        """

        def squared_distance(p1: Point2D, p2: Point2D) -> float:
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for unit in self.get_my_units():
            if unit.unit_type.is_refinery and squared_distance(unit.position, geyser.position) < 1:
                return unit

        return None

    # DP
    def build_refinery(self):
        """Builds a refinery at base location, then calls for collection"""
        refinery = UnitType(UNIT_TYPEID.TERRAN_REFINERY, self)
        geysers_list = self.my_geysers()

        for geyser in geysers_list:
            worker = random.choice(self.get_my_workers())
            if not self.currently_building(UNIT_TYPEID.TERRAN_REFINERY) and \
                    self.get_refinery(geyser) is None and \
                    self.can_afford(refinery):
                worker.build_target(refinery, geyser)
                self.add_to_job(worker, geyser)
            elif self.get_refinery(geyser) is not None:
                print(list(job_dict.values()))
                self.add_to_job(list(job_dict.keys())[list(job_dict.values()).index(geyser)], self.get_refinery(geyser))

    # DP
    def gather_gas(self):
        """Gathers gas from all available refineries"""
        for refinery in self.get_my_refineries():
            amount = 0
            if refinery.is_completed:
                for unit in job_dict:
                    if job_dict[unit] == refinery:
                        amount += 1
                while amount < 3:
                    worker = random.choice(self.get_my_workers())
                    if job_dict[worker].unit_type.is_mineral:
                        worker.right_click(refinery)
                        self.add_to_job(worker, refinery)
                        amount += 1

    # DP
    def add_to_job(self, unit, target):
        job_dict[unit] = target

    # DP
    def get_my_mineral_miners(self):
        mineral_miner = []
        for unit in job_dict:
            if job_dict[unit].unit_type.is_mineral:
                mineral_miner.append(unit)
        return mineral_miner

    # DP
    def my_geysers(self):
        """Returns list of all geysers player has access to"""
        base_locations = self.base_location_manager.get_occupied_base_locations(PLAYER_SELF)
        geysers_base_list = []
        gey_list = []
        for base in base_locations:
            geysers_base_list.append(base.geysers)
            for geysers in geysers_base_list:
                gey_list += geysers

        return gey_list

    # ZW
    def can_afford(self, unit_type: UnitType) -> bool:
        """Returns whenever a unit is affordable. """
        return self.minerals >= unit_type.mineral_price \
            and self.gas >= unit_type.gas_price \
            and self.max_supply - self.current_supply \
            >= unit_type.supply_required

    # ZW
    def get_my_type_units(self, searched_type: UnitTypeID):
        """Get all owned units with given unit type."""
        units = []
        for unit in self.get_my_units():
            if unit.unit_type.unit_typeid == searched_type:
                units.append(unit)
        return units

    # ZW
    def get_my_types_units(self, searched_types: List[UnitTypeID]):
        """Get all owned units with oe of the given unit types."""
        units = []
        for unit in self.get_my_units():
            if unit.unit_type.unit_typeid in searched_types:
                units.append(unit)
        return units

    # DP
    def get_start_base_minerals(self):
        """Returns list of minerals (units) within starting base"""
        # Base location can be changed later on, making it work with expansions
        start_location = self.base_location_manager \
            .get_player_starting_base_location(PLAYER_SELF)
        return start_location.minerals

    # ZW
    def train_scv(self):
        """Builds a SCV if possible on a base if needed."""
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        base_locations = self.get_base_locations_with_grounded_cc()

        if self.can_afford(scv_type):
            for bl in base_locations:
                scvs = self.get_my_workers()
                ccs = list(filter(lambda cc: bl.contains_position(cc.position),
                             self.get_my_types_units(
                                 grounded_command_centers_TYPEIDS)))

                count_gatherers = 0
                count_caretakers = 0
                count_promised = 0

                # Count all scvs in base_location and note if their gathering resources
                for scv in scvs:
                    if bl.contains_position(scv.position):
                        # Scv in base location
                        count_caretakers += 1
                        if scv.has_target:
                            if scv.target.unit_type.unit_typeid \
                                    in minerals_TYPEIDS:
                                # Scv is gathering resources
                                count_gatherers += 1
                # Count all scvs that are being produced at location
                for cc in ccs:
                    if cc.is_constructing(scv_type):
                        count_promised += 1

                # Required least amount of caretakers
                refineries = list(filter(lambda ref: ref.gas_left_in_refinery,
                                  self.get_my_types_units(refineries_TYPEIDS)))
                need_scvs = 3 * len(refineries) + 2 * len(bl.mineral_fields)

                # If more scvs are required, try to produce more at closest cc
                if ccs and count_gatherers + count_promised < need_scvs \
                        or count_caretakers + count_promised < need_scvs:
                    cc = get_closest_unit(ccs, bl.position)
                    if cc.is_idle:
                        cc.train(scv_type)

    def currently_building(self, unit_type): #AW
        """"Checks if a unit is being built"""
        value = 0
        for unit in self.get_my_units():
            if unit.unit_type.unit_typeid == unit_type\
                    and not unit.is_completed:
                value = value + 1
        if value >= 1:
            return True
        else:
            return False

    # ZW
    def train_marine(self):
        """Train marines if more are required."""

        # Try to fill troops with lone marines first
        marines = list(filter(lambda unit: not any([trp.has_unit(unit)
                                                    for trp in troops]),
                              self.get_my_type_units(
                                  UNIT_TYPEID.TERRAN_MARINE)))
        if marines:
            for marine in marines:
                troop = marine_seeks_troop(marine.position)
                if troop:
                    troop += marine

        # Try to fill troops by producing marines
        barracks = self.get_my_type_units(UNIT_TYPEID.TERRAN_BARRACKS)
        marine = UnitType(UNIT_TYPEID.TERRAN_MARINE, self)
        # To stop overflow of produce
        already_producing = len(list(filter(lambda b: b.is_constructing(marine),
                                            barracks)))
        for troop in troops:
            if troop.wants_marines - already_producing\
                    and self.can_afford(marine):

                barrack = get_closest_unit(
                    list(filter(lambda b: b.is_idle, barracks)),
                    troop.target)

                if barrack:
                    barrack.train(marine)

            already_producing -= troop.wants_marines

    def build_supply_depot(self):  # AW
        """Builds a supply depot when necessary."""
        home_base = self \
            .base_location_manager.get_player_starting_base_location(PLAYER_SELF).position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        location = self.building_placer.get_build_location_near(home_base_2di, supply_depot)

        worker = random.choice(self.get_my_workers())

        if (self.current_supply / self.max_supply) >= 0.8\
                and self.max_supply < 200\
                and self.minerals >= 100\
                and not self.currently_building(UNIT_TYPEID.TERRAN_SUPPLYDEPOT):
            Unit.build(worker, supply_depot, location)

    def build_barrack(self): #AW
        """Builds a barrack when necessary."""
        home_base = (self.base_location_manager.
                     get_player_starting_base_location(PLAYER_SELF).position)
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        location = self.building_placer.get_build_location_near(home_base_2di,
                                                                barrack)
        worker = self.get_my_workers()[0]

        if self.minerals >= barrack.mineral_price\
                and len(self.get_my_type_units(UNIT_TYPEID.TERRAN_BARRACKS)) <\
                self.max_number_of_barracks()\
                and not self.currently_building(UNIT_TYPEID.TERRAN_BARRACKS):
            Unit.build(worker, barrack, location)

    def max_number_of_barracks(self): #AW
        """Determines the suitable number of barracks"""
        return len(self.base_location_manager.get_occupied_base_locations
                   (PLAYER_SELF)) * 2

    def get_base_locations_with_grounded_cc(self) -> List[BaseLocation]:
        """Get all base locations that have an owned command center."""
        base_locations = self.base_location_manager.base_locations
        command_centers = self \
            .get_my_types_units(grounded_command_centers_TYPEIDS)
        found = []
        for base_location in base_locations:
            if base_location.is_occupied_by_player(PLAYER_SELF):
                if any([base_location.contains_position(cc.position)
                        for cc in command_centers]):
                    found.append(base_location)
        return found

    def squared_distance(self, p1, p2): #AW
        """Calculates the squared distance between 2 points"""
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

    def nearest_choke_point(self): #AW
        """Returns the choke point closest to command center"""
        home_base = (self.base_location_manager.
                     get_player_starting_base_location(PLAYER_SELF).position)
        home_base_tuple = (int(home_base.x), int(home_base.y))
        point1 = (119, 47)
        point2 = (33, 120)

        if (self.squared_distance(home_base_tuple, point1)
                < self.squared_distance(home_base_tuple, point2)):
            return Point2D(119, 47)
        else:
            return Point2D(33, 120)

    def defence(self): #AW
        """Moves troops to a nearby choke point"""
        target_coords = (troops[0].target.x, troops[0].target.y)
        choke_coords = (self.nearest_choke_point().x,
                        self.nearest_choke_point().y)
        if target_coords != choke_coords:
            troops[0].move_units(self, self.nearest_choke_point())

    def expansion(self): #AW
        """Builds new command center when needed"""
        marines = UNIT_TYPEID.TERRAN_MARINE
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        worker = random.choice(self.get_my_workers())
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position

        if len(self.get_my_type_units(marines)) >= 8\
                and self.can_afford(command_center_type)\
                and not self.currently_building(command_center):
            Unit.build(worker, command_center_type, location)

    def get_mineral_fields(self, base_location: BaseLocation) -> List[Unit]: #Kurssidan
        """ Given a base_location, this method will find and return a list of
        all mineral fields (Unit) for that base """
        mineral_fields = []
        for mineral_field in base_location.mineral_fields:
            for unit in self.get_all_units():
                if unit.unit_type.is_mineral \
                        and mineral_field.tile_position.x == unit.tile_position.x \
                        and mineral_field.tile_position.y == unit.tile_position.y:
                    mineral_fields.append(unit)
        return mineral_fields

    def get_geysers(self, base_location: BaseLocation) -> List[Unit]: #Kurssidan
        """ Given a base_location, this method will find and return a list of
            all geysers for that base """
        geysers = []
        for geyser in base_location.geysers:
            for unit in self.get_all_units():
                if unit.unit_type.is_geyser \
                        and geyser.tile_position.x == unit.tile_position.x \
                        and geyser.tile_position.y == unit.tile_position.y:
                    geysers.append(unit)
        return geysers

if __name__ == "__main__":
    MyAgent.bootstrap()
