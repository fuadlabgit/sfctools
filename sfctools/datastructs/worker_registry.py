__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod



from collections import defaultdict
import numpy as np


class WorkerRegistry:
    """
    The (rudimentary) worker registry keeps track of all agents that work at a firm (or other agent)

+----------+
|  Worker  |
+----------+
|   Agent1 |
+----------+
|   Agent2 |
+----------+
|   ...    |
+----------+
|          |
|   AgentN |
+----------+

    """

    def __init__(self, owner,wage_attr="reservation_wage"):
        """
        constructor for worker registry
        """
        self.owner = owner

        self.agent_data = []
        self.total_workforce = 0.0
        self.wage_bill = defaultdict(lambda: 0.0) # stores the wage expenditures by time

        self.wage_attr = wage_attr

    def add_worker(self ,agent):
        """
        add a worker and corresponding wage to the registry
        """
        print(self.owner,"add worker",agent)
        agent.employer = self.owner
        self.agent_data.append(agent)
        self.total_workforce += 1

    def remove_worker(self, agent):
        """
        remove a worker from registry (has been fired, retired, ...)
        """

        if hasattr(self.owner,"labor_market"):
            self.owner.labor_market.unlink_agents(agent, agent.employer)

        agent.is_employed = 0.0
        agent.employer = None

        self.agent_data.remove(agent)
        self.total_workforce -= 1

    def get_avg_costs(self):
        """
        computes the cost of labor, i.e. the average value of all wages
        """
        # each worker works 1 unit
        vals = [getattr(worker,self.wage_attr) * 1.0 for worker in self.agent_data]

        if len(vals) > 0:

            return np.mean(vals)
        else:
            return 0

    def fire_random(self, number):
        """
        fire a certain number of workers at random
        """

        print("fire",self.agent_data)

        for i in range(min(number, len(self.agent_data))):
            random_worker = np.random.choice(self.agent_data)
            self.remove_worker(random_worker)

    def fire_all(self):
        """
        remove all workers from the registry
        """
        for worker in self.agent_data:
            self.remove_worker(worker)
