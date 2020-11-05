from library import *
from jobs.economics import *


class Employer:
    """Assigns jobs to units."""
    def __init__(self):
        pass

    @classmethod
    def assign(cls, unit: Unit):
        if unit.unit_type.is_worker and Gatherer.hire(unit):
            return True
        elif unit.unit_type.is_building and Structure.hire(unit):
            return True
        else:
            print("Unit", unit, "can't find a job!")


class Job:
    """Template for all different jobs."""

    assigned = []

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
    def on_step(cls, unit: Unit):
        """Called every on_step()"""
        pass

    @classmethod
    def hire(cls, unit: Unit):
        if cls.is_proper and cls.is_qualified(unit):
            cls.assigned.append(unit)
            cls.on_assignment(unit)
            return True
        else:
            return False


def find_unit_job(unit, cls=Job):
    if unit in cls.assigned:
        return cls



