from job_system.job import *


# ZW
class Structure(Job):
    """Does nothing but looking pretty."""

    name: str = 'Structure -TEMPLATE-'

    @classmethod
    def is_qualified(cls, bot: IDABot, unit: Unit):
        if not unit.unit_type.is_building:
            return False
        else:
            return super().is_qualified(bot, unit)


# ZW
class SupplyDepot(Structure):

    name = "Supply Depot"

    must_be = [UNIT_TYPEID.TERRAN_SUPPLYDEPOT]

    @classmethod
    def get_demand(cls, bot: IDABot):
        supply_provided = get_provided_supply(bot)
        if supply_provided >= 200:
            supply_overflow = (supply_provided-200)
            return 30 * (0.5**(supply_overflow/10))
        else:
            supply_left = bot.max_supply - bot.current_supply
            return 100 * (0.5**(supply_left/20))
