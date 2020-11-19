from job_system.job import *


plans: List = []  # Key are UNIT_TYPEID and value is a tuple as following
# (jobs: List, time_required: float, mineral_cost: int, gas_cost: int,
#  supply_cost: int)


class Plan:
    goal: UNIT_TYPEID
    goal_type: UnitType

    can_work: List[Job]
    able_investors: List[UnitType]

    preferred_location: Callable

    time_required = property(lambda self: self.goal_type.build_time)
    mineral_cost = property(lambda self: self.goal_type.mineral_price)
    gas_cost = property(lambda self: self.goal_type.gas_price)
    supply_cost = property(lambda self: self.goal_type.supply_required)

    def __init__(self, bot: IDABot, utid: UNIT_TYPEID):
        self.goal = utid
        self.goal_type = UnitType(utid, bot)

        self.can_work = []
        for job in get_all_jobs():
            if utid in job.must_be:
                self.can_work.append(job)
        self.able_investors = bot.tech_tree.get_data(self.goal_type).what_builds

        # TODO: FINISH this!
        if self.utid in on_target_builds_TYPEID:
            self.preferred_location = self.get_closest_target
        elif self.utid.is_building:
            self.preferred_location = self.get_closest_target

    def get_can_work_depth(self, depth, found) -> Dict:
        if depth == 0:
            return found
        else:
            for job in self.can_work:
                if job in found:
                    found[job] = max(found[job], depth)
                else:
                    found[job] = depth

            for plan in self.can_plan():
                found = plan.get_can_work_depth(depth-1, found)

            return found

    def get_demand(self, bot: IDABot):

        demand = 0
        seabed = 3
        jobs_n_depth = self.get_can_work_depth(seabed, {})
        for job, depth in jobs_n_depth.items():
            demand += (0.5 ** (seabed - depth)) * job.get_demand(bot)

        demand /= 1 + len(list(filter(
            lambda job: job.committed_plan == self, jobs)))

        return demand

    def can_plan(self):
        found = []
        for plan in plans:
            if self.goal_type in plan.able_investors:
                found.append(plan)
        return found

    def __str__(self):
        return 'PLAN{' + str(self.goal) + '}'


def invest(job: Job, bot: IDABot):
    if job.unit.is_idle:
        if job.committed_plan:
            if bot.produce_unit(bot, job.unit, job.committed_plan.goal_type,
                                job.preferred_location_plan):
                job.committed_plan = None


Job.invest = invest


def get_affordable_plans(bot: IDABot):
    found = []
    for plan in plans:
        if bot.can_afford(plan.goal_type):
            found.append(plan)
    return found
