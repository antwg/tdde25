import os
import inspect

from typing import Optional
from library import *


class ScaiBootstrap(IDABot):
    def __init__(self):
        IDABot.__init__(self)

    def on_game_start(self):
        IDABot.on_game_start(self)
        self.awake()

    def awake(self):
        """Event when game starts. Meant to be inherited."""
        pass

    def on_step(self):
        IDABot.on_step(self)
        self.update()

    def update(self):
        """Event on regular update. Meant to be inherited."""
        pass

    @classmethod
    def main(cls):
        coordinator = Coordinator(r"C:\Program Files (x86)\StarCraft II\Versions\Base81433\SC2_x64.exe")

        bot1 = cls()
        # bot2 = cls()

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

