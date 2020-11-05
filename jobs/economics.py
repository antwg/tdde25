from library import *

from jobs.employer import Job
from debug import *


class Structure(Job):
    """Do nothing but look pretty."""

    @classmethod
    def on_step(cls, unit: Unit):
        """Just wait."""

        print_unit_info(unit)


class Gatherer(Job):
    """Gather resources."""

    @classmethod
    def on_step(cls, unit: Unit):
        """Gather resources."""

        print_unit_info(unit)

