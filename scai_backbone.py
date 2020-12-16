import os
from math import sqrt

from library import *

import personal


# ___LISTS_OF_UNIT_TYPEIDS___

terran_buildings_TYPEIDS = [
    UNIT_TYPEID.TERRAN_COMMANDCENTER, UNIT_TYPEID.TERRAN_ORBITALCOMMAND,
    UNIT_TYPEID.TERRAN_PLANETARYFORTRESS, UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
    UNIT_TYPEID.TERRAN_REFINERY, UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.TERRAN_BARRACKS, UNIT_TYPEID.TERRAN_BUNKER,
    UNIT_TYPEID.TERRAN_ENGINEERINGBAY, UNIT_TYPEID.TERRAN_FACTORY,
    UNIT_TYPEID.TERRAN_MISSILETURRET, UNIT_TYPEID.TERRAN_SENSORTOWER,
    UNIT_TYPEID.TERRAN_GHOSTACADEMY, UNIT_TYPEID.TERRAN_ARMORY,
    UNIT_TYPEID.TERRAN_STARPORT, UNIT_TYPEID.TERRAN_FUSIONCORE,
    UNIT_TYPEID.TERRAN_TECHLAB, UNIT_TYPEID.TERRAN_REACTOR
]

repairable_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SIEGETANK, UNIT_TYPEID.TERRAN_SIEGETANKSIEGED,
    UNIT_TYPEID.TERRAN_HELLION, UNIT_TYPEID.TERRAN_HELLIONTANK,
    UNIT_TYPEID.TERRAN_BANSHEE, UNIT_TYPEID.TERRAN_BATTLECRUISER,
    UNIT_TYPEID.TERRAN_CYCLONE, UNIT_TYPEID.TERRAN_THOR,
    UNIT_TYPEID.TERRAN_THORAP, UNIT_TYPEID.TERRAN_VIKINGASSAULT,
    UNIT_TYPEID.TERRAN_VIKINGFIGHTER, UNIT_TYPEID.TERRAN_MEDIVAC,
    UNIT_TYPEID.TERRAN_LIBERATOR, UNIT_TYPEID.TERRAN_LIBERATORAG,
    UNIT_TYPEID.TERRAN_RAVEN, UNIT_TYPEID.TERRAN_WIDOWMINE
] + terran_buildings_TYPEIDS

repairer_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SCV,
    UNIT_TYPEID.TERRAN_MULE,
]

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

geysers_TYPEIDS = [
    UNIT_TYPEID.NEUTRAL_PROTOSSVESPENEGEYSER,
    UNIT_TYPEID.NEUTRAL_VESPENEGEYSER,
    UNIT_TYPEID.NEUTRAL_SPACEPLATFORMGEYSER,
    UNIT_TYPEID.NEUTRAL_SHAKURASVESPENEGEYSER,
    UNIT_TYPEID.NEUTRAL_RICHVESPENEGEYSER,
    UNIT_TYPEID.NEUTRAL_PURIFIERVESPENEGEYSER
]

refineries_TYPEIDS = [
    UNIT_TYPEID.TERRAN_REFINERY,
    UNIT_TYPEID.TERRAN_REFINERYRICH,
    UNIT_TYPEID.AUTOMATEDREFINERY,
    UNIT_TYPEID.INFESTEDREFINERY]

siege_tanks_TYPEIDS = [
    UNIT_TYPEID.TERRAN_SIEGETANK,
    UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]


# ___COORDINATES___

choke_point_dict = {(59, 28): (52, 35), (125, 137): (127, 128),
                    (58, 128): (67, 116), (125, 30): (114, 46),
                    (92, 139): (99, 130), (25, 111): (38, 110),
                    (26, 81): (30, 67), (86, 114): (93, 102),
                    (91, 71): (88, 82), (93, 39): (85, 50),
                    (126, 56): (114, 58), (65, 53): (69, 58),
                    (125, 86): (121, 100), (26, 30): (23, 39),
                    (26, 137): (37, 120), (60, 96): (58, 83)}

# List made for scouts to store base_chords
all_base_chords = []


# ___EXTENDED_METHODS___

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

# Subtract a Point2DI from a Point2DI
Point2DI.__sub__ = lambda self, other: Point2DI(self.x-other.x, self.y-other.y) \
    if isinstance(other, Point2DI) else Point2D(self.x-other.x, self.y-other.y)
# Add a Point2DI from a Point2DI
Point2DI.__add__ = lambda self, other: Point2DI(self.x+other.x, self.y+other.y) \
    if isinstance(other, Point2DI) else Point2D(self.x+other.x, self.y+other.y)
Point2D.__eq__ = lambda self, o: self.x == o.x and self.y == o.y \
    if isinstance(o, (Point2D, Point2DI)) else False
Point2DI.__eq__ = Point2D.__eq__


class ScaiBackbone(IDABot):
    """Handles bootstrap of program and important startup functions."""

    id: int  # The value of owner in it's units that corresponds to this player

    def __init__(self):
        IDABot.__init__(self)
        self.id = 0
        self.remember_these = []
        self.remember_mine = {}
        self.remember_enemies = []
        self.should_train_marines = []
        self.should_train_tanks = []
        self.should_develop_infantry = []
        self.should_develop_vehicle = []

    def on_game_start(self) -> None:
        IDABot.on_game_start(self)

    def on_step(self) -> None:
        IDABot.on_step(self)
        if not self.id:
            for unit in self.get_my_units():
                self.id = unit.owner
                # print("ID:", self.id)
                break

    def expansion(self) -> None:
        """Builds new command center when needed."""
        pass

    @classmethod
    def bootstrap(cls) -> None:
        """Starts and runs a Starcraft 2 math with defined settings."""

        coordinator = Coordinator(personal.game_dir)

        bot1 = cls()
        # bot2 = agent9()
        # bot2 = ScaiBackbone()

        participant_1 = create_participants(Race.Terran, bot1, "Dank_mejmejs - SCAI-07")
        # participant_2 = create_participants(Race.Terran, bot2)
        participant_2 = create_computer(Race.Terran, Difficulty.Easy)

        coordinator.set_real_time(False)
        coordinator.set_participants([participant_1, participant_2])
        coordinator.launch_starcraft()
        path = os.path.join(os.getcwd(), "maps", "InterloperTest-adjusted.SC2Map")

        coordinator.start_game(path)

        while coordinator.update():
            pass
