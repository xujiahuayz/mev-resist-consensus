import random

class Transaction:
    def __init__(self, fee, is_mev):
        self.fee = fee 
        self.is_mev = is_mev

class Participant:
    def __init__(self, is_mev):
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