from typing import Type, List

from job_system.economics import *
from job_system.industry import *

plans: Dict = {}  # Key are UNIT_TYPEID and value is a tuple as following
# (jobs: List, time_required: float, mineral_cost: int, gas_cost: int,
#  supply_cost: int)


# ZW
class Investor(Job):

    name = 'Investor'

    producing: UnitTypeID
    produce_on: Union[Point2D, Unit]
    produce_to: Union[Point2D, Unit]

    def on_step(self, bot: IDABot, unit: Unit):
        pass


# ZW
class Employer:
    """Assigns job_system to units."""

    # Blacklist units from work
    ban: set = set()

    @classmethod
    def assign(cls, bot: IDABot, unit: Unit) -> bool:
        """Assign a unit to a new job."""
        # Try to find current job anf if found remove unit from it
        before_job = find_unit_job(unit)
        if before_job:
            Employer.fire(bot, unit)

        print([(job.get_demand(bot), job) for job in get_jobs_after_demand(bot)])

        if not Job.is_proper(bot, unit):
            cls.ban_unit(unit)
            print("Unit", unit, "couldn't find work and is banned!")
        elif not cls.is_banned(unit):
            """Basically the assignment process so far."""
            for job in get_jobs_after_demand(bot):
                if job.is_qualified(bot, unit) and job.get_demand(bot):
                    cls.add(bot, unit, job)
                    return True

        # Oof. Harsh life
        return False

    @classmethod
    def fire(cls, bot: IDABot, unit: Unit) -> bool:
        job = find_unit_job(unit)
        if job:
            job.on_discharge(bot, unit)
            jobs.remove(job)
            return True
        return False

    @classmethod
    def add(cls, bot: IDABot, unit: Unit, job: Type[Job]) -> bool:
        have_job = find_unit_job(unit)
        if not have_job:
            jobs.append(job(bot, unit))
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
    def load_system(cls, bot: IDABot):
        """Necessary load for Employer to work properly."""
        cls.ban = set()

        for job in get_all_jobs():
            job.load_class()

        create_all_plans(bot)

        for plan_unit in plans:
            data = bot.tech_tree.get_data(UnitType(plan_unit, bot))


# ZW
def get_jobs_after_demand(bot: IDABot) -> List:
    return sorted(get_all_jobs(),
                  key=lambda job: job.get_demand(bot),
                  reverse=True)


# ZW
def create_all_plans(bot: IDABot):
    for job in get_all_jobs():
        for must_be in job.must_be:
            if must_be not in plans:
                create_new_plan(bot, must_be)
            if job not in plans[must_be][0]:
                plan_jobs = list(plans[must_be])
                plan_jobs[0] += (job,)
                plans[must_be] = tuple(plan_jobs)


# ZW
def create_new_plan(bot: IDABot, utid: UnitTypeID):
    unit_type = UnitType(utid, bot)
    plans[utid] = (tuple(),
                   unit_type.build_time,
                   unit_type.mineral_price,
                   unit_type.gas_price,
                   unit_type.supply_required)


"""
def start_to_plan(cls, bot: IDABot):
    for must_be in cls.must_be:
        data = bot.tech_tree.get_data(UnitType(must_be, bot))

        jobs_to_update = set()

        for builder in data.what_builds:
            jobs_to_update.update(
                set(get_planning_jobs_with_must_be(builder.unit_typeid)))

        for job in jobs_to_update:
            if must_be not in job.plans:
                job.create_new_plan(bot, must_be)
            if cls not in job.plans[must_be][0]:
                plan_jobs = list(job.plans[must_be])
                plan_jobs[0] += (cls,)
                job.plans[must_be] = plan_jobs
"""
