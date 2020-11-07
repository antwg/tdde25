from library import *

from common_funcs import *


# ZW
class Job:
    """Template for all different job_system."""

    name: str = '-TEMPLATE-'

    @classmethod
    def is_proper(cls, bot: IDABot, unit: Unit):
        """Check if Unit is allowed in any job, True if so, else False"""
        if unit.player is not PLAYER_SELF:
            return False
        elif not unit.is_alive:
            return False
        else:
            return True

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        """Check if Unit is allowed on this job, True if so, else False."""
        if unit.player is not PLAYER_SELF:
            return False
        else:
            return True

    def __init__(self, bot: IDABot, unit: Unit):
        """Called when unit is assigned to job."""
        self.id = unit.id

    def on_step(self, bot: IDABot, unit: Unit):
        """Called every on_step()"""
        bot.map_tools.draw_text(unit.position,
                                self.name,
                                Color.WHITE)

    def on_discharge(self, bot: IDABot, unit: Unit):
        """Called when unit is removed from job."""
        pass

