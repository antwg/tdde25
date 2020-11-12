from job_system.structures import *

from job_system.economics import *


# ZW
class GatheringCenter(Structure):
    """Central for gathering stuff at base locations."""

    name: str = 'GatheringCenter'
    demand: int = 100

    base_location_p: Point2D

    must_be = grounded_command_center_TYPEID

    def __init__(self, bot: IDABot, unit: Unit):
        base_location = find_base_location_on_point(bot, unit.position)
        if base_location:
            self.base_location_p = base_location.position

            Gatherer.clients[self] = len(base_location.mineral_fields)

            Refinery.clients[self] = len(base_location.geysers)

            super().__init__(bot, unit)
        else:
            raise Exception("Gathering center is not within a base location!")

    def on_step(self, bot: IDABot, unit: Unit):
        super().on_step(bot, unit)

    def on_discharge(self, bot: IDABot, unit: Unit):
        del Gatherer.clients[self]
        del Refinery.clients[self]

    def get_base_location(self, bot: IDABot):
        for base_location in bot.base_location_manager.base_locations:
            if base_location.position == self.base_location_p:
                return base_location
        else:
            return None

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            return False
        elif not find_base_location_on_point(bot, unit.position):
            return False
        else:
            return super().is_qualified(bot, unit)
