from job_system.economics import *
from job_system.structures import *


# ZW
class Employer:
    """Assigns job_system to units."""

    # Blacklist units from work
    ban: set = set()

    @classmethod
    def assign(cls, unit: Unit) -> bool:
        """Assign a unit to a new job."""
        # Try to find current job anf if found remove unit from it
        before_job = find_unit_job(unit)
        if before_job:
            before_job.fire(unit)

        """Basically the assignment process so far."""
        if Gatherer.hire(unit):
            return True
        elif CommandCenter.hire(unit):
            return True
        elif Structure.hire(unit):
            return True
        else:
            # Oof. Harsh life
            cls.ban_unit(unit)
            return False

    @classmethod
    def is_banned(cls, unit: Unit) -> bool:
        """Check if unit is prohibited from getting a job"""
        if unit.id in cls.ban:
            return True
        else:
            return False

    @classmethod
    def ban_unit(cls, unit: Unit):
        """Prohibit a unit from getting a job."""
        cls.ban.add(unit.id)
        print("Unit", unit, "couldn't find work and is banned!")

    @classmethod
    def load_system(cls):
        """Necessary load for Employer to work properly."""
        cls.ban = set()
        cls.load_work()

    @classmethod
    def load_work(cls, work=Job):
        """Necessary load for all jobs before using them."""
        work.load_work()

        for sub_work in work.__subclasses__():
            cls.load_work(sub_work)


# ZW
def find_unit_job(unit: Unit, cls=Job):
    """Finds a units job."""
    for sub_cls in cls.__subclasses__():
        result = find_unit_job(unit, sub_cls)
        if result:
            return result
    if unit.id in cls.assigned:
        return cls
    else:
        return None
