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
                if job.is_bored():
                    Employer.snark_job(self, job)

                if job.committed_plan:
                    job.invest(self)
                else:
                    job.on_step(self)
            elif not Employer.is_banned(unit):
                Employer.assign(self, unit)

    def can_afford(self, ut: UnitType) -> bool:
        return ut.mineral_price <= self.minerals \
                and ut.gas_price <= self.gas \
                and ut.supply_required <= self.max_supply - self.current_supply


if __name__ == "__main__":
    MyAgent.bootstrap()
