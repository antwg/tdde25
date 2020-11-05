import os

from typing import Optional
from library import *


class MyAgent(IDABot):
    def __init__(self):
        IDABot.__init__(self)

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        self.print_debug()

    def print_debug(self):
        """Funktion that displays tge units type, id and enumereringsindex"""

        unit_list = self.get_my_units()
        for i, unit in list(enumerate(unit_list)):
            text = str((unit.unit_type, "ID:", unit.id, "I:", i))
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


def main():
    coordinator = Coordinator(r"C:\Users\Daniel P\StarCraft II\Versions\Base81009\SC2_x64.exe")

    bot1 = MyAgent()
    # bot2 = MyAgent()

    participant_1 = create_participants(Race.Terran, bot1)
    # participant_2 = create_participants(Race.Terran, bot2)
    participant_2 = create_computer(Race.Random, Difficulty.Easy)

    coordinator.set_real_time(True)
    coordinator.set_participants([participant_1, participant_2])
    coordinator.launch_starcraft()

    path = os.path.join(os.getcwd(), "maps", "InterloperTest.SC2Map")
    coordinator.start_game(path)

    while coordinator.update():
        pass


if __name__ == "__main__":
    main()