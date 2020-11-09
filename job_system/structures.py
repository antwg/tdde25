from job_system.constructor import *


# ZW
class Structure(Job):
    """Do nothing but look pretty."""

    name: str = 'Structure -TEMPLATE-'

    def on_step(self, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""

        super().on_step(bot, unit)

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        else:
            return super().is_qualified(bot, unit)


# ZW
class GatheringCenter(Structure):
    """Do nothing but look pretty."""

    name: str = 'GatheringCenter'
    demand: int = 100
    base_location_p: Point2D

    def __init__(self, bot: IDABot, unit: Unit):
        base_location = find_base_location_on_point(bot, unit.position)
        if base_location:
            self.base_location_p = base_location.position
            super().__init__(bot, unit)
        else:
            raise Exception("Gathering center is not within a base location!")

    def on_step(self, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""
        super().on_step(bot, unit)

    def get_base_location(self, bot: IDABot):
        for base_location in bot.base_location_manager.base_locations:
            if base_location.position == self.base_location_p:
                return base_location
        else:
            return None

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        elif not unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            return False
        elif not find_base_location_on_point(bot, unit.position):
            return False
        else:
            return super().is_qualified(bot, unit)
