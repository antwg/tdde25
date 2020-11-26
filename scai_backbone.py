import os
import inspect
from math import sqrt

from typing import Optional
from library import *

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

siege_tanks_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SIEGETANK,
    UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]


# Get the distance to a point from a point
Point2D.dist = lambda self, other: sqrt((self.x - other.x)**2
                                        + (self.y - other.y)**2)
# Get the distance to a point from a point
Point2D.squared_dist = lambda self, other: (self.x - other.x)**2 \
                                           + (self.y - other.y)**2
# Translate a Point2D to a Point2DI
Point2D.to_i = lambda self: Point2DI(round(self.x), round(self.y))
# Translate a Point2DI to a Point2D
Point2DI.to_f = lambda self: Point2D(self.x, self.y)


class ScaiBackbone(IDABot):

    id: int  # The value of owner in it's units that corresponds to this player

    def __init__(self):
        IDABot.__init__(self)
        self.id = None

    def on_game_start(self):
        IDABot.on_game_start(self)

    def on_step(self):
        IDABot.on_step(self)
        if not self.id:
            for unit in self.get_my_units():
                self.id = unit.owner
                print("ID:", self.id)
                break

    @classmethod
    def bootstrap(cls):
        coordinator = Coordinator(personal.game_dir)

        bot1 = cls()
        # bot2 = cls()

        participant_1 = create_participants(Race.Terran, bot1, "Dank_mejmejs - SCAI-07")
        # participant_2 = create_participants(Race.Terran, bot2)
        participant_2 = create_computer(Race.Random, Difficulty.Easy)

        coordinator.set_real_time(False)
        coordinator.set_participants([participant_1, participant_2])
        coordinator.launch_starcraft()
        path = os.path.join(os.getcwd(), "maps", "InterloperTest-adjusted.SC2Map")

        coordinator.start_game(path)

        while coordinator.update():
            pass
