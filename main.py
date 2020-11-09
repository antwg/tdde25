import time
import random

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

        self.build_supply_depot()
        self.mine_minerals()
        self.train_scv()

    # ZW
    def train_scv(self):
        """Builds a SCV if possible and necessary, not regarding to where
        and why."""

        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        unit_cost = scv_type.mineral_price
        scvs = self.get_my_workers()

        # Fetches first best base, not going to work with expansions.
        command_centers = self \
            .get_my_type_units(UNIT_TYPEID.TERRAN_COMMANDCENTER)
        if command_centers:
            command_center = command_centers[0]

            if len(scvs) < 16 and unit_cost <= self.minerals \
                    and not command_center.is_training:
                command_center.train(scv_type)

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
    def get_my_type_units(self, searched_type: UnitTypeID):
        """Get all owned units with given unit type."""
        units = []
        for unit in self.get_my_units():
            if unit.unit_type.unit_typeid == searched_type:
                units.append(unit)
        return units

    def get_start_base_minerals(self):
        """Returns list of minerals (units) within starting base"""
        # Base location can be changed later on, making it work with expansions
        start_location = self.base_location_manager \
            .get_player_starting_base_location(PLAYER_SELF)
        return start_location.minerals

    def currently_building_supply_depot(self):
        """"Checks if a supply depot is being built"""
        value = 0
        for unit in self.get_my_units():
            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT\
                    and not unit.is_completed:
                value = value + 1
        if value >= 1:
            return True
        else:
            return False

    def build_supply_depot(self): #AW
        """Builds a supply depot when necessary."""
        home_base = self \
            .base_location_manager.get_player_starting_base_location(PLAYER_SELF).position
        home_base_2di = Point2DI(int(home_base.x), int(home_base.y))
        supply_depot = UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)
        location = self.building_placer.get_build_location_near(home_base_2di, supply_depot)

        worker = random.choice(self.get_my_workers())

        if (self.current_supply / self.max_supply) >= 0.8 \
                and self.max_supply < 200 \
                and self.minerals >= 200 \
                and not self.currently_building_supply_depot():
            Unit.build(worker, supply_depot, location)


if __name__ == "__main__":
    MyAgent.bootstrap()
