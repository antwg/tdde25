from job_system.constructor import *
from job_system.industry import *
from job_system.investment import *


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

        print([(job.get_demand(bot), str(job)) for job in get_jobs_and_plans_after_demand(bot)])

        if not Job.is_proper(bot, unit):
            cls.ban_unit(unit)
            print("Unit", unit, "couldn't find work and is banned!")
        elif not cls.is_banned(unit):
            """Basically the assignment process so far."""
            for job in get_jobs_after_demand(bot):
                if job.is_qualified(bot, unit) and job.get_demand(bot):
                    cls.add_to_job(bot, unit, job)
                    return True

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
    def add_to_job(cls, bot: IDABot, unit: Unit, job: Type[Job]) -> bool:
        have_job = find_unit_job(unit)
        if not have_job:
            jobs.append(job(bot, unit))
            return True
        return False

    @classmethod
    def add_to_plan(cls, bot: IDABot, job: Type[Job], plan: Plan) -> bool:
        if job.unit.unit_type in plan.able_investors:
            job.committed_plan = plan
            job.preferred_location_plan = plan.preferred_location
            job.reset_boredom()
            return True
        return False

    @classmethod
    def look_for_plan(cls, bot: IDABot, job: Type[Job]):
        for plan in get_plans_after_demand(bot):
            if cls.add_to_plan(bot, job, plan):
                return True
        return False

    @classmethod
    def is_banned(cls, unit: Unit) -> bool:
        """Check if unit is prohibited from getting a job"""
        if unit in cls.ban:
            return True
        else:
            return False

    @classmethod
    def ban_unit(cls, unit: Unit) -> bool:
        """Prohibit a unit from getting a job."""
        cls.ban.add(unit)
        return True

    @classmethod
    def load_system(cls, bot: IDABot):
        """Necessary load for Employer to work properly."""
        cls.ban = set()

        for job in get_all_jobs():
            job.load_class()

        create_all_plans(bot)

    @classmethod
    def snark_job(cls, bot: IDABot, job: Type[Job]):
        """Reached when a unit is bored, or rather wants to switch jobs."""
        if job.should_i_plan and cls.look_for_plan(bot, job):
            return True
        if cls.assign(bot, job.unit):
            return True
        elif cls.is_banned(job.unit):
            cls.fire(bot, job.unit)
            return False
        else:
            job.reset_boredom()
            return True


# ZW
def get_jobs_after_demand(bot: IDABot) -> List:
    return sorted(get_all_jobs(),
                  key=lambda job: job.get_demand(bot),
                  reverse=True)


# ZW
def get_plans_after_demand(bot: IDABot) -> List:
    return sorted(plans,
                  key=lambda plan: plan.get_demand(bot),
                  reverse=True)


# ZW
def create_all_plans(bot: IDABot):
    for job in get_all_jobs():
        for must_be in job.must_be:
            found = False
            for plan in plans:
                if must_be == plan.goal:
                    found = True
                    break

            if not found:
                plans.append(Plan(bot, must_be))


# ZW
def get_jobs_and_plans_after_demand(bot: IDABot) -> List:
    return sorted(list(filter(lambda interest: interest.get_demand(bot) != 0,
                              get_all_real_jobs() + get_affordable_plans(bot))),
                  key=lambda job: job.get_demand(bot),
                  reverse=True)
