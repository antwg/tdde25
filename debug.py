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
    unit_list = self.get_all_units()
    my_unit_list = self.get_my_units()

    for i, my_unit in list(enumerate(my_unit_list)):
        if my_unit in unit_list:
            text = str((my_unit.unit_type, "ID:", my_unit.id, "I:", i))
            self.map_tools.draw_text(my_unit.position, text, Color(255, 255, 255))


    # DP
def print_debug_minerals_near_base(self):
    unit_list = self.get_all_units()
    player_constant = PLAYER_SELF
    start_location = self.base_location_manager.get_player_starting_base_location(player_constant)
    mineral_unit_list = start_location.minerals

    for i, material_unit in list(enumerate(mineral_unit_list)):
        if material_unit in unit_list:
            text = str((material_unit.unit_type, "ID:", material_unit.id, "I:", i))
            self.map_tools.draw_text(material_unit.position, text, Color(255, 255, 255))


    # DP
def print_debug_geysers_near_base(self):
    unit_list = self.get_all_units()
    player_constant = PLAYER_SELF
    start_location = self.base_location_manager.get_player_starting_base_location(player_constant)
    geysers_unit_list = start_location.geysers

    for i, geysers_unit in list(enumerate(geysers_unit_list)):
        if geysers_unit in unit_list:
            text = str((geysers_unit.unit_type, "ID:", geysers_unit.id, "I:", i))
            self.map_tools.draw_text(geysers_unit.position, text, Color(255, 255, 255))

    pass


def print_unit_info():

    # Skriver ut enehters uppgift på deras position

    pass


def print_unit_overview():

    # Skriver ut alla uppgifter/jobb i en lista men antalet arbetare

    pass
