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
        create_workplace(self.base_location_manager \
        .get_player_starting_base_location(PLAYER_SELF), self)

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        self.look_for_new_units()
        print_debug(self)
       # self.get_coords()
        self.worker_do()
        for workplace in workplaces:
            workplace.on_step(self)
        self.train_scv()
        self.train_marine()
        self.defence()

    def side(self):
        """Return what side player spawns on"""
        start_location = self.base_location_manager.\
            get_player_starting_base_location(PLAYER_SELF).position
        start_location_tuple = (start_location.x, start_location.y)

        if start_location_tuple == (127.750000, 28.500000):
            return 'right'
        else:
            return 'left'

    def on_lost_my_unit(self, unit: Unit):
        """Called each time a unit is killed."""
        # Try removing from troop if in any
        troop = find_unit_troop(unit)
        if troop:
            troop.member_lost(unit)

        # Remove minerals from workplace.miners_targets
        if unit.unit_type.unit_typeid in minerals_TYPEIDS:
            for workplace in workplaces:
                if unit in workplace.miners_targets:
                    workplace.miners_targets.remove(unit)

    def on_new_my_unit(self, unit: Unit):
        """Called each time a new unit is noticed."""
        # print(unit)
        self.train_marine()
        self.defence()
        self.expansion()
        self.look_for_new_units()

        if unit.unit_type.is_building:
            for workplace in workplaces:
                workplace.on_building_completed(unit)

        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)
            work = closest_workplace(unit.position)
            # print("sup build gone")
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
                print("ref built")
                work.update_workers(self)

        elif unit.unit_type.unit_typeid is UNIT_TYPEID.TERRAN_BARRACKS:
            work = closest_workplace(unit.position)
            work.add_barracks(unit)
            work.update_workers(self)

        elif unit.unit_type.unit_typeid is UNIT_TYPEID.TERRAN_COMMANDCENTER:
            print("should be making a workplace")

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            workplace = scv_seeks_workplace(unit.position)
            if workplace:
                workplace += unit

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
                    self.on_lost_my_unit(unit)
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
        """Assigns starting workers/ idle workers to a jobs to closest workplace"""
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
            ccs = get_my_types_units(self, grounded_command_centers_TYPEIDS)
            ccs = list(filter(lambda cc: cc.is_idle, ccs))

            for workplace in workplaces:
                if not ccs:
                    break
                count_needed = workplace.wants_scvs
                while count_needed > 0 and ccs:
                    trainer = get_closest_unit(ccs, workplace.location.position)
                    trainer.train(scv_type)
                    count_needed -= 1
                    ccs.remove(trainer)

    # ZW
    def train_scv_old(self):
        """OLD: Builds a SCV if possible on a base if needed."""
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
        # TODO: Rewrite
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
        for i, troop in enumerate(troops):
            if (troop.target.x, troop.target.y) != \
                    (self.choke_points(i).x, self.choke_points(i).y):
                troop.move_units(self.choke_points(i))

    def choke_points(self, base_nr):
        """Returns the appropriate choke point"""
        left = [Point2D(33, 120), Point2D(37, 110), Point2D(67, 117),
                Point2D(65, 86), Point2D(37, 110)]
        right = [Point2D(119, 47), Point2D(114, 58), Point2D(85, 50),
                 Point2D(60, 62), Point2D(98, 89), Point2D(41, 33)]

        if self.side() == 'left':
            return left[base_nr]
        elif self.side() == 'right':
            return right[base_nr]
        else:
            raise IndexError('Choke point list out of range')

if __name__ == "__main__":
    MyAgent.bootstrap()
