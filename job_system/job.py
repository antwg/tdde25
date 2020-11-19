from typing import Type, Dict

from library import *

from common_funcs import *

jobs: list = []


# ZW
class Job:
    """Template for all different jobs in job_system."""

    unit: Unit  # The unit that has this job

    name: str = '-TEMPLATE-'  # The displayed name for the job, mostly for debug
    demand: int = 0  # How much more important then other jobs this job is
    boredom: int  # A parameter to see to that the unit tries switching jobs

    clients: Dict  # Key is jobs that requires this job and value is how many

    must_be: List = []  # UNIT_TYPEIDS that can have this job (for planning)

    should_i_plan: bool = True  # If the unit should try to invest in market
    committed_plan: Union[Type, None]  # Plan that the unit is trying to achieve
    preferred_location_plan: Callable  # Calculates where plan is best placed

    @classmethod
    def is_proper(cls, bot: IDABot, unit: Unit) -> bool:
        """Check if Unit is allowed in any job, True if so, else False."""
        if unit.player is not PLAYER_SELF:
            return False
        elif not unit.is_alive:
            return False
        else:
            return True

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit) -> bool:
        """Check if Unit is allowed on this job, True if so, else False."""
        if cls.must_be and unit.unit_type.unit_typeid not in cls.must_be:
            return False
        else:
            return True

    @classmethod
    def is_template(cls):
        return True if '-TEMPLATE-' in cls.name else False

    @classmethod
    def load_class(cls):
        cls.plans = {}

    def __init__(self, bot: IDABot, unit: Unit):
        """Called when unit is assigned to job."""
        self.unit = unit
        self.slaves = []
        self.master = None
        self.boredom = 10
        self.committed_plan = None
        self.preferred_location_plan = None

    def on_step(self, bot: IDABot):
        """Called every on_step()."""
        if self.is_job_boring(bot):
            self.increase_boredom()

        bot.map_tools.draw_text(self.unit.position,
                                self.name,
                                Color.WHITE)

    def on_discharge(self, bot: IDABot):
        """Called when unit is removed from job."""
        pass

    def is_job_boring(self, bot: IDABot) -> bool:
        """Checks if the job should increase it's boredom."""
        if self.unit.is_idle:
            return True
        return False

    def increase_boredom(self):
        """Move unit towards boredom state."""
        if self.boredom > 0:
            self.boredom -= 1

    def is_bored(self):
        """Check if job has reached boredom."""
        return self.boredom == 0

    def reset_boredom(self):
        """Refills boredom so that the job keeps working for a while."""
        self.boredom = 100

    def set_bored(self):
        self.boredom = 0

    def most_demanding_client(self, bot: IDABot):
        """Return the client which is closest and request most."""
        found = None
        weight = 0
        this_position = self.unit.position
        for client, demand in self.clients.items():
            client_position = client.unit.position
            ground_distance = bot.map_tools.get_ground_distance(client_position,
                                                                this_position)
            if not found or weight < demand / ground_distance:
                found = client
                weight = demand / ground_distance
        return found

    @classmethod
    def get_demand(cls, bot: IDABot):
        return cls.demand

    @classmethod
    def set_demand(cls, val: int):
        cls.demand = val


# ZW
def get_all_jobs(from_job=Job) -> List:
    found_jobs = []
    if not from_job.is_template():
        found_jobs.append(from_job)

    sub_jobs = from_job.__subclasses__()
    if sub_jobs:
        for sub_job in sub_jobs:
            found_jobs += get_all_jobs(sub_job)

    return found_jobs


# ZW
def get_all_real_jobs(from_job=Job) -> List:
    found_jobs = []
    if not from_job.is_template() and from_job.name != "Investor":
        found_jobs.append(from_job)

    sub_jobs = from_job.__subclasses__()
    if sub_jobs:
        for sub_job in sub_jobs:
            found_jobs += get_all_jobs(sub_job)

    return found_jobs


# ZW
def get_jobs_of(searched: Type[Job]) -> List[Job]:
    result = []
    for job in jobs:
        if isinstance(job, searched):
            result.append(job)
    return result


# ZW
def get_planning_jobs_with_must_be(utid: UnitTypeID) -> List[Job]:
    found = []
    for job in get_all_jobs():
        if utid in job.must_be and job.should_i_plan:
            found.append(job)
    return found


# ZW
def find_unit_job(unit: Unit):
    for job in jobs:
        if job.unit == unit:
            return job
    return None


# ZW
def find_units_with_job(bot: IDABot, searched: Type[Job]) -> List[Unit]:
    result = []
    for job in bot.get_my_jobs():
        if isinstance(job, searched):
            result.append(job.unit)
    return result


# ZW
def any_units_with_job(searched: Type[Job]) -> bool:
    for job in jobs:
        if isinstance(job, searched):
            return True
    else:
        return False
