from blockchain_env.constants import BUILDER_STRATEGY_LIST, BASE_FEE
from blockchain_env.account import Account
from blockchain_env.proposer import Proposer
from blockchain_env.chain import Transaction
import uuid
from datetime import datetime
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
        selected_transactions = []  # Initialize an empty list for selected transactions
        remaining_gas = self.gas_limit
        
        if self.builder_strategy == "greedy":
            # Sort transactions by fee in descending order
            sorted_transactions = sorted(self.mempool.transactions, key=lambda x: x.fee, reverse=True)
        elif self.builder_strategy == "random":
            # Shuffle transactions randomly
            random.shuffle(self.mempool.transactions)
            sorted_transactions = self.mempool.transactions
        elif self.builder_strategy == "FCFS":
            # Sort transactions by timestamp in ascending order
            sorted_transactions = sorted(self.mempool.transactions, key=lambda x: x.timestamp)
        else:
            raise ValueError("Invalid builder_strategy")

        # Iterate through sorted transactions and add them to the list until gas limit is reached
        for transaction in sorted_transactions:
            transaction_gas = transaction.gas
            if remaining_gas >= transaction_gas:
                selected_transactions.append(transaction)
                remaining_gas -= transaction_gas
            else:
                break  
        
        return selected_transactions
        
    def bid(self):
        for selected_transaction in self.select_transactions():
            # 10% of the transaction fee is put for bid
            bid = selected_transaction.fee * 0.1
            # send this information to proposer's blockpool
            bid_transaction = Transaction(
                            transaction_id=str(uuid.uuid4()),
                            timestamp=int(datetime.now().timestamp()),
                            sender=self.proposer_address,  # Set the proposer as the sender
                            recipient=self.address,  # The builder's address is the recipient
                            amount=bid,
                            base_fee=BASE_FEE,  # Replace with the actual base fee
                            priority_fee=0  # No priority fee for the bid
                        )
            self.selected_transactions.append(bid_transaction)
            Proposer.blockpool.add_body(self, selected_transaction, bid)

if __name__ == "__main__":
    pass