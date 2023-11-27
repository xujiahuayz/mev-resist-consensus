# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring, too-many-instance-attributes, too-many-arguments,too-few-public-methods
import uuid
from datetime import datetime
import random
import numpy as np

from blockchain_env.constants import BASE_FEE, GAS_LIMIT
from blockchain_env.account import Account
from blockchain_env.transaction import Transaction


class Mempool:
    def __init__(self, address: str) -> None:
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
                # builder_strategy: str = "mev",
                builder_strategy: None = None,
                discount: float | None = None,
                private: bool = False,
                credit=0.0,
                inclusion_rate=0.0
    ):
        super().__init__(address, balance)
        # assert builder_strategy in BUILDER_STRATEGY_LIST, f"The builder_strategy must
        # be one of {BUILDER_STRATEGY_LIST}."
        self.builder_strategy = builder_strategy
        self.discount = discount if discount is not None else np.random.random()
        self.mempool = Mempool(self.address)
        self.private = private
        self.credit = credit
        self.inclusion_rate = inclusion_rate
        self.notebook = {}
        self.mev_profits = 0


    # def update_notebook(self, transaction):
    #     self.notebook[transaction.sender] = self.notebook.get(transaction.sender,
    # self.get_balance(transaction.sender)) - (transaction.amount + transaction.fee)
    #     self.notebook[transaction.recipient] = self.notebook.get(transaction.recipient,
    # self.get_balance(transaction.recipient)) + transaction.amount

    # def revert_notebook(self, transaction):
    #     self.notebook[transaction.sender] += (transaction.amount + transaction.fee)
    #     self.notebook[transaction.recipient] -= transaction.amount
    #     pass

    # def get_balance(self, address, chain):
    #     for account in chain.normal_users + chain.proposers + chain.builders:
    #         if account.address == address:
    #             return account.balance
    #     raise ValueError(f"No account found for address {address}")

    def inclusion_count(self):
        self.inclusion_rate += 1

    def select_transactions(self):
        selected_transactions = []  # Initialize an empty list for selected transactions
        remaining_gas = GAS_LIMIT
        self.mev_profits = 0

        if self.builder_strategy == "greedy":
            sorted_transactions = sorted(self.mempool.transactions,
                                         key=lambda x: x.priority_fee, reverse=True)
        elif self.builder_strategy == "mev":
            sorted_transactions = sorted(self.mempool.transactions,
                                         key=lambda x: x.priority_fee, reverse=True)
            num_to_sample = min(len(sorted_transactions), 10)
            mev_target = random.sample(sorted_transactions, num_to_sample)
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
                # self.update_notebook(transaction)
                # if self.notebook.get(transaction.sender) < 0 or
                # self.notebook.get(transaction.recipient) < 0:
                #     self.revert_notebook(transaction)
                # else:
                selected_transactions.append(transaction)
                remaining_gas -= transaction_gas
                if self.builder_strategy == "mev" and transaction in mev_target:
                    mev_deduction = random.uniform(0.1, 0.3) * transaction.amount
                    transaction.amount -= mev_deduction
                    self.mev_profits += mev_deduction
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
            return True

    # Method to add bid for the transactions
    # Input: selected_transactions, proposer_address, self.address
    # Output: bid_transaction
    # Steps: 10% of the transaction fee is put for bid
    def bid(self, proposer_address):
        # call the select_transactions method to get the selected_transactions
        selected_transactions = self.select_transactions()
        # calculate the 10% of the total transaction fee
        bid_amount = sum(transaction.fee * random.uniform(0.1, 0.3) for
                         transaction in selected_transactions)

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

    def update(self, selected, used_mev):
        if selected:
            self.inclusion_rate = min(self.inclusion_rate + 0.1, 1.0)
            self.credit = max(self.credit + 0.1, 0.0)
        if used_mev:
            self.credit = max(self.credit - 0.2, 0.0)


if __name__ == "__main__":
    # selected_transactions.append(bid_transaction)
    pass
