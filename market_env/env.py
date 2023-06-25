import numpy as np
import pandas as pd

class ChainEnv:
    def __init__(
        self,
        users: dict[str, User] | None = None,
        proposers: dict[str, Proposer] | None = None,
        builders: dict[str, Builder] | None = None,
        mempools: Mempool | None = None,
        blocks: Block | None = None,
    ):

        if users is None:
            users = {}
        if proposers is None:
            proposers = {}
        if builders is None:
            builders = {}
        if mempools is None:
            mempools = []
        if blocks is None:
            blocks = []

        self.users = users
        self.proposers = proposers
        self.builders = builders
        self.mempools = mempools
        self.blocks = blocks

class User:
    def __init__(self, user_id, env: ChainEnv, name: str):
        self.user_id = user_id
        self.env = env
        self.env.users[name] = self

    # users initiate transactions to a recipient
    def create_transaction(self, transaction_id, amount, recipient):
        transaction = Transaction(transaction_id, amount, recipient)
        return transaction
    
    # users send transactions to mempool
    def send_transaction(self, transaction):
        self.env.mempools.add_transaction(transaction)

class Proposer:
    def __init__(self, proposer_id):
        self.proposer_id = proposer_id

    # select the block with the highest pay
    def select_block(self, block_id, builder_blocks):
        selected_block = max(builder_blocks, key=lambda block: block.get_pay())
        return selected_block

class Builder:
    def __init__(self, builder_id):
        self.builder_id = builder_id
        self.mempool = None

    def set_mempool(self, mempool):
        self.mempool = mempool

    # check mempoool, order the transactions, and build the block
    def build_block(self, block_id):
        if self.mempool is None:
            raise ValueError("Mempool not set for the builder.")

        transactions = self.mempool.get_transactions()
        ordered_transactions = self.order_transactions(transactions)

        block = Block(block_id)
        for transaction in ordered_transactions:
            block.add_transaction(transaction)
        return block

    # order transactions by gas usage
    def order_transactions(self, transactions):
        ordered_transactions = sorted(transactions, key=lambda x: x.gas_usage)
        return ordered_transactions

class Mempool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_transactions(self):
        return self.transactions

class Block:
    def __init__(self, block_id):
        self.block_id = block_id
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_transactions(self):
        return self.transactions
