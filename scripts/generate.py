from blockchain_env.account import Account
from blockchain_env.chain import Block, Chain
from blockchain_env.builder import Builder, Mempool
from blockchain_env.constants import BASE_FEE, GAS_LIMIT
from blockchain_env.proposer import Blockpool, Proposer
from blockchain_env.transaction import Transaction

import random

def generate_accounts(num_accounts):
    accounts = []
    for i in range(num_accounts):
        address = f"Address{i}"
        balance = random.uniform(100.0, 1000.0)
        account = Account(address, balance)
        accounts.append(account)
    return accounts

def generate_transactions(accounts, num_transactions):
    transactions = []
    for _ in range(num_transactions):
        sender = random.choice(accounts)
        recipient = random.choice(accounts)
        while sender == recipient:
            recipient = random.choice(accounts)
        
        amount = random.uniform(1.0, 10.0)  
        base_fee = BASE_FEE
        priority_fee = random.uniform(0.0, 5.0)  
        transaction = sender.create_transaction(recipient, amount, base_fee, priority_fee)
        transactions.append(transaction)
    return transactions

def generate_builders(num_builders):
    builders = []
    for i in range(num_builders):
        builder = Builder(f"Builder{i}", initial_balance)
        builders.append(builder)
    return builders

def generate_proposers(num_proposers):
    proposers = []
    for i in range(num_proposers):
        proposer = Proposer(f"Proposer{i}", initial_balance)
        proposers.append(proposer)
    return proposers

num_accounts = 200
num_transactions = 100
initial_balance = 100.0
num_builders = 20
num_proposers = 20



if __name__ == "__main__":
    accounts = generate_accounts(num_accounts)
    transactions = generate_transactions(accounts, num_transactions)
    builders = generate_builders(num_builders)
    proposers = generate_proposers(num_proposers)

    for account in accounts:
        print(account.address, account.balance)
    for transaction in transactions:
        print(
            f"Transaction ID: {transaction.transaction_id}, Sender: {transaction.sender}, "
            f"Recipient: {transaction.recipient}, Amount: {transaction.amount}, "
            f"Base Fee: {transaction.base_fee}, Priority Fee: {transaction.priority_fee}"
        )
    for builder in builders:
        print(builder.address, builder.balance)
    for proposer in proposers:
        print(proposer.address, proposer.balance)