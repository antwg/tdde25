import time
import random
from copy import deepcopy
from typing import List

from scai_backbone import *
from debug import *
from extra import *
from armies import *
from workplace import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_game_start(self)
        create_troop(Point2D(35, 123))
        self.unit = None
        create_workplace(self.base_location_manager \
        .get_player_starting_base_location(PLAYER_SELF), self)

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        self.look_for_new_units()
        self.build_barrack()
        print_debug(self)
       # self.get_coords()
        self.worker_do()
        for workplace in workplaces:
            workplace.on_step(self)
        self.build_supply_depot()
        self.build_barrack()
        self.train_scv()
        self.train_marine()
        self.defence()
        self.expansion()

    def side(self):
        """Return what side player spawns on"""
        start_location = self.base_location_manager.\
            get_player_starting_base_location(PLAYER_SELF).position
        start_location_tuple = (start_location.x, start_location.y)

        if start_location_tuple == (127.750000, 28.500000):
            return 'right'
        else:
            return 'left'

    def on_new_my_unit(self, unit: Unit):
        """Called each time a new unit is noticed."""
        print(unit)
        self.train_marine()
        self.defence()
        self.expansion()
        self.look_for_new_units()

    def on_new_my_unit(self, unit: Unit):
        """Called each time a new unit is noticed."""
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)
            work = closest_workplace_building(unit.position)
            print("sup build gone")
            work.update_workers(self)

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
            troop = marine_seeks_troop(unit.position)
            if troop:
                troop += unit

        elif unit.unit_type.unit_typeid in [UNIT_TYPEID.TERRAN_SIEGETANK,
                                            UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]:
            troop = tank_seeks_troop(unit.position)
            if troop:
                troop += unit

        elif unit.unit_type.unit_typeid in refineries_TYPEIDS:
            work = closest_workplace(unit.position)
            if work:
                work.add_refinery(unit)
                work.update_workers(self)

        elif unit.unit_type.unit_typeid is UNIT_TYPEID.TERRAN_BARRACKS:
            work = closest_workplace_building(unit.position)
            print("barack build gone")
            work.update_workers(self)

        elif unit.unit_type.unit_typeid is UNIT_TYPEID.TERRAN_COMMANDCENTER:
            print("should be making a workplace")


    remember_these: List[Unit] = []

    def look_for_new_units(self):
        """Find units that has not been noticed by the bot."""
        temp_remember_these = self.remember_these.copy()
        for unit in self.get_all_units():
            if unit not in temp_remember_these:
                if unit.is_completed and unit.is_alive and unit.is_valid:
                    self.remember_these.append(unit)
                    if unit.owner == self.id:
                        self.on_new_my_unit(unit)
            else:
                temp_remember_these.remove(unit)
                if not unit.is_completed or not unit.is_alive or not unit.is_valid:
                    self.remember_these.remove(unit)
        for remembered_unit in temp_remember_these:
            # How to handle not found units?
            pass


    # ZW
    def is_worker_collecting_minerals(self, worker: Unit):
        """Returns: True if a unit is collecting Minerals, False otherwise."""
        # TODO: Make it return the value correctly
        # ARGH!!! AbilityID is the one to solve it but it's broken!
        # An AbilityID can't be compared to another or a ABILITY_ID. WHY?!
        return worker.unit_type.is_worker \
            and worker.has_target \
            and worker.target.unit_type.unit_typeid in minerals_TYPEIDS \
            or (worker.is_carrying_minerals
                and worker.target.unit_type.unit_typeid
                in grounded_command_centers_TYPEIDS)

    def worker_do(self):
        for unit in get_my_workers(self):
            for workplace in workplaces:
                if unit.is_idle and not workplace.has_unit(unit):
                    work = closest_workplace(unit.position)
                    work += unit

    # ZW
    def train_scv(self):
        """Builds a SCV if possible on a base if needed."""
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)

        if can_afford(self, scv_type):
            base_locations = self.base_location_manager.base_locations

            for bl in base_locations:


                ccs = list(filter(lambda cc: bl.contains_position(cc.position),
                             get_my_types_units(self,
                                                grounded_command_centers_TYPEIDS)))

                if not ccs:  # If no grounded command centers were found...
                    continue  # ...continue on to next base location

                scvs = get_my_workers(self)

                count_gatherers = 0
                count_caretakers = 0
                count_promised = 0

                # Count all scvs in base_location and note if their gathering resources
                for scv in scvs:
                    if bl.contains_position(scv.position):
                        # Scv in base location
                        count_caretakers += 1
                        if scv.has_target:
                            if self.is_worker_collecting_minerals(scv):
                                # Scv is gathering resources
                                count_gatherers += 1
                # Count all scvs that are being produced at location
                for cc in ccs:
                    if cc.is_constructing(scv_type):
                        count_promised += 1

                # Required least amount of caretakers
                refineries = list(filter(lambda ref: ref.gas_left_in_refinery,
                                  get_my_types_units(self, refineries_TYPEIDS)))
                need_scvs = 3 * len(refineries) + 2 * len(bl.mineral_fields) + 2


                # If more scvs are required, try to produce more at closest cc
                if ccs and count_caretakers + count_promised < need_scvs:
                    #    or count_gatherers + count_promised < need_scvs:
                    cc = get_closest_unit(ccs, bl.position)
                    if cc.is_idle:
                        cc.train(scv_type)


    def currently_building(self, unit_type): #AW
        """"Checks if a unit is currently being built"""
        return any([unit.build_percentage < 1 for unit in
                    get_my_type_units(self, unit_type)])


    # ZW
    def train_marine(self):
        """Train marines if more are required."""

        # ___Try to fill troops by producing marines___
        barracks = get_my_type_units(self, UNIT_TYPEID.TERRAN_BARRACKS)
        marine = UnitType(UNIT_TYPEID.TERRAN_MARINE, self)
        # To stop overflow of produce
        not_promised_marine = len(list(filter(
            lambda b: b.is_constructing(marine), barracks)))

        for troop in troops:
            if troop.wants_marines - not_promised_marine > 0\
                    and can_afford(self, marine):


                barrack = get_closest_unit(
                    list(filter(lambda b: b.is_idle, barracks)),
                    troop.target)

                if barrack:
                    barrack.train(marine)

            not_promised_marine -= troop.wants_marines

    def building_location_finder(self, unit_type):
        """Finds a suitable location to build a unit of given type"""
        home_base = self.base_location_manager.\
            get_player_starting_base_location(PLAYER_SELF).position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        location = self.building_placer.get_build_location_near(home_base_2di,
                                                                unit_type)
        if self.building_placer.can_build_here_with_spaces(location.x, location.y,
                                                           unit_type, 5):
            return location
        else:
            raise Exception
        return location

    def squared_distance_p2d(self, p1: Point2D, p2: Point2D) -> float:
        """Gives the squared distance between two Point2D points"""
        return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

    def nearest_worker(self, location):
        """Finds the nearest worker given a location"""
        return self.nearest_unit_list(get_my_workers(self), location)

    def nearest_unit_list(self, units, location):
        """Finds the nearest unit in a list given a location"""
        unit_list = []
        for unit in units:
            distance = self.squared_distance_p2d(location, unit.position)
            unit_tuple = (distance, unit)
            unit_list.append(unit_tuple)
        return sorted(unit_list, key=lambda tup: tup[0])[0][1]

    def build_supply_depot(self):  # AW
        """Builds a supply depot when necessary."""
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        location = self.building_location_finder(supply_depot)

        if (self.current_supply / self.max_supply) >= 0.8\
                and self.max_supply < 200\
                and self.minerals >= 100\
                and not currently_building(self, UNIT_TYPEID.TERRAN_SUPPLYDEPOT):
            # worker = closest_workplace(home_base).get_suitable_builder()
            worker = random.choice(get_my_workers(self))
            Unit.build(worker, supply_depot, location)

    def build_barrack(self):  # AW
        """Builds a barrack when necessary."""
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        location = self.building_location_finder(barrack)

        if self.minerals >= barrack.mineral_price\
                and len(get_my_type_units(self, UNIT_TYPEID.TERRAN_BARRACKS)) <\
                self.max_number_of_barracks()\
                and not self.currently_building(UNIT_TYPEID.TERRAN_BARRACKS):
            print(self.currently_building(UNIT_TYPEID.TERRAN_BARRACKS))

            # worker = closest_workplace(home_base).get_suitable_builder()
            worker = random.choice(get_my_workers(self))

            Unit.build(worker, barrack, location)
            print('building barrack')

    def max_number_of_barracks(self):  # AW
        """Determines the suitable number of barracks"""
        return len(self.base_location_manager.get_occupied_base_locations
                   (PLAYER_SELF))

    def squared_distance(self, p1, p2): #AW
        """Calculates the squared distance between 2 points"""
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

    def start_choke_point(self):  # AW
        """Returns the choke point closest to command center"""
        if self.side() == 'right':
            return Point2D(119, 47)
        else:
            return Point2D(33, 120)

    def defence(self):  # AW
        """Moves troops to a nearby choke point"""
        bases = len(self.base_location_manager.get_occupied_base_locations
                    (PLAYER_SELF)) - 1
        target_coords = (troops[bases].target.x, troops[bases].target.y)
        choke_coords = (self.choke_points(bases).x, self.choke_points(bases).y)

        if target_coords != choke_coords:
            troops[0].move_units(self.choke_points(bases))

    def choke_points(self, base_nr):
        """Returns the appropriate choke point"""
        left = [Point2D(33, 120), Point2D(37, 110), Point2D(37, 110)]
        right = [Point2D(119, 47), Point2D(114, 58), Point2D(114, 58)]

        if self.side() == 'left':
            return left[base_nr]
        elif self.side() == 'right':
            return right[base_nr]
        else:
            raise IndexError('Choke point list out of range')

    def expansion(self):  # AW
        """Builds new command center when needed"""
        marines = UNIT_TYPEID.TERRAN_MARINE
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position


        worker = self.nearest_worker(location)

        if len(get_my_type_units(self, marines)) >= \
                len(self.base_location_manager.get_occupied_base_locations
                    (PLAYER_SELF)) * 8\
                and can_afford(self, command_center_type)\
                and not self.currently_building(command_center):


            worker = closest_workplace(self.base_location_manager.get_next_expansion(PLAYER_SELF). \
                                       position).get_suitable_builder()


            Unit.build(worker, command_center_type, location)
            create_troop(self.choke_points(len(self.base_location_manager.
                                               get_occupied_base_locations(PLAYER_SELF))))

if __name__ == "__main__":
    MyAgent.bootstrap()
