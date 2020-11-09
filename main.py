import time
import random
from typing import List

from scai_backbone import *

from debug import *
from extra import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_game_start(self)

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        # print_debug(self)
        self.build_barrack()
        self.build_supply_depot()
        self.mine_minerals()
        self.train_scv()

    def mine_minerals(self):
        """Makes workers mine at starting base"""
        for unit in self.get_my_workers():
            if unit.is_idle:
                unit.right_click(random.choice(self.get_start_base_minerals()))

    def get_my_workers(self):
        """Makes a list of workers"""
        workers = []
        for unit in self.get_my_units():
            if unit.unit_type.is_worker:
                workers.append(unit)

        return workers

    # ZW
    def can_afford(self, unit_type: UnitType) -> bool:
        """Returns whetever a unit is affordable. """
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
        scvs = self.get_my_workers()
        base_locations = self.get_base_locations_with_grounded_cc()

        if self.can_afford(scv_type):
            for bl in base_locations:
                count_gatherers = 0
                for scv in scvs:
                    if bl.contains_position(scv.position):
                        if scv.has_target:
                            if scv.target.unit_type.unit_typeid \
                                    in minerals_TYPEIDS:
                                count_gatherers += 1

                if count_gatherers < 16:
                    ccs = filter(lambda cc: bl.contains_position(cc.position),
                                 self.get_my_types_units(
                                     grounded_command_centers_TYPEIDS))
                    closest_cc = None
                    closest_dist = 0
                    for cc in ccs:
                        if not closest_cc \
                                or closest_dist < cc.position.dist(bl.position):
                            closest_cc = cc
                            closest_dist = cc.position.dist(bl.position)

                    if closest_cc.is_idle:
                        closest_cc.train(scv_type)

    def currently_building(self, unit_type):
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
        home_base = (self.base_location_manager.
                     get_player_starting_base_location(PLAYER_SELF).position)
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        barrack = UnitType(UNIT_TYPEID.TERRAN_BARRACKS, self)
        location = self.building_placer.get_build_location_near(home_base_2di,
                                                                barrack)
        worker = random.choice(self.get_my_workers())

        if self.minerals >= barrack.mineral_price\
                and len(self.get_my_type_units(UNIT_TYPEID.TERRAN_BARRACKS)) <\
                self.max_number_of_barracks()\
                and not self.currently_building(UNIT_TYPEID.TERRAN_BARRACKS):
            Unit.build(worker, barrack, location)


    def max_number_of_barracks(self):
        return len(self.base_location_manager.get_occupied_base_locations
                   (PLAYER_SELF)) * 2



if __name__ == "__main__":
    MyAgent.bootstrap()
