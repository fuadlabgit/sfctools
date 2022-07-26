__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'test' # options are: dev, test, prod

from collections import defaultdict
from ..core.agent import Agent
from ..bottomup.matching import MarketMatching
import pandas as pd
import numpy as np


class BankOrderBook:
    """
    The order book keeps track of all agents that have deposits and loans at a bank.

    loans data:

    .. code-block:: python

            {
            Agent1: list[Table],
            Agent2: list[Table],
            ...
            }

    Loans:

    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |  ID      | Agent     | Loans    | interest on loans (r_l) |   Loan Payback rate (absolute)  | Time | Loan Duration  |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |     0    |  10.0     |          | 0.05                    |  0.01                           | ...  |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |     1    |   ...     |          |                         |                                 |      |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |          |           |          |                         |                                 |      |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |          |   ...     |          |                         |                                 |      |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |          |           |          |                         |                                 |      |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+
    |     42   |   ...     |          |                         |                                 |      |                |
    +----------+-----------+----------+-------------------------+---------------------------------+------+----------------+


    Deposits:

    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |  ID      | Agent     |  Depos.   | interest on deposits (r_d)  |   Time                          |  Duration  |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |     0    |  10.0     |  0.05     |                             |  0.01                           |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |     1    |   ...     |           |                             |                                 |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |          |           |           |                             |                                 |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |          |   ...     |           |                             |                                 |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |          |           |           |                             |                                 |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+
    |     42   |   ...     |           |                             |                                 |            |
    +----------+-----------+-----------+-----------------------------+---------------------------------+------------+

    """

    def __init__(self, owner,credit_market:MarketMatching,deposit_market:MarketMatching):
        """
        constructor

        :param owner: agent instance who owns this data structure
        :credit_market: a MarketMatching obect for the credit market
        :deposit_market:  a MarketMatching object or the deposit market

        """

        self.owner = owner
        self.loans_data = defaultdict(list)
        self.deposits_data = defaultdict(list)

        """
        deposits, loans, r_d, r_l
        """

        self.idx_d = 0  # index counter deposits
        self.idx_l = 0  # index counter loans

        self.total_deposits = 0.0
        self.total_loans = 0.0

        self.credit_market = credit_market
        self.deposit_market = deposit_market

    def __repr__(self):
        return "<Order Book of %s>" %self.owner

    def to_string(self):
        """
        string representation of this data structure
        """
        s = "----  ORDER BOOK of {0:20} -----------------------------------------".format(str(self.owner))

        data = {"ID":[],"Agent":[],"Loans":[],"r_l":[],"payback rate":[],"time":[],"duration":[]}
        for agent, listing in self.loans_data.items():
            for entry in listing:
                data["ID"].append(entry["idx"])
                data["Agent"].append(agent)
                data["Loans"].append(entry["Loans"])
                data["r_l"].append(entry["r_l"])

                data["payback rate"].append(entry["payback"])
                data["time"].append(entry["time"])
                data["duration"].append(entry["loan duration"])

        loans_df = pd.DataFrame(data).set_index("ID")
        if loans_df.empty:
            loans_str = "(None)"
        else:
            loans_str = loans_df.to_string()

        s+= "\nLoans: %.2f\n"%self.total_loans + loans_str+ "\n\n"

        data = {"ID": [], "Agent":[], "Deposits": [], "r_d": [], "time":[],"duration":[]}

        for agent,listing in self.deposits_data.items():
            for entry in listing:
                data["ID"].append(entry["idx"])
                data["Agent"].append(agent)
                data["Deposits"].append(entry["Deposits"])
                data["r_d"].append(entry["r_d"])
                data["time"].append(entry["time"])
                data["duration"].append(entry["duration"])

        deposits_df =  pd.DataFrame(data).set_index("ID")
        if deposits_df.empty:
            deposits_str = "(None)"
        else:
            deposits_str = deposits_df.to_string()

        s += "\nDeposits: %.2f\n"%self.total_deposits +deposits_str+ "\n\n"
        s += "----------------------------------------------------------------------------------"
        return s

    def remove_loan(self, idx, agent):
        """
        Removes a whole entry (this should be called when a loan is entirely paid back)

        :param idx: id of the loan
        :param agent: agent belonging to the loan
        """

        self.credit_market.unlink_agents(supply_agent=self.owner, demand_agent=agent)

        remove_index = None
        # find the entry with the corresponding index
        for i,entry in enumerate(self.loans_data[agent]):
            if entry["idx"] == idx:
                remove_index = i

        if remove_index is None:
            raise KeyError("Could not find entry")

        self.total_loans -= self.loans_data[agent][remove_index]["Loans"]
        del self.loans_data[agent][remove_index]

    def remove_deposit(self, idx, agent):
        """
        remove a deposit by index

        :param idx: index of entry
        :param agent: agent who belongs to this deposit
        """

        self.deposit_market.unlink_agents(supply_agent=agent, demand_agent=self.owner)

        remove_index = None
        # find the entry with the corresponding index
        for i, entry in enumerate(self.deposits_data[agent]):
            if entry["idx"] == idx:
                remove_index = i

        if remove_index is None:
            raise KeyError("Could not find entry")

        self.total_deposits -= self.deposits_data[agent][remove_index]["Deposits"]

        # print("REMOVE DEPOSIT", self, idx, agent,self.deposits_data[agent][remove_index]["Deposits"])

        del self.deposits_data[agent][remove_index]

    def withdraw_from_account(self,agent,quantity):
        """
        withdraw money from deposit account.

        :param agent: agent who withdraws
        :param quantity: quantity to withdraw
        """

        # print("WITHDRAW DEPOSIT", self,  agent,quantity)

        x = 0
        removals = []

        for i, entry in enumerate(self.deposits_data[agent]):
            D = entry["Deposits"]
            idx = entry["idx"]

            remaining_amount = quantity-x
            if remaining_amount < D:  # only change the account
                self.deposits_data[agent][i]["Deposits"] -= remaining_amount

                assert self.deposits_data[agent][i]["Deposits"] >= 0, print(self.deposits_data[agent][i]["Deposits"])
                self.total_deposits -= remaining_amount
                x += remaining_amount

                break

            else:  # completely remove the account
                removals.append(idx)
                x += D

        for idx in removals:
            self.remove_deposit(idx, agent)


    def add_deposits(self, agent: Agent, new_deposits, r_d,t=np.inf):
        """
        add deposits of an agent at this bank

        :param agent: reference to agent
        :param new_deposits: amount of new deposits
        :param r_d: interest rate on deposits
        :param t: time of the deposits
        """

        # print("ADD DEPOSIT", self, agent, new_deposits)

        self.idx_d += 1

        self.deposits_data[agent].append({
            "idx":self.idx_d,
            "Deposits": new_deposits,
            "r_d":r_d,
            "time":0,
            "duration":t
        })

        self.total_deposits += new_deposits

    @property
    def depositors(self) -> dict:
        # gets a list of depositors and their deposits

        deps = defaultdict(lambda: 0.0)
        for key,val in self.deposits_data.items():

            agent = key
            deposits = 0.0
            for entry in val:
                deposits += entry["Deposits"]

            deps[agent] = deposits

        return deps

    @property
    def debtors(self) -> dict:
        # gets a list of debtors and their loans

        loans = defaultdict(lambda: 0.0)
        for key, val in self.loans_data.items():

            agent = key
            deposits = 0.0
            for entry in val:
                deposits += entry["Loans"]

            loans[agent] = deposits

        return loans

    def get_deposit_interest_of(self,agent) -> float:
        """
        compute the mean interest rate an agent is paid
        """

        i = []
        for entry in self.deposits_data[agent]:
            i.append(entry["r_d"])
        return np.mean(i)

    def get_loan_interest_of(self, agent) -> float:
        """
        compute the mean interest rate an agent pays

        :param agent: reference to an agent instance
        """

        i = []
        for entry in self.deposits_data[agent]:
            i.append(entry["r_l"])
        return np.mean(i)

    def get_deposits_of(self, agent) -> float:
        """
        returns the total deposts of an agent

        :param agent: reference to an agent instance
        """

        total_deposits = 0.0
        for entry in self.deposits_data[agent]:
            total_deposits += entry["Deposits"]

        return total_deposits

    def get_loans_of(self,agent) -> float:
        """
        returns the total loans of an agent

        :param agent: reference to an agent instance
        """

        total_loans = 0.0
        for entry in self.loans_data[agent]:
            total_loans += entry["Loans"]

        return total_loans

    def add_loans(self, agent:Agent, new_loans:float, r_l: float, t=20):
        """
        add loans of an agent at this bank

        :param agent: reference to agent
        :param new_loans: amount of new loans
        :param r_l: interest rate on loans
        :param t: payback time (default 20 periods)
        """

        assert new_loans > 0

        self.idx_l += 1

        self.loans_data[agent].append({
            "idx": self.idx_l,
            "Loans": new_loans,
            "r_l": r_l,
            "payback": new_loans/(1.0*t),
            "time": 0,
            "loan duration": t
        })

        self.total_loans += new_loans


    def debt_equity_swap(self, agent, q):
        """
        writes off a debt-equity swap

        :param agent: refrence to an agent instance
        :param q: quanity to write off
        """

        entries = self.loans_data[agent]

        cumu = 0  # cumulative variable (debt written off)

        for i, entry in enumerate(entries):

            if cumu >= 0:
                break

            if entry["Loans"] <= q - cumu:  # require whole entry?
                cumu += entry["Loans"]
                self.remove_loan(entry["idx"], agent)

            else:  # require only part of entry?
                cumu += q - cumu
                self.total_loans -= q - cumu

                self.loans_data[agent][i]["Loans"] -= q - cumu  # partially reduce entry
                # re-adjust the amount of loan payback
                t_remain = self.loans_data[agent][i]["loan duration"] - self.loans_data[agent][i]["time"]
                self.loans_data[agent][i]["payback"] = self.loans_data[agent][i]["Loans"] / (1.0 * t_remain)

                return


    def write_off_bad_debt(self, agent, q):
        """
        books a bad debt. This means that loans are written off this data struct.

        :param agent: the agent concerning the bad debt
        :param q: amount of bad debt to write off
        """

        assert q >= 0,  q

        entries = self.loans_data[agent]

        cumu = 0  # cumulative variable (debt written off)

        for i, entry in enumerate(entries):

            if cumu >= q:
                break

            if entry["Loans"] <= q-cumu:  # require whole entry?
                self.remove_loan(entry["idx"],agent)
                cumu += entry["Loans"]

            else:  # require only part of entry?
                self.loans_data[agent][i]["Loans"] -= q-cumu  # partially reduce entry
                cumu += q-cumu
                self.total_loans -= q-cumu

                # re-adjust the amount of loan payback
                t_remain = self.loans_data[agent][i]["loan duration"] - self.loans_data[agent][i]["time"]
                self.loans_data[agent][i]["payback"] = self.loans_data[agent][i]["Loans"] / (1.0*t_remain)

                return
