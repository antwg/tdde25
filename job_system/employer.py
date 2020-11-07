from typing import Type

from job_system.economics import *
from job_system.structures import *


# ZW
class Employer:
    """Assigns job_system to units."""

    # Blacklist units from work
    ban: set = set()

    jobs: list

    @classmethod
    def assign(cls, bot: IDABot, unit: Unit) -> bool:
        """Assign a unit to a new job."""
        # Try to find current job anf if found remove unit from it
        before_job = find_unit_job(unit)
        if before_job:
            Employer.fire(bot, unit)

        if not cls.is_banned(unit) and Job.is_proper(bot, unit):
            """Basically the assignment process so far."""
            if Gatherer.is_qualified(bot, unit):
                cls.add(bot, unit, Gatherer)
                return True
            elif CommandCenter.is_qualified(bot, unit):
                cls.add(bot, unit, CommandCenter)
                return True
            elif Structure.is_qualified(bot, unit):
                cls.add(bot, unit, Structure)
                return True

        # Oof. Harsh life
        cls.ban_unit(unit)
        print("Unit", unit, "couldn't find work and is banned!")
        return False

    @classmethod
    def fire(cls, bot: IDABot, unit: Unit) -> bool:
        job = find_unit_job(unit)
        if job:
            job.on_discharge(bot, unit)
            cls.jobs.remove(job)
            return True
        return False

    @classmethod
    def add(cls, bot: IDABot, unit: Unit, job: Type[Job]) -> bool:
        have_job = find_unit_job(unit)
        if not have_job:
            cls.jobs.append(job(bot, unit))
            return True
        return False

    @classmethod
    def is_banned(cls, unit: Unit) -> bool:
        """Check if unit is prohibited from getting a job"""
        if unit.id in cls.ban:
            return True
        else:
            return False

    @classmethod
    def ban_unit(cls, unit: Unit) -> bool:
        """Prohibit a unit from getting a job."""
        cls.ban.add(unit.id)
        return True

    @classmethod
    def load_system(cls):
        """Necessary load for Employer to work properly."""
        cls.ban = set()
        cls.jobs = list()


# ZW
def find_unit_job(unit: Unit):
    for job in Employer.jobs:
        if job.id == unit.id:
            return job
    return None
