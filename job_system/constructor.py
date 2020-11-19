from job_system.economics import *


# ZW
class ConstructionOrder:
    need: int = 1
    where: Union[Point2DI, UnitType]
    what: UnitType

    def __init__(self, what: UnitType, where: Union[Point2D, UnitType],
                 need: int = 10):
        self.need = need
        self.where = where
        self.what = what

 
construct_queue = []


def add_building_request(what: UnitType, where: Union[Point2D, UnitType],
                         need: int = 10):
    construct_queue.append(ConstructionOrder(what, where, need))


# ZW
class Builder(Worker):
    """Worker who construct buildings."""

    name: str = 'Builder'

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not construct_queue:
            return False
        else:
            return super().is_qualified(bot, unit)

    def __init__(self, bot: IDABot, unit: Unit):
        """Called when unit is assigned to job."""
        # unit.build(self.build_this)
        super().__init__(bot, unit)

    @classmethod
    def get_demand(cls, bot):
        if construct_queue:
            return 20 + 2*len(construct_queue)
        else:
            return 0
