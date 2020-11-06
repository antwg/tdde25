import time
from scai_backbone import *


def print_debug(self):

    # Skriver ut (< UnitType >  id: < id >  i: < enumereringsindex >)
    # för alla egna eneheter och resurser

    print_debug_my_units(self)
    print_debug_minerals_near_base(self)
    print_debug_geysers_near_base(self)


    # DP
def print_debug_my_units(self):
    """Prints < UnitType >  id: < id >  i: < enumereringsindex > for the players units """
    my_unit_list = self.get_my_units()

    for i, my_unit in list(enumerate(my_unit_list)):
        print_debug_all(self, my_unit, i)


    # DP
def print_debug_minerals_near_base(self):
    """Prints < UnitType >  id: < id >  i: < enumereringsindex > for starting base minerals"""
    start_location = self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)
    mineral_unit_list = start_location.minerals

    for i, mineral_unit in list(enumerate(mineral_unit_list)):
        print_debug_all(self, mineral_unit, i)


    # DP
def print_debug_geysers_near_base(self):
    """Prints < UnitType >  id: < id >  i: < enumereringsindex > for starting base geysers"""
    start_location = self.base_location_manager.get_player_starting_base_location(PLAYER_SELF)
    geysers_unit_list = start_location.geysers

    for i, geysers_unit in list(enumerate(geysers_unit_list)):
        print_debug_all(self, geysers_unit, i)


    # DP
def print_debug_all(self, unit, i):
    text = str((unit.unit_type, "ID:", unit.id, "I:", i))
    self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


def print_unit_info():

    # Skriver ut enehters uppgift på deras position

    pass


def print_unit_overview():

    # Skriver ut alla uppgifter/jobb i en lista men antalet arbetare

    pass
