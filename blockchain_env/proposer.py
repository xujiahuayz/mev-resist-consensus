from blockchain_env.account import Account
from blockchain_env.constants import PROPOSER_STRATEGY_LIST
from blockchain_env.transaction import Transaction
from blockchain_env.builder import Builder

import random

class Body:
    # transactions packed by builders is a body, which is a list of transactions
    # this list of transaction is the selected transactions by builder
    def __init__(self,
        transactions: list[Transaction] = None, 
        proposer_address = None, 
        select_time = None,
        builder: Builder = None
    ) -> None:
        # define the transactions in the body
        self.transactions = builder.selected_transactions.append(builder.bid_transaction)
        self.proposer_address = proposer_address
        self.selected_timestamp = select_time

class Blockpool:
    # body should consist of a list of transactions
    # blockpool should be a list of bodys
    def __init__(self, address=None) -> None:
        self.bodys = []
        # here, the address is the address of the proposer
        self.address = address

    def add_body(self, body: Body, select_time) -> None:
        self.bodys.append(body)
        for transaction in body.transactions:
            transaction.enter_blockpool(proposer_address=self.address, selected_timestamp = select_time)

    def remove_body(self, body) -> None:
        if body in self.bodys:
            self.bodys.remove(body)

class Proposer(Account):
    def __init__(self, 
                 address, balance: float, 
                 proposer_strategy: str = "greedy", 
                 blockpool: Blockpool | None = None
    ):
        if blockpool is None:
            blockpool = Blockpool()
        else:
            self.blockpool = blockpool
        super().__init__(address, balance)
        assert proposer_strategy in PROPOSER_STRATEGY_LIST, f"The proposer_strategy must be one of {PROPOSER_STRATEGY_LIST}."
        self.proposer_strategy = proposer_strategy
    
    def select_block(self) -> str | None:
        if self.proposer_strategy == "greedy":
            if not self.blockpool:
                return None  
            
            def calculate_profit(body, blockpool):
                total_profit = 0
                for transaction in body:
                    total_profit += (transaction.priority_fee * transaction.gas) - transaction.bid
                return total_profit

            selected_body = max(self.blockpool.bodys, key=lambda body: calculate_profit(body, self.blockpool), default=None)
            return selected_body

        elif self.proposer_strategy == "random":
            # Choose a body randomly from the blockpool
            if not self.blockpool:
                return None  
            selected_body = random.choice(list(self.blockpool.bodys()))
            return selected_body

        elif self.proposer_strategy == "cheap":
            # Select the body with the lowest bid price
            if not self.blockpool:
                return None  
            selected_body = min(self.blockpool.bodys(), key=lambda x: x.bid)
            return selected_body

        else:
            raise ValueError("Invalid proposer_strategy")



