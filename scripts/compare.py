"""This file compares the profit distribution and mev rate of PoS with and without PBS"""

import random
import numpy as np

random.seed(42)

NUM_PARTICIPANTS = 20
NUM_TRANSACTIONS = 500
TRANSACTION_CAPACITY = 50

class Transaction:
    def __init__(self, id, fee, is_mev, creator_id):
        self.id = id
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id

def generate_transactions(num_transactions, participants):
    transactions = []
    for _ in range(num_transactions):
        fee = random.uniform(0.01, 0.1)
        is_mev = False  # Regular transactions are not MEV
        transactions.append(Transaction(id, fee, is_mev, Participant.id))

    # Generate a high-fee MEV transaction for each MEV-oriented participant
    for participant in participants:
        if participant.is_mev:
            transactions.append(Transaction(id, fee, True, Participant.id))
    
    return transactions

class Participant:
    def __init__(self, id, is_mev):
        self.id = id
        self.is_mev= is_mev 

    def select_transactions(self, transactions):
        if self.is_mev:
            selected_transactions = sorted(transactions, key=lambda x: (x.is_mev, x.fee), reverse=True)
        else:
            selected_transactions = sorted(transactions, key=lambda x: x.fee, reverse=True)
        return selected_transactions
    
class Builder(Participant):
    def bid_for_block(self, transactions):
        pass

class Proposer:
    def select_winner(self, bids):
        return max(bids, key=bids.get)

def simulate_pbs(transactions, builders, proposer):
    bids = {builder: builder.bid_for_block(transactions) for builder in builders}
    winner = proposer.select_winner(bids)
    # Winner builds the block with their preferred transactions
    block_transactions = winner.select_transactions(transactions)
    return block_transactions, bids[winner]

class Validator(Participant):
    pass


def simulate_pos(transactions, validators):
    validator = random.choice(validators)
    block_transactions = validator.select_transactions(transactions)
    return block_transactions