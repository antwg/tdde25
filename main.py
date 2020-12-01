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
        if self.side() == 'right':
            create_troop(Point2D(119, 47))
        else:
            create_troop(Point2D(33, 120))
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
        workplaces[-1].expansion(self)
        self.train_scv()
        self.train_marine()
        self.expansion()
        self.get_coords()

    def get_coords(self):
        """Prints position of all workers"""
        for unit in self.get_my_units():
            text = str(unit.position)
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))

    def side(self):
        """Return what side player spawns on"""
        start_location = self.base_location_manager.\
            get_player_starting_base_location(PLAYER_SELF).position
        start_location_tuple = (start_location.x, start_location.y)

        if start_location_tuple == (127.750000, 28.500000):
            return 'right'
        else:
            return 'left'

    def scout(self):
        if troops >= 2:
            scout = workplaces[-1].get_scout
            for base_location in BaseLocationManager.get_occupied_base_location(PLAYER_ENEMY):
                scout.move

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

        if unit in scouts:
            remove_scout(unit)

    def on_idle_unit(self, unit: Unit):
        """Called each time a unit is idle."""
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BARRACKS:
            self.train_marine()

    def on_new_my_unit(self, unit: Unit):
        """Called each time a new unit is noticed."""
        self.train_marine()
        self.defence()
        # self.look_for_new_units()

        if unit.unit_type.is_building:
            for workplace in workplaces:
                workplace.on_building_completed(unit)

        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)
            work = closest_workplace(unit.position)
            if work:
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
                # print("ref built")
                work.update_workers(self)

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BARRACKS:
            work = closest_workplace(unit.position)
            if work:
                work.add_barracks(unit)
                work.update_workers(self)

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            print("should be making a workplace")

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            workplace = closest_workplace(unit.position)
            if workplace:
                print("work is now added", workplace.location, workplace.miners)
                workplace += unit

        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_FACTORY:
            work = closest_workplace(unit.position)
            if work:
                work.add_factory(unit)
                work.update_workers(self)

    remember_these: List[Unit] = []

    def look_for_new_units(self):
        """Find units that has not been noticed by the bot."""
        temp_remember_these = self.remember_these.copy()
        for unit in self.get_all_units():
            # If idle call on_idle_unit()
            if unit.is_idle:
                self.on_idle_unit(unit)

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

    def choke_points(self, coordinates) -> Point2D:
        """Returns the appropriate choke point"""
        choke_point_dict = {(59, 28): (52, 35), (125, 137): (127, 128),
                            (58, 128): (67, 116), (125, 30): (119, 47),
                            (92, 139): (99, 130), (25, 111): (44, 101),
                            (26, 81): (30, 67), (86, 114): (93, 102),
                            (91, 71): (88, 82), (93, 39): (85, 50),
                            (126, 56): (108, 67), (65, 53): (69, 58),
                            (125, 86): (121, 100), (26, 30): (23, 39),
                            (26, 137): (33, 120)}

        return Point2D(choke_point_dict[coordinates][0],
                       choke_point_dict[coordinates][1])

    def expansion(self):  # AW
        """Builds new command center when needed"""
        marines = UNIT_TYPEID.TERRAN_MARINE
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position
        workplace = closest_workplace(location)
        worker = workplace.get_suitable_worker_and_remove()

        if len(get_my_type_units(self, marines)) >= \
                len(workplaces) * 8\
                and can_afford(self, command_center_type)\
                and not currently_building(self, command_center)\
                and worker:

            new_workplace = create_workplace\
                (self.base_location_manager.get_next_expansion(PLAYER_SELF),
                 self)

            new_workplace += worker
            new_workplace.have_worker_construct(command_center_type, location)

            create_troop(self.choke_points((location.x, location.y)))

if __name__ == "__main__":
    MyAgent.bootstrap()
