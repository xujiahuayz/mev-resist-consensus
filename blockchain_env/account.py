from blockchain_env.constants import BASE_FEE
from blockchain_env.transaction import Transaction
import uuid
from datetime import datetime
import random

class Account:
    def __init__(self, address, balance: float):
        """
        Initialize a new account.
        """
        self.address = address
        self.balance = balance

    def deposit(self, amount: float):
        """
        Deposit amount to the account.
        """
        self.balance += amount

    def withdraw(self, amount: float):
        """
        Withdraw amount from the account.
        """
        if self.balance < amount:
            print(f"Insufficient balance. the amount to withdraw is {amount} but address {self.address} only has {self.balance}")
            return
        self.balance -= amount

if __name__ == "__main__":
    # user1 = Account(x,x,x)
    # builder1 = Builder("dsdsd", 2121212, , x, x)

    # trans1 = user1.create_transaction(x,x,x,x)
    # builder1.mempool.add_transaction(trans1)
    pass