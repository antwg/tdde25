import time

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

        # DP
    def print_debug(self):
        """Funktion that displays the units type, id and enumereringsindex"""

        unit_list = self.get_all_units()
        for i, unit in list(enumerate(unit_list)):
            text = str((unit.unit_type, "ID:", unit.id, "I:", i))
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


if __name__ == "__main__":
    MyAgent.bootstrap()
