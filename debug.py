import time
from scai_backbone import *
from workplace import *

def print_debug(self):
    # Skriver ut (< UnitType >  id: < id >  i: < enumereringsindex >)
    # för alla egna eneheter och resurser

    # print_debug_my_units(self)
    # print_debug_minerals_near_base(self)
    # print_debug_geysers_near_base(self)
    print_unit_info(self)
    print_unit_overview(self)

    # tihi
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
    assignment_amount_list = assignment_amount(self)
    self.map_tools.draw_text_screen(0.01, 0.01, "Units Assignments:", Color(255, 255, 255))
    self.map_tools.draw_text_screen(0.01, 0.03, "------------------", Color(255, 255, 255))

    space = 0.025

    for assignment, amount in assignment_amount_list.items():
        text = str(assignment) + ":"
        self.map_tools.draw_text_screen(0.01, 0.03 + space, text, Color(255, 255, 255))
        self.map_tools.draw_text_screen(0.1, 0.03 + space, str(amount), Color(255, 255, 255))

        space *= 2


    # DP
def unit_assignment(self):
    """Creates dictionary of unit and assignment, for the class Workplace"""
    assignment = {}

    for workplace in workplaces:
        for miner in workplace.miners:
            assignment[miner] = "miner"
        for gaser in workplace.gasers:
            assignment[gaser] = "gas_gatherer"
        for builder in workplace.builders:
            assignment[builder] = "builder"

        return assignment


def assignment_amount(self):
    """Makes a dictionary of assignment and amount of personnel"""
    unit_assignment_list = unit_assignment(self)
    assignment_amount_list = {}

    for unit, assignment in unit_assignment_list.items():
        if unit_assignment_list[unit] in assignment_amount_list:
            assignment_amount_list[assignment] += 1
        else:
            assignment_amount_list[assignment] = 1

    return assignment_amount_list


def get_coords(self):
    """Prints position of all workers"""
    for unit in self.get_my_units():
        text = str(unit.position)
        self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


# ZW
def remove_this_debug(bot: IDABot):
    building = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, bot)
    size_x = building.tile_width
    size_y = building.tile_height
    margin = 0

    for y in range(int(bot.map_tools.height / 3)):
        for x in range(int(bot.map_tools.width / 3)):
            col = Color.WHITE if bot.building_placer.can_build_here_with_spaces(
                x,
                y,
                building,
                margin) else Color.RED

            bot.map_tools.draw_circle(Point2D(x, y), 0.5, col)

    if not bot.unit:
        for unit in bot.get_my_units():
            bot.unit = unit
            break

    bot.map_tools.draw_text(bot.unit.position, str(
        bot.building_placer.can_build_here_with_spaces(
            int(bot.unit.position.x),
            int(bot.unit.position.y),
            building,
            margin)))

    firstPoint = (bot.unit.position - Point2D(margin + size_x / 2, margin + size_y / 2)).to_i()
    secondPoint = (bot.unit.position + Point2D(margin + size_x / 2, margin + size_y / 2)).to_i()
    bot.map_tools.draw_box(firstPoint.to_f(), secondPoint.to_f())
    bot.map_tools.draw_circle(bot.unit.position.to_i().to_f(), margin + sqrt(size_x ** 2 + size_y ** 2) / 2)

