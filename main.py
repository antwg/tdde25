import time
import random

from scai_backbone import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_game_start(self)

    def on_step(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_step(self)
        self.print_debug()
        self.build_supply_depot()

        # DP
    def print_debug(self):
        """Funktion that displays the units type, id and enumereringsindex"""

        unit_list = self.get_all_units()
        for i, unit in list(enumerate(unit_list)):
            text = str((unit.unit_type, "ID:", unit.id, "I:", i))
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


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
