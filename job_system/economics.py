from job_system.structures import *

from job_system.market import *


# ZW
class Worker(Job):
    """Job template for Workers."""

    name: str = 'Worker -TEMPLATE-'
    demand = 0

    must_be = [UNIT_TYPEID.TERRAN_SCV]

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        return super().is_qualified(bot, unit)


# ZW
class Gatherer(Worker):
    """Worker who gathers resources."""

    name: str = 'Gatherer'
    gathering_center: Type[Job]

    clients: Dict = {}  # Gathering Centers ONLY!

    def __init__(self, bot: IDABot, unit: Unit):
        super().__init__(bot, unit)

        self.gathering_center = self.most_demanding_client(bot)
        self.unit.right_click(
            find_closest_mineralfield(bot, self.gathering_center.unit.position))

    def on_step(self, bot: IDABot):
        if self.unit.is_idle:
            self.unit.right_click(
                find_closest_mineralfield(bot,
                                          self.gathering_center.unit.position))
        super().on_step(bot)

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not cls.clients:
            return False
        else:
            return super().is_qualified(bot, unit)

    @classmethod
    def get_demand(cls, bot):
        result = 0
        for demand in cls.clients.values():
            result += demand
        return result * 2 + cls.demand - len(get_jobs_of(cls))


# ZW
class GathererGas(Worker):
    """Worker who gathers resources."""

    name: str = 'Gatherer - Gas'

    target: Type[Job]

    def __init__(self, bot: IDABot, unit: Unit, target: Type[Job]):
        self.target = target
        unit.right_click(target.unit)
        super().__init__(bot, unit)

    def on_step(self, bot: IDABot):
        # if unit.is_idle:
        # click_closest_refinery(bot, unit)
        super().on_step(bot)

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not any_units_with_job(Refinery):
            return False
        else:
            return True


# ZW
class Refinery(Structure):

    name: str = "Refinery"

    clients: Dict = {}  # Gathering Centers ONLY!

    must_be = refineries_TYPEID

    def __init__(self, bot: IDABot, unit: Unit):
        super().__init__(bot, unit)

        GathererGas.clients[self] = 3

    def on_step(self, bot: IDABot):
        super().on_step(bot)

    def on_discharge(self, bot: IDABot):
        del GathererGas.clients[self]

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if unit.unit_type.unit_typeid not in refineries_TYPEID:
            return False
        else:
            return super().is_qualified(bot, unit)

    @classmethod
    def get_demand(cls, bot):
        result = 0
        for demand in cls.clients.values():
            result += demand
        return 3 * result + cls.demand
