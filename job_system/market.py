from library import *

from job_system.job import *


class Market:

    jobs: list = []
    orders: List

    makers: dict = {}

    def request_job(self, job: Type[Job]):
        pass

    def request_order(self, unit_type: UnitType, quantity: int = 1):
        self.orders.append()

    def take_order(self, taker: Type[Job], order_index: int):
        pass
