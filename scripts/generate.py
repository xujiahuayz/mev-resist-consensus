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
initial_balance = 100.0
num_builders = 20
num_proposers = 20

builders = generate_builders(num_builders)
proposers = generate_proposers(num_proposers)