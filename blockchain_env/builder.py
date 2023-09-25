from blockchain_env.constants import BUILDER_STRATEGY_LIST
from blockchain_env.account import Account

import random
class Mempool:
    def __init__(self) -> None:
        self.transactions = []

    def add_transaction(self, transaction) -> None:
        self.transactions.append(transaction)

    def remove_transaction(self, transaction) -> None:
        if transaction in self.transactions:
            self.transactions.remove(transaction)

class Builder(Account):
    def __init__(self, address,
                balance: float,
                builder_strategy: str = "greedy",
                mempool: dict[str, Mempool] | None = None
    ):
        if mempools is None:
            mempools = {}
        super().__init__(address, balance)
        # make sure builder_strategy is a str from the list of available strategies
        assert builder_strategy in BUILDER_STRATEGY_LIST, f"The builder_strategy must be one of {BUILDER_STRATEGY_LIST}."
        self.builder_strategy = builder_strategy
        self.mempool = mempool
    
    def select_transactions(self):
        if self.builder_strategy == "greedy":
            # Select the transaction with the highest fee
            if not self.mempool.transactions:
                return None  
            selected_transaction = max(self.mempool.transactions, key=lambda x: x.fee)
            return selected_transaction

        elif self.builder_strategy == "random":
            # Select a random transaction from the mempool
            if not self.mempool.transactions:
                return None  
            selected_transaction = random.choice(self.mempool.transactions)
            return selected_transaction

        elif self.builder_strategy == "first come first serve":
            # Select the transaction with the earliest timestamp
            if not self.mempool.transactions:
                return None  
            selected_transaction = min(self.mempool.transactions, key=lambda x: x.timestamp)
            return selected_transaction

        else:
            raise ValueError("Invalid builder_strategy")
