"""This file compares the profit distribution and mev rate of PoS with and without PBS"""

import random
import numpy as np

random.seed(42)

NUM_USERS = 100
NUM_BUILDERS = 20
NUM_VALIDATORS = 20
NUM_PROPOSERS = 5
BLOCK_CAPACITY = 50
NUM_TRANSACTIONS = 100

MEV_FEE_MIN = 0.05
MEV_FEE_MAX = 0.2
NON_MEV_FEE_MIN = 0.01
NON_MEV_FEE_MAX = 0.15

class Transaction:
    def __init__(self, fee, is_mev, creator_id=None):
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id

class Participant:
    def __init__(self, id, is_mev):
        self.id = id
        self.is_mev = is_mev
        self.mev_transaction = None
        if self.is_mev:
            self.mev_transaction = self.create_transaction(True)

    def create_transaction(self, is_mev):
        if is_mev:
            fee = random.triangular(MEV_FEE_MIN, MEV_FEE_MAX, MEV_FEE_MAX * 0.75)
        else:
            fee = random.uniform(NON_MEV_FEE_MIN, NON_MEV_FEE_MAX)
        return Transaction(fee, is_mev, self.id)


class Builder(Participant):
    def select_transactions(self, transactions):
        # If MEV-oriented, ensure the builder's MEV transaction is considered
        if self.mev_transaction:
            transactions = [self.mev_transaction] + transactions
        transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = transactions[:BLOCK_CAPACITY]
        return selected_transactions


class Validator(Participant):
    def select_transactions(self, transactions):
        if self.mev_transaction:
            transactions = [self.mev_transaction] + transactions
        transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = transactions[:BLOCK_CAPACITY]
        return selected_transactions

class run_PBS:
    pass

class run_PoS:
    pass
