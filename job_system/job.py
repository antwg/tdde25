from library import *


# ZW
class Job:
    """Template for all different job_system."""

    name: str = '-TEMPLATE-'
    assigned: set

    @classmethod
    def load_work(cls):
        """Handles necessary action before class can be used."""
        # If not assigned here, the assigned property will exist in parent Job
        # and be shared between all jobs
        cls.assigned = set()

    @classmethod
    def is_proper(cls, unit: Unit):
        """Check if Unit is allowed in any job, True if so, else False"""
        if unit.player is not PLAYER_SELF:
            return False
        elif not unit.is_alive:
            return False
        else:
            return True

    @classmethod
    def is_qualified(cls, unit: Unit):
        """Check if Unit is allowed on this job, True if so, else False."""
        if unit.player is not PLAYER_SELF:
            return False
        else:
            return True

    @classmethod
    def on_assignment(cls, unit: Unit):
        """Called when unit is assigned to job."""
        pass

    @classmethod
    def on_step(cls, bot: IDABot, unit: Unit):
        """Called every on_step()"""
        bot.map_tools.draw_text(unit.position,
                                cls.name,
                                Color.WHITE)

    @classmethod
    def hire(cls, unit: Unit) -> bool:
        """Assign a unit to this job."""
        if cls.is_proper(unit) and cls.is_qualified(unit):
            print(cls, __class__)
            cls.assigned.add(unit.id)
            cls.on_assignment(unit)
            return True
        else:
            return False

    @classmethod
    def fire(cls, unit: Unit) -> bool:
        """Fire a unit from this job."""
        if unit.id in cls.assigned:
            cls.assigned.remove(unit.id)
            return True
        else:
            return False
