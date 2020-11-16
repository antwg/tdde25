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
        .get_player_starting_base_location(PLAYER_SELF))

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        for workplace in workplaces:
            workplace.on_step(self)
        ScaiBackbone.on_step(self)
        print_debug(self)
       # self.get_coords()
        self.build_barrack()
        self.build_supply_depot()
       # self.mine_minerals()
        self.train_scv()
       # self.build_refinery()
       # self.gather_gas()
        self.train_marine()
        self.defence()
        self.expansion()

    # DP
    def mine_minerals(self):
        """Makes workers mine at starting base"""
        for unit in self.get_my_workers(self):
            for workplace in workplaces:
                if unit.is_idle and unit not in workplace:


                    if marines:
                        for marine in marines:
                            troop = marine_seeks_troop(marine.position)
                            if troop:
                                troop += marine



    def is_worker_collecting_gas(self, worker):
        """ Returns: True if a Unit `worker` is collecting gas, False otherwise """

        def squared_distance(unit_1, unit_2):
            p1 = unit_1.position
            p2 = unit_2.position
            return (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2

        for refinery in get_my_refineries(self):
            if refinery.is_completed and squared_distance(worker, refinery) < 2 ** 2:
                return True

    # ZW
    def can_afford(self, unit_type: UnitType) -> bool:
        """Returns whenever a unit is affordable. """
        return self.minerals >= unit_type.mineral_price \
            and self.gas >= unit_type.gas_price \
            and self.max_supply - self.current_supply \
            >= unit_type.supply_required

    # ZW
    def train_scv(self):
        """Builds a SCV if possible on a base if needed."""
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        base_locations = self.get_base_locations_with_grounded_cc()

        if self.can_afford(scv_type):
            for bl in base_locations:
                scvs = get_my_workers(self)
                ccs = list(filter(lambda cc: bl.contains_position(cc.position),
                             get_my_types_units(self,
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
                                  get_my_types_units(self, refineries_TYPEIDS)))
                need_scvs = 3 * len(refineries) + 2 * len(bl.mineral_fields)

                # If more scvs are required, try to produce more at closest cc
                if ccs and count_gatherers + count_promised < need_scvs \
                        or count_caretakers + count_promised < need_scvs:
                    cc = get_closest_unit(ccs, bl.position)
                    if cc.is_idle:
                        cc.train(scv_type)


    # ZW
    def train_marine(self):
        """Train marines if more are required."""

        # Try to fill troops with lone marines first
        marines = list(filter(lambda unit: not any([trp.has_unit(unit)
                                                    for trp in troops]),
                              get_my_type_units(self,
                                  UNIT_TYPEID.TERRAN_MARINE)))
        if marines:
            for marine in marines:
                troop = marine_seeks_troop(marine.position)
                if troop:
                    troop += marine

        # Try to fill troops by producing marines
        barracks = get_my_type_units(self, UNIT_TYPEID.TERRAN_BARRACKS)
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

        worker = random.choice(get_my_workers(self))

        if (self.current_supply / self.max_supply) >= 0.8\
                and self.max_supply < 200\
                and self.minerals >= 100\
                and not currently_building(self, UNIT_TYPEID.TERRAN_SUPPLYDEPOT):
            Unit.build(worker, supply_depot, location)

    def build_barrack(self): #AW
        """Builds a barrack when necessary."""
        home_base = (self.base_location_manager.
                     get_player_starting_base_location(PLAYER_SELF).position)
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        location = self.building_placer.get_build_location_near(home_base_2di,
                                                                barrack)
        worker = get_my_workers(self)[0]

        if self.minerals >= barrack.mineral_price\
                and len(get_my_type_units(self, UNIT_TYPEID.TERRAN_BARRACKS)) <\
                self.max_number_of_barracks()\
                and not currently_building(self, UNIT_TYPEID.TERRAN_BARRACKS):
            Unit.build(worker, barrack, location)

    def max_number_of_barracks(self): #AW
        """Determines the suitable number of barracks"""
        return len(self.base_location_manager.get_occupied_base_locations
                   (PLAYER_SELF)) * 2

    def get_base_locations_with_grounded_cc(self) -> List[BaseLocation]:
        """Get all base locations that have an owned command center."""
        base_locations = self.base_location_manager.base_locations
        command_centers = get_my_types_units(self, grounded_command_centers_TYPEIDS)
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
        worker = random.choice(get_my_workers(self))
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF).\
            depot_position

        if len(get_my_type_units(self, marines)) >= 8\
                and self.can_afford(command_center_type)\
                and not currently_building(self, command_center):
            Unit.build(worker, command_center_type, location)


if __name__ == "__main__":
    MyAgent.bootstrap()
