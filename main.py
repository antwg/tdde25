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

        unit_list = self.get_my_units()
        index_unit_list = list(enumerate(unit_list))

        # writes/displays all the moving units type, id and index
        for unit_tuple in index_unit_list:
            print_debug(unit_tuple, self)


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


def print_debug(unit_tuple, bot):
    """Funktion that displays tge units type, id and enumereringsindex"""
    text1 = str(unit_tuple[1].unit_type)
    text2 = str(unit_tuple[1].id)
    text3 = str(unit_tuple[0])
    text = text1 + " ID: " + text2 + " I: " + text3
    bot.map_tools.draw_text(unit_tuple[1].position, text, Color(255, 255, 255))


if __name__ == "__main__":
    main()