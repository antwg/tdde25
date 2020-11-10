import time
from scai_backbone import *


def print_debug(self):
    # Skriver ut (< UnitType >  id: < id >  i: < enumereringsindex >)
    # för alla egna eneheter och resurser

    # print_debug_my_units(self)
    # print_debug_minerals_near_base(self)
    # print_debug_geysers_near_base(self)
    print_unit_info(self)
    print_unit_overview(self)


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
def print_unit_info(self):
    """prints out units assignment"""
    assignment_list = unit_assignment(self)
    for unit in assignment_list:
        self.map_tools.draw_text(unit.position, assignment_list[unit], Color(255, 255, 255))


    # DP
def print_unit_overview(self):
    """Prints out the assignment and number of workers in the top left corner"""
    assignment_list = unit_assignment(self)
    self.map_tools.draw_text_screen(0.01, 0.01, "Units Assignments:", Color(255, 255, 255))
    self.map_tools.draw_text_screen(0.01, 0.03, "------------------", Color(255, 255, 255))

    speace = 0.025
    assignments = {}

    for unit, assignment in assignment_list.items():
        if assignment_list[unit] in assignments:
            assignments[assignment] += 1
        else:
            assignments[assignment] = 1

    for assignment, amount in assignments.items():
        text = str(assignment) + ":"
        self.map_tools.draw_text_screen(0.01, 0.03 + speace, text, Color(255, 255, 255))
        self.map_tools.draw_text_screen(0.06, 0.03 + speace, str(amount), Color(255, 255, 255))

        speace *= 2

<<<<<<< Updated upstream

    # DP
def unit_assignment(self):
    """Creates a dictionary with a unit and its current assignment"""
    my_unit_list = self.get_my_units()
    assignment = {}
    for my_unit in my_unit_list:
        if my_unit.has_target:
            if my_unit.target.unit_type.is_mineral or my_unit.is_carrying_minerals:
                assignment[my_unit] = "mineral"
            elif my_unit.target.unit_type.is_refinery or my_unit.is_carrying_gas:
                assignment[my_unit] = "gas"
        elif my_unit.is_constructing(UnitType(UNIT_TYPEID.TERRAN_SUPPLYDEPOT, self)):
            assignment[my_unit] = "supply"
        elif my_unit.unit_type.is_geyser:
            assignment[my_unit] = "refinery"
    return assignment
=======
    pass


def get_coords(self):
    """Prints position of all workers"""
    for unit in self.get_my_workers():
        text = str(unit.position)
        self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))
>>>>>>> Stashed changes
