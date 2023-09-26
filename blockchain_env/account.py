from blockchain_env.chain import Transaction
from blockchain_env.constants import BASE_FEE
from blockchain_env.builder import Builder
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

    def create_transaction(self, recipient, amount: float, base_fee: float = BASE_FEE, priority_fee: float = 0):
        """
        Create a transaction and add it to the mempool.
        """
        transaction_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())

        total_fee = amount * (base_fee + priority_fee)
        if self.balance < total_fee + amount:
            print(f"Insufficient balance to create the transaction.")
            return
        
        transaction = Transaction(transaction_id, timestamp, self.address, recipient, amount, base_fee, priority_fee)
        # selected_builders = random.sample(builders, len(builders) // 2)
        # for builder in selected_builders:
        Builder.mempool.add_transaction(transaction) 
        self.balance -= total_fee + amount
