from typing import Type, Dict

from library import *

from common_funcs import *

jobs: list = []


# ZW
class Job:
    """Template for all different job_system."""

    id: int  # Id of unit that has this job

    name: str = '-TEMPLATE-'  # The displayed name for the job, mostly for debug
    demand: int = 0  # How much more important then other jobs this job is

    clients: Dict  # Key is jobs that requires this job and value is how many

    must_be: List = []  # UNIT_TYPEIDS that can have this job (for planning)

    invested_plans: List = []  # References to items in the plans list
    should_i_plan: bool = True  # If the unit should try to invest in market

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
        self.id = unit.id
        self.slaves = []
        self.master = None

    def on_step(self, bot: IDABot, unit: Unit):
        """Called every on_step()"""
        bot.map_tools.draw_text(unit.position,
                                self.name,
                                Color.WHITE)

    def on_discharge(self, bot: IDABot, unit: Unit):
        """Called when unit is removed from job."""
        pass

    def get_unit(self, bot: IDABot) -> Union[Unit, None]:
        """Fetches the unit that has this job since it only knows its id."""
        for unit in bot.get_my_units():
            if unit.id == self.id:
                return unit
        return None

    def most_demanding_client(self, bot: IDABot):
        """Return the client which is closest and request most."""
        found = None
        weight = 0
        this_position = self.get_unit(bot).position
        for client, demand in self.clients.items():
            client_position = client.get_unit(bot).position
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
        if job.id == unit.id:
            return job
    return None


# ZW
def find_units_id_with_job(searched: Type[Job]) -> List[int]:
    result = []
    for job in jobs:
        if isinstance(job, searched):
            result.append(job.id)
    return result


# ZW
def find_units_with_job(bot: IDABot, searched: Type[Job]) -> List[Unit]:
    ids = find_units_id_with_job(searched)
    result = []
    for unit in bot.get_my_units():
        if unit.id in ids:
            result.append(unit)
    return result


# ZW
def any_units_with_job(searched: Type[Job]) -> bool:
    for job in jobs:
        if isinstance(job, searched):
            return True
    else:
        return False


