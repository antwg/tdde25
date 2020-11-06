from job_system.job import *


# ZW
class Worker(Job):
    """Job template for Workers."""

    name: str = 'Worker -TEMPLATE-'

    @classmethod
    def is_qualified(cls, unit: Unit):
        if not unit.unit_type.is_worker:
            return False
        else:
            return super().is_qualified(unit)


# ZW
class Gatherer(Worker):
    """Worker who gathers resources."""

    name: str = 'Gatherer'

    @classmethod
    def on_step(cls, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""

        super().on_step(bot, unit)


# ZW
class Builder(Job):
    """Worker who construct buildings."""

    name: str = 'Builder'

    @classmethod
    def on_step(cls, bot: IDABot, unit: Unit):
        """What kind of work the unit shall do on_step()."""
        super().on_step(bot, unit)



