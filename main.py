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

    def build_supply_depot(self): #AW
        """Builds supply depot when necessary"""
        if (self.current_supply / self.max_supply) <= 0.8 and \
                self.max_supply < 200 and self.minerals >= 100:
            Unit.build((random.choice(get_my_workers(self)),
                       UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
                       BuildingPlacer.get_build_location_near(self.base_location_manager.get_player_starting_base_location(PLAYER_SELF),
                                                              UNIT_TYPEID.TERRAN_SUPPLYDEPOT))
    def get_my_workers(self):
        filter(lambda unit: unit.unit_type.is_worker, self.get_all_units())

if __name__ == "__main__":
    MyAgent.bootstrap()
