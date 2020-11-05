import time
import random

from scai_backbone import *

from debug import *

# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_game_start(self)

    def on_step(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_step(self)
        print_debug(self)
        self.build_supply_depot()

    def build_supply_depot(self):
        """Builds supply depot when necessary"""
        if (self.current_supply / self.max_supply) <= 0.8 and \
                self.max_supply < 200 and self.minerals >= 100:
            print('bygg då')
            Unit.build((random.choice(self.get_my_units())),
                       UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
                       BuildingPlacer.get_build_location_near)


if __name__ == "__main__":
    MyAgent.bootstrap()
