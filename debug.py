import time
from scai_backbone import *


def print_debug(self, job_dict):
    # Skriver ut (< UnitType >  id: < id >  i: < enumereringsindex >)
    # för alla egna eneheter och resurser

    # print_debug_my_units(self)
    # print_debug_minerals_near_base(self)
    # print_debug_geysers_near_base(self)
    print_unit_info(self, job_dict)
    print_unit_overview(self, job_dict)


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
    """prints out the giver information < UnitType >  id: < id >  i: < enumereringsindex >"""
    text = str((unit.unit_type, "ID:", unit.id, "I:", i))
    self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


    # DP
def print_unit_info(self, job_dict):
    """prints out units assignment"""
    assignment_list = unit_assignment(self, job_dict)
    for unit in assignment_list:
        self.map_tools.draw_text(unit.position, assignment_list[unit], Color(255, 255, 255))


    # DP
def print_unit_overview(self, job_dict):
    """Prints out the assignment and number of workers in the top left corner"""
    assignment_amount_list = assignment_amount(self, job_dict)
    self.map_tools.draw_text_screen(0.01, 0.01, "Units Assignments:", Color(255, 255, 255))
    self.map_tools.draw_text_screen(0.01, 0.03, "------------------", Color(255, 255, 255))

    space = 0.025

    for assignment, amount in assignment_amount_list.items():
        text = str(assignment) + ":"
        self.map_tools.draw_text_screen(0.01, 0.03 + space, text, Color(255, 255, 255))
        self.map_tools.draw_text_screen(0.06, 0.03 + space, str(amount), Color(255, 255, 255))

        space *= 2


    # DP
def unit_assignment(self, job_dict):
    """Creates dictionary of unit and assignment"""
    assignment = {}
    #kollar vad för typ av target unit har å skapar en dict baserat på det
    for unit in job_dict:
        if unit.unit_type.is_worker:
            if job_dict[unit].unit_type.is_mineral:
                assignment[unit] = "mineral"
            elif job_dict[unit].unit_type.is_refinery:
                assignment[unit] = "gas"

    return assignment


def assignment_amount(self, job_dict):
    """Makes a dictionary of assignment and amount of personnel"""
    unit_assignment_list = unit_assignment(self, job_dict)
    assignment_amount_list = {}

    for unit, assignment in unit_assignment_list.items():
        if unit_assignment_list[unit] in assignment_amount_list:
            assignment_amount_list[assignment] += 1
        else:
            assignment_amount_list[assignment] = 1

    return assignment_amount_list


def get_coords(self):
    """Prints position of all workers"""
    for unit in self.get_my_workers():
        text = str(unit.position)
        self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))
