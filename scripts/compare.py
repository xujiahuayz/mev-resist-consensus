"""This file compares the profit distribution and mev rate of PoS with and without PBS"""

import random
import numpy as np
import matplotlib.pyplot as plt

random.seed(42)

NUM_USERS = 100
NUM_BUILDERS = 20
NUM_VALIDATORS = 20
NUM_PROPOSERS = 5
BLOCK_CAPACITY = 50
NUM_TRANSACTIONS = 100
NUM_BLOCKS = 100

MEV_FEE_MIN = 0.05
MEV_FEE_MAX = 0.2
NON_MEV_FEE_MIN = 0.01
NON_MEV_FEE_MAX = 0.15

class Transaction:
    def __init__(self, fee, is_mev, creator_id=None, targeted=False):
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id
        self.targeted = targeted

class Participant:
    def __init__(self, id, is_mev):
        self.id = id
        self.is_mev = is_mev
        self.mev_transaction = None
        self.transactions = []
        if self.is_mev:
            self.mev_transaction = self.create_transaction(True)

    def create_transaction(self, is_mev):
        if is_mev:
            fee = random.triangular(MEV_FEE_MIN, MEV_FEE_MAX, MEV_FEE_MAX * 0.75)
        else:
            fee = random.uniform(NON_MEV_FEE_MIN, NON_MEV_FEE_MAX)
        tx = Transaction(fee, is_mev, self.id)
        self.transactions.append(tx)
        return tx
    
    def receive_transaction(self, transaction):
        self.transactions.append(transaction)

    def select_transactions(self, transactions):
        # If MEV-oriented, ensure the builder's MEV transaction is considered
        if self.mev_transaction:
            transactions = [self.mev_transaction] + transactions
        transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = transactions[:BLOCK_CAPACITY]
        return selected_transactions


class Builder(Participant):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bid_history = []
    
    def bid(self, transactions):
        block_value = sum(tx.fee for tx in transactions[:BLOCK_CAPACITY])
        last_bid = self.bid_history[-1] if self.bid_history else 0
        bid_amount = np.random.normal(last_bid, last_bid * 0.1)  
        self.bid_history.append(bid_amount)
        return bid_amount, transactions[:BLOCK_CAPACITY]

class Proposer:
    def __init__(self, id):
        self.id = id
        self.cumulative_reward = 0 

class Validator(Participant):
    pass

def run_pbs(builders, proposers, NUM_BLOCKS):
    cumulative_mev_transactions = []
    builder_profits = {builder.id: 0 for builder in builders}  # Initialize builder profits
    total_mev_transactions = 0
    
    for _ in range(NUM_BLOCKS):
        bids = []
        for builder in builders:
            bid_amount, selected_transactions = builder.bid(builder.transactions)
            total_fees_in_block = sum(tx.fee for tx in selected_transactions)
            profit_from_block = total_fees_in_block - bid_amount  
            builder_profits[builder.id] += profit_from_block  
            bids.append((bid_amount, selected_transactions))
        
        highest_bid = max(bids, key=lambda x: x[0])
        winning_block = highest_bid[1]
        mev_transactions_in_block = sum(1 for tx in winning_block if tx.is_mev)

        total_mev_transactions += highest_bid[2]
        cumulative_mev_transactions.append(total_mev_transactions)

    return cumulative_mev_transactions, builder_profits

def run_pos(validators, num_blocks):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators}  # Initialize validator profits
    total_mev_transactions = 0
    
    for _ in range(num_blocks):
        validator = random.choice(validators)
        selected_transactions = sorted(validator.transactions, key=lambda x: x.fee, reverse=True)[:BLOCK_CAPACITY]
        mev_transactions_in_block = sum(tx.is_mev for tx in selected_transactions)
        profit_from_block = sum(tx.fee for tx in selected_transactions)
        validator_profits[validator.id] += profit_from_block 
        
        total_mev_transactions += mev_transactions_in_block
        cumulative_mev_transactions.append(total_mev_transactions)

    return cumulative_mev_transactions, validator_profits

def plot_cumulative_mev(cumulative_mev_pbs, cumulative_mev_pos):
    plt.figure(figsize=(10, 6))
    plt.plot(cumulative_mev_pbs, label='PBS', alpha=0.7)
    plt.plot(cumulative_mev_pos, label='PoS', alpha=0.7)
    plt.title('Cumulative MEV Transactions Included Over Blocks')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Number of MEV Transactions Included')
    plt.legend()
    plt.show()

def plot_profit_distribution(builder_profits, validator_profits, num_blocks):
    plt.figure(figsize=(10, 6))
    selected_builders = list(builder_profits.keys())[:5]  # Select first 5 builders
    selected_validators = list(validator_profits.keys())[:5]  # Select first 5 validators
    
    # Assuming profits are cumulative, plot them directly
    for builder_id in selected_builders:
        plt.plot(range(num_blocks), builder_profits[builder_id], label=f'Builder {builder_id}', alpha=0.7)
    for validator_id in selected_validators:
        plt.plot(range(num_blocks), validator_profits[validator_id], label=f'Validator {validator_id}', alpha=0.7)
    
    plt.title('Profit Distribution Over Blocks')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Profit')
    plt.legend()
    plt.show()

users = [Participant(i, random.choice([True, False])) for i in range(NUM_USERS)]
builders = [Builder(i, random.choice([True, False])) for i in range(NUM_BUILDERS)]
validators = [Validator(i, random.choice([True, False])) for i in range(NUM_VALIDATORS)]
proposers = [Proposer(i) for i in range(NUM_PROPOSERS)]


mev_included_pbs = run_pbs(builders, proposers, NUM_BLOCKS)
mev_included_pos = run_pos(validators, NUM_BLOCKS)

print(f"MEV transactions included in final blocks (PBS): {mev_included_pbs}")
print(f"MEV transactions included in final blocks (PoS): {mev_included_pos}")

plot_cumulative_mev(mev_included_pbs, mev_included_pos)
plot_profit_distribution(builder_profits, validator_profits, NUM_BLOCKS)