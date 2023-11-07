import uuid
from datetime import datetime
import random
import copy

from blockchain_env.constants import BUILDER_STRATEGY_LIST, BASE_FEE, GAS_LIMIT
from blockchain_env.account import Account
from blockchain_env.transaction import Transaction
from blockchain_env.proposer import Proposer

class Mempool:
    def __init__(self, address) -> None:
        self.transactions = []
        # here, the address is the address of the builder
        self.address = address

    def add_transaction(self, transaction: Transaction, enter_time) -> None:
        self.transactions.append(transaction)
        transaction.enter_mempool(builder_address = self.address, enter_timestamp = enter_time)

    def remove_transaction(self, transaction) -> None:
        if transaction in self.transactions:
            self.transactions.remove(transaction)

class Builder(Account):
    def __init__(self,
                address,
                balance: float,
                builder_strategy: str = "greedy",
    ):
        super().__init__(address, balance)
        # make sure builder_strategy is a str from the list of available strategies
        assert builder_strategy in BUILDER_STRATEGY_LIST, f"The builder_strategy must be one of {BUILDER_STRATEGY_LIST}."
        self.builder_strategy = builder_strategy
        # Initialize a mempool for the builder, which should have the same address as the builder
        self.mempool = Mempool(self.address)
        self.notebook: []

    def update_notebook(self, transaction):
        self.notebook[transaction.sender] = self.notebook.get(transaction.sender, self.get_balance(transaction.sender)) - (transaction.amount + transaction.fee)

    def revert_notebook(self, transaction):
        pass

    def get_balance(self, address):
        pass

    def select_transactions(self):
        selected_transactions = []  # Initialize an empty list for selected transactions
        remaining_gas = GAS_LIMIT

        if self.builder_strategy == "greedy":
            sorted_transactions = sorted(self.mempool.transactions, key=lambda x: x.priority_fee, reverse=True)
        elif self.builder_strategy == "random":
            random.shuffle(self.mempool.transactions)
            sorted_transactions = self.mempool.transactions
        elif self.builder_strategy == "FCFS":
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

    # Method to validate transactions
    # Input: transactions,balance
    # Output: True/False
    # Steps: if balance is less than amount in the transaction, return False
    #        if balance is greater than amount in the transaction, return True
    def validate_transactions(self, transactions, balance):
        for transaction in transactions:
            if balance < transaction.amount:
                return False
            balance >= transaction.amount
        return True

    # Method to add bid for the transactions
    # Input: selected_transactions, proposer_address, self.address
    # Output: bid_transaction
    # Steps: 10% of the transaction fee is put for bid
    def bid(self, proposer_address):
        # call the select_transactions method to get the selected_transactions
        selected_transactions = self.select_transactions()
        # calculate the 10% of the total transaction fee
        bid_amount = sum(transaction.fee * random.uniform(0.1, 0.3) for transaction in selected_transactions)

        # create a bid transaction
        bid_transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            timestamp=int(datetime.now().timestamp()),
            sender=proposer_address,
            recipient=self.address,
            gas=1,
            amount=bid_amount,
            base_fee=BASE_FEE,
            priority_fee=0
        )
        return bid_transaction

    def mev_front(self):
        # front running strategy for the builder
        # identify profitable bid

        pass

if __name__ == "__main__":
    # selected_transactions.append(bid_transaction)
    pass