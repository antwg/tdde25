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
            create_troop_defending(Point2D(114, 46))
        else:
            create_troop_defending(Point2D(37, 121))
        create_workplace(self.base_location_manager
                         .get_player_starting_base_location(PLAYER_SELF), self)

        # workplaces[0].max_number_of_barracks = 3
        # workplaces[0].max_number_of_factories = 2

        # self.debug_give_all_resources()

        # self.points = []

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        self.look_for_new_units()

        print_debug(self)

        for workplace in workplaces:
            workplace.on_step(self)

        for troop in all_troops():
            troop.on_step(self)
            if troop.is_attackers and troop.satisfied and troop.have_all_reached_target:
                troop.march_units(self.base_location_manager.get_player_starting_base_location(PLAYER_ENEMY).position)

        self.train_scv()
        if self.should_train_marines:
            self.train_marine()
        if self.should_train_tanks:
            self.train_tank()
        self.expansion()
        # self.scout()

        
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

    def on_lost_my_unit(self, unit: Unit):
        """Called each time a unit is killed."""
        # Try removing from troop if in any
        troop = find_unit_troop(unit)
        if troop:
            troop.remove(unit)

        work = find_unit_workplace(unit)
        if work:
            work.remove(unit)

        # remove scout from scouts list
        if unit in scouts:
            remove_scout(unit)

    def on_idle_my_unit(self, unit: Unit):
        """Called each time a unit is idle."""
        troop = find_unit_troop(unit)
        if troop:
            troop.on_idle(unit, self)

        work = find_unit_workplace(unit)
        if work:
            work.on_idle_my_unit(unit, self)

    def on_new_my_unit(self, unit: Unit):
        """Called each time a new unit is noticed."""

        # Places building in right workplace (base location)
        add_to_workplace = False

        if unit.unit_type.is_building:
            for workplace in workplaces:
                if workplace.has_build_target(unit):
                    workplace.on_building_completed(unit)
                    break

        # lowers a supplydepot when done building
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)

        # add marine to closest troop wanting marines
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
            troop = marine_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # add marine to closest troop wanting tanks
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BUNKER:
            troop = bunker_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # add tank to closest troop wanting tanks
        elif unit.unit_type.unit_typeid in [UNIT_TYPEID.TERRAN_SIEGETANK,
                                            UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]:
            troop = tank_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # adds refinery to workplace at the end
        elif unit.unit_type.unit_typeid in refineries_TYPEIDS:
            add_to_workplace = True

        # adds barracks to workplace at the end
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BARRACKS:
            add_to_workplace = True

        # adds SCV to closest workplace wanting SCVs
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            workplace = scv_seeks_workplace(unit.position)
            if workplace:
                workplace.add(unit)

        # add commandcenter to workplace at the end
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            add_to_workplace = True
            if len(workplaces) == 3:
                if self.side() == 'right':
                    create_troop_attacking(Point2D(114, 46))
                else:
                    create_troop_attacking(Point2D(37, 121))

        # adds factory to workplace, then tries to build techlab        
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_FACTORY:
            add_to_workplace = True

        # add scv to closest workplace wanting SCVs
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            work = scv_seeks_workplace(unit.position)
            if work:
                work.add(unit)

        # if add_to_workplace is true from other if statments, add building to workplace.
        # also upgrades factory if possible (only possible when unit is factory)
        if add_to_workplace:
            work = closest_workplace(unit.position)
            if work:
                work.add(unit)

    def on_discover_unit(self, unit: Unit):
        """Called when a unit is discovered, even when new_my_unit."""
        if unit.unit_type.unit_typeid in minerals_TYPEIDS and unit.minerals_left_in_mineralfield > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_mineral_field(unit)

        elif unit.unit_type.unit_typeid in geysers_TYPEIDS and unit.gas_left_in_refinery > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_geyser(unit)

        # elif unit.unit_type.unit_typeid in grounded_command_centers_TYPEIDS \
        #    and unit.player == PLAYER_ENEMY:

    def on_lost_unit(self, unit: Unit):
        """Called when a unit is lost, even when lost_my_unit."""
        if unit.unit_type.unit_typeid in minerals_TYPEIDS:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.mineral_fields.remove(unit)

    remember_these: List[Unit] = []

    def look_for_new_units(self):
        """Find units that has not been noticed by the bot."""
        temp_remember_these = self.remember_these.copy()
        # Checks for new units
        for unit in self.get_all_units():
            if unit not in temp_remember_these:
                if unit.is_completed and unit.is_alive and unit.is_valid \
                        and self.map_tools.is_explored(unit.position):
                    if unit.owner == self.id:
                        self.on_new_my_unit(unit)
                    self.on_discover_unit(unit)
                self.remember_these.append(unit)

            else:
                temp_remember_these.remove(unit)
                if not unit.is_completed or not unit.is_alive or not unit.is_valid:
                    if unit.owner == self.id:
                        self.on_lost_my_unit(unit)
                    self.on_lost_unit(unit)
                    self.remember_these.remove(unit)

            # If idle call on_idle_unit()
            if unit.is_idle and unit.owner == self.id:
                self.on_idle_my_unit(unit)

        for remembered_unit in temp_remember_these:
            pass

    # DP
    def scout(self):
        """Finds suitable scout (miner) that checks all base locations based on chords"""
        if len(defenders) >= 1:
            if not scouts:
                # Finds and adds scout to scouts
                workplaces[-1].get_scout()
            if not all_base_chords:
                # Gets all base chords
                for cords in choke_point_dict:
                    all_base_chords.append(cords)

            if len(all_base_chords) > 0:
                scout = scouts[0]
                closest_base = self.closest_base(scout.position, all_base_chords)
                # Move to closest base chord. If there or idle, go to next site.
                if scout.is_idle or scout.position.dist(Point2D(closest_base.x, closest_base.y)) <= 1.5:
                    scout.move(closest_base)
                    all_base_chords.remove((closest_base.x, closest_base.y))

    def closest_base(self, pos: Point2D, locations):
        """Checks the closest base_location to a position"""
        closest = None
        distance = 0
        for base_chords in locations:
            base = Point2D(base_chords[0], base_chords[1])
            # Point2D.dist(...) is a function in scai_backbone
            if not closest or distance > base.dist(pos):
                closest = base
                distance = base.dist(pos)

        return closest

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

    def currently_building(self, unit_type): # AW
        """"Checks if a unit is currently being built"""
        # TODO: Rewrite/Delete?
        return any([unit.build_percentage < 1 for unit in
                    get_my_type_units(self, unit_type)])

    # ZW
    def have_one(self, utid: Union[UNIT_TYPEID, UnitType]) -> bool:
        """Check if there exists at least one of these units in my_units."""
        if isinstance(utid, UNIT_TYPEID):
            for unit in self.get_my_units():
                if unit.unit_type.unit_typeid == utid:
                    return True
        elif isinstance(utid, UnitType):
            for unit in self.get_my_units():
                if unit.unit_type == utid:
                    return True
        return False

    # ZW
    def train_marine(self):
        """Train marines if more are required."""

        # ___Try to fill troops by producing marines___
        barracks = self.should_train_marines
        marine = UnitType(UNIT_TYPEID.TERRAN_MARINE, self)
        # To stop overflow of produce
        not_promised_marine = len(list(filter(
            lambda b: b.is_constructing(marine), self.get_my_units())))

        for troop in all_troops():
            if troop.wants_marines - not_promised_marine > 0\
                    and can_afford(self, marine):

                barrack = get_closest_unit(
                    list(filter(lambda b: b.is_idle, barracks)),
                    troop.target_pos)

                if barrack:
                    barrack.train(marine)

            not_promised_marine -= troop.wants_marines

        self.should_train_marines = []

    # ZW
    def train_tank(self):
        """Train tanks if more are required."""

        tank = UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self)

        if can_afford(self, tank):
            factories = self.should_train_tanks

            # To stop overflow of produce
            not_promised_tanks = len(list(filter(
                lambda b: b.is_constructing(tank), self.get_my_units())))

            for troop in all_troops():
                if troop.wants_tanks - not_promised_tanks > 0:

                    factory = get_closest_unit(
                        list(filter(lambda b: b.is_idle, factories)),
                        troop.target_pos)

                    if factory:
                        factory.train(tank)

                not_promised_tanks -= troop.wants_tanks

        self.should_train_tanks = []

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

    def squared_distance(self, p1, p2):  # AW
        """Calculates the squared distance between 2 points"""
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

    def choke_points(self, coordinates) -> Point2D:  # AW
        """Returns the appropriate choke point"""
        return Point2D(choke_point_dict[coordinates][0],
                       choke_point_dict[coordinates][1])

    def troops_full(self):  # AW
        """Returns true if all troops are full"""
        for troop in all_troops():
            if troop.wants_marines <= 1:
                return True

    def expansion(self):  # AW
        """Builds new command center when needed"""
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position

        tot_marines = 0
        for troop in defenders:
            tot_marines += len(troop.marines)

        if (tot_marines >= len(workplaces) * 8)\
                and can_afford(self, command_center_type)\
                and not currently_building(self, command_center)\
                and closest_workplace(location).get_suitable_builder():

            workplace = closest_workplace(location)
            worker = workplace.get_suitable_worker_and_remove()

            if worker:
                new_workplace = create_workplace\
                    (self.base_location_manager.get_next_expansion(PLAYER_SELF),
                     self)

                new_workplace.add(worker)
                new_workplace.have_worker_construct(command_center_type,
                                                    location)

            point = self.choke_points((location.x, location.y))
            create_troop_defending(point)


if __name__ == "__main__":
    MyAgent.bootstrap()
