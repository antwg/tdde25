import os
import inspect
from math import sqrt

from typing import Optional
from library import *

# ZW
import personal

grounded_command_centers_TYPEIDS = [
    UNIT_TYPEID.TERRAN_COMMANDCENTER,
    UNIT_TYPEID.TERRAN_ORBITALCOMMAND,
    UNIT_TYPEID.TERRAN_PLANETARYFORTRESS]

minerals_TYPEIDS = [
    UNIT_TYPEID.NEUTRAL_MINERALFIELD,
    UNIT_TYPEID.NEUTRAL_MINERALFIELD450,
    UNIT_TYPEID.NEUTRAL_MINERALFIELD750,
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD,
    UNIT_TYPEID.NEUTRAL_BATTLESTATIONMINERALFIELD750,
    UNIT_TYPEID.NEUTRAL_LABMINERALFIELD750,
    UNIT_TYPEID.NEUTRAL_RICHMINERALFIELD750,
    UNIT_TYPEID.NEUTRAL_PURIFIERMINERALFIELD750,
    UNIT_TYPEID.NEUTRAL_PURIFIERRICHMINERALFIELD750]

refineries_TYPEIDS = [
    UNIT_TYPEID.TERRAN_REFINERY,
    UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.AUTOMATEDREFINERY,
    UNIT_TYPEID.INFESTEDREFINERY]

# Get the distance to a point from a point
Point2D.dist = lambda self, other: sqrt((self.x - other.x)**2
                                        + (self.y - other.y)**2)

job_dict = {}
job_dict2 = {}


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

        coordinator.set_real_time(False)
        coordinator.set_participants([participant_1, participant_2])
        coordinator.launch_starcraft()
        path = os.path.join(os.getcwd(), "maps", "InterloperTest-adjusted.SC2Map")

        coordinator.start_game(path)

        while coordinator.update():
            pass
