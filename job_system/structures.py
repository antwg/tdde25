from job_system.job import *


# ZW
class Structure(Job):
    """Do nothing but look pretty."""

    name: str = 'Structure'

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
class CommandCenter(Structure):
    """Do nothing but look pretty."""

    name: str = 'CommandCenter'

    def on_step(self, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""

        super().on_step(bot, unit)

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        elif not unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            return False
        else:
            return super().is_qualified(bot, unit)
