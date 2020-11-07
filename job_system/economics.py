from job_system.job import *


# ZW
class Worker(Job):
    """Job template for Workers."""

    name: str = 'Worker -TEMPLATE-'

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.is_worker:
            return False
        else:
            return super().is_qualified(bot, unit)


# ZW
class Gatherer(Worker):
    """Worker who gathers resources."""

    name: str = 'Gatherer'

    def on_assignment(self, bot: IDABot, unit: Unit):
        self.click_closest_mineral(bot, unit)

    def on_step(self, bot: IDABot, unit: Unit):
        if unit.is_idle:
            self.click_closest_mineral(bot, unit)
        super().on_step(bot, unit)

    def click_closest_mineral(self, bot: IDABot, unit: Unit):
        mineral = find_closest_mineralfield(bot, unit.position)
        unit.right_click(mineral)


# ZW
class Builder(Job):
    """Worker who construct buildings."""

    name: str = 'Builder'

    def on_assignment(self, unit: Unit):
        """Called when unit is assigned to job."""
        unit.build(self.build_this)





