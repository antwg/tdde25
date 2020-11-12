from scai_backbone import *
from job_system.employer import *


# ZW
class MyAgent(ScaiBackbone):
    """In game bot."""

    def on_game_start(self):
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_game_start(self)

        Employer.load_system(self)

        pass

    def on_step(self):
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_step(self)

        for unit in self.get_my_units():
            job = find_unit_job(unit)
            if job:
                job.on_step(self, unit)
            elif not Employer.is_banned(unit):
                Employer.assign(self, unit)

        # DP
    def print_debug(self):
        """Function that displays the units type, id and enumerate index"""

        unit_list = self.get_all_units()
        for i, unit in list(enumerate(unit_list)):
            text = str((unit.unit_type, "ID:", unit.id, "I:", i))
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))


if __name__ == "__main__":
    MyAgent.bootstrap()

