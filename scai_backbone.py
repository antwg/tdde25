import os
import inspect

from typing import Optional
from library import *


# ZW
import personal


class ScaiBackbone(IDABot):
    def __init__(self):
        IDABot.__init__(self)

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)

    @classmethod
    def bootstrap(cls):
        coordinator = Coordinator(personal.game_dir)

        bot1 = cls()
        # bot2 = cls()

        participant_1 = create_participants(Race.Terran, bot1, "Gerald - SCAI-07")
        # participant_2 = create_participants(Race.Terran, bot2)
        participant_2 = create_computer(Race.Random, Difficulty.Easy)

        coordinator.set_real_time(True)
        coordinator.set_participants([participant_1, participant_2])
        coordinator.launch_starcraft()
        path = os.path.join(os.getcwd(), "maps", "InterloperTest-adjusted.SC2Map")

        coordinator.start_game(path)

        while coordinator.update():
            pass

