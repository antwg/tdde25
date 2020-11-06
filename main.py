import time
import random

from scai_backbone import *

from debug import *

# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_game_start(self)

    def on_step(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)
        print_debug(self)
        test = self.base_location_manager.get_player_starting_base_location(PLAYER_SELF).position
        test2 = (int(test.x), int(test.y))
        print(test)
        print(test2)
        self.build_supply_depot()
        self.mine_minerals()

    def mine_minerals(self):
        for unit in self.get_my_workers():
            if unit.is_idle:
                unit.right_click(random.choice(self.get_start_base_minerals()))

    def get_my_workers(self):
        workers = []
        for unit in self.get_my_units():
            if unit.unit_type.is_worker:
                workers.append(unit)

        return workers

    def get_start_base_minerals(self):
        start_location = self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)
        return start_location.minerals

  #  def get_my_workers(self):
    #       return (lambda unit: unit.unit_type.is_worker, self.get_all_units())

    def build_supply_depot(self):  # AW
        """Builds supply depot when necessary"""
        if (self.current_supply / self.max_supply) <= 0.8 and \
                self.max_supply < 200 and self.minerals >= 100:
            Unit.build((random.choice(get_my_workers(self)),
                        UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
                        BuildingPlacer.get_build_location_near(
                            self.base_location_manager.get_player_starting_base_location(PLAYER_SELF),
                            UNIT_TYPEID.TERRAN_SUPPLYDEPOT))


if __name__ == "__main__":
    MyAgent.bootstrap()
