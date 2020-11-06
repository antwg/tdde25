from job_system.job import *


# ZW
class Structure(Job):
    """Do nothing but look pretty."""

    name: str = 'Structure'

    @classmethod
    def on_step(cls, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""

        super().on_step(bot, unit)

    @classmethod
    def is_qualified(cls, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        else:
            return super().is_qualified(unit)


# ZW
class CommandCenter(Structure):
    """Do nothing but look pretty."""

    name: str = 'CommandCenter'

    @classmethod
    def on_step(cls, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""

        super().on_step(bot, unit)

    @classmethod
    def is_qualified(cls, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        elif not unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            return False
        else:
            return super().is_qualified(unit)