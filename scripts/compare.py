import random
import numpy as np
import matplotlib.pyplot as plt
import uuid

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
    def __init__(self, id, fee, is_mev, creator_id=None, targeted=False):
        self.id = uuid.uuid4()
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id
        self.targeted = targeted
        self.included = False

class Participant:
    def __init__(self, id, is_mev):
        self.id = id
        self.is_mev = is_mev
        self.mev_transaction = None
        self.transactions = []
        self.total_profit = 0
        self.mev_transactions_created = 0
        if self.is_mev:
            self.mev_transaction = self.create_transaction(True)

    def create_transaction(self, is_mev):
        if is_mev:
            fee = random.triangular(MEV_FEE_MIN, MEV_FEE_MAX, MEV_FEE_MAX * 0.75)
            self.mev_transactions_created += 1
        else:
            fee = random.uniform(NON_MEV_FEE_MIN, NON_MEV_FEE_MAX)
        tx = Transaction(fee, is_mev, self.id)
        self.transactions.append(tx)
        return tx
    
    def receive_transaction(self, transaction):
        self.transactions.append(transaction)

    def select_transactions(self):
        # Filter out transactions that have already been included
        available_transactions = [tx for tx in self.transactions if not tx.included]
        
        # If MEV-oriented, ensure the builder's MEV transaction is considered first
        if self.mev_transaction and not self.mev_transaction.included:
            available_transactions = [self.mev_transaction] + available_transactions
        
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]
        
        # Mark selected transactions as included
        for tx in selected_transactions:
            tx.included = True
        
        return selected_transactions

class NormalUser(Participant):
    def __init__(self, id):
        super().__init__(id, False)
    
    def create_transaction(self, is_mev=False):
        fee = np.random.normal(loc=0.1, scale=0.05)
        fee = max(min(fee, NON_MEV_FEE_MAX), NON_MEV_FEE_MIN)
        tx = Transaction(uuid.uuid4(), fee, is_mev, self.id)
        self.transactions.append(tx)
        return tx

class AttackUser(Participant):
    def __init__(self, id):
        super().__init__(id, False)
    
    def create_transaction(self, target_tx=None):
        if target_tx and target_tx.is_mev:
            fee = target_tx.fee + 0.01  # front-running strategy
            tx = Transaction(uuid.uuid4(), fee, False, self.id, targeted=True)
            self.transactions.append(tx)
            return tx
        else:
            fee = np.random.normal(loc=0.1, scale=0.05)
            fee = max(min(fee, NON_MEV_FEE_MAX), NON_MEV_FEE_MIN)
            tx = Transaction(uuid.uuid4(), fee, False, self.id)
            self.transactions.append(tx)
            return tx

class NormalBuilder(Participant):
    def __init__(self, id, reactivity):
        super().__init__(id, False)
        self.reactivity = reactivity 
    
    def bid(self, block_bid_his):
        block_value = sum(tx.fee for tx in self.transactions)
        if block_bid_his:
            last_bid = max(block_bid_his[-1].values())
            new_bid = np.random.normal(last_bid, last_bid * self.reactivity)
            return min(new_bid, block_value)
        else:
            return block_value * 0.5

class AttackBuilder(Participant):
    def __init__(self, id, reactivity):
        super().__init__(id, True)
        self.reactivity = reactivity 
    
    def bid(self, block_bid_his):
        block_value = sum(tx.fee for tx in self.transactions) + sum(tx.fee for tx in self.transactions if tx.is_mev)
        if block_bid_his:
            last_bid = max(block_bid_his[-1].values())
            new_bid = np.random.normal(last_bid, last_bid * self.reactivity)
            return min(new_bid, block_value)
        else:
            return block_value * 0.5
    
    def select_transactions(self):
        available_transactions = [tx for tx in self.transactions if not tx.included]
        if self.mev_transaction and not self.mev_transaction.included:
            available_transactions = [self.mev_transaction] + available_transactions
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]
        for tx in selected_transactions:
            tx.included = True
        attack_transactions = [tx for tx in available_transactions if tx.targeted]
        selected_transactions.extend(attack_transactions)
        selected_transactions = selected_transactions[:BLOCK_CAPACITY]
        return selected_transactions

class Proposer:
    def __init__(self, id):
        self.id = id
        self.cumulative_reward = 0

class Validator(Participant):
    pass

def run_pbs(builders, proposers, num_blocks):
    cumulative_mev_transactions = [0] * num_blocks
    builder_profits = {builder.id: [] for builder in builders}
    
    for block_num in range(num_blocks):
        block_bid_his = []  # Tracks bid history for the current block

        for counter in range(24): 
            counter_bids = {}
            for builder in builders:
                bid = builder.bid(block_bid_his)
                counter_bids[builder.id] = bid
            block_bid_his.append(counter_bids)
        
        highest_bid = max(block_bid_his[-1].values())
        winning_builder_id = max(block_bid_his[-1], key=block_bid_his[-1].get)
        
        selected_transactions = builders[winning_builder_id].select_transactions()
        block_value = sum(tx.fee for tx in selected_transactions)
        profit = block_value - highest_bid
        builder_profits[winning_builder_id].append(builder_profits[winning_builder_id][-1] + profit if builder_profits[winning_builder_id] else profit)
        
        mev_transactions_in_block = sum(1 for tx in selected_transactions if tx.is_mev)
        cumulative_mev_transactions[block_num] = cumulative_mev_transactions[block_num - 1] + mev_transactions_in_block if block_num > 0 else mev_transactions_in_block

    builder_final_profits = {k: v[-1] for k, v in builder_profits.items() if v}
    
    return cumulative_mev_transactions, builder_final_profits

def run_pos(validators, num_blocks):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators} 
    total_mev_transactions = 0
    
    for block_num in range(num_blocks):
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions()
        mev_transactions_in_block = sum(tx.is_mev for tx in selected_transactions)
        profit_from_block = sum(tx.fee for tx in selected_transactions)
        validator_profits[validator.id] += profit_from_block
        
        total_mev_transactions += mev_transactions_in_block
        cumulative_mev_transactions.append(total_mev_transactions)
    
        # Diagnostic print for each block
        print(f"Block {block_num + 1}:")
        print(f"Total MEV Transactions in Block: {mev_transactions_in_block}")
        print("Transactions in Winning Block:")
        for tx in selected_transactions:
            print(f"  - TX ID: {tx.creator_id}, Fee: {tx.fee}, MEV: {tx.is_mev}")

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

def plot_ranked_profit_distribution(builder_profits, validator_profits):
    sorted_builder_profits = sorted(builder_profits.items(), key=lambda x: x[1], reverse=True)
    sorted_validator_profits = sorted(validator_profits.items(), key=lambda x: x[1], reverse=True)
    
    builder_ids, builder_profits = zip(*sorted_builder_profits)
    validator_ids, validator_profits = zip(*sorted_validator_profits)
    
    index = np.arange(len(builder_profits))
    bar_width = 0.35
    
    plt.figure(figsize=(12, 8))
    
    builder_bars = plt.bar(index, builder_profits, bar_width, label='Builders', color='b', alpha=0.6)
    validator_bars = plt.bar(index + bar_width, validator_profits, bar_width, label='Validators', color='g', alpha=0.6)
    
    plt.xlabel('Rank')
    plt.ylabel('Cumulative Profit')
    plt.title('Ranked Cumulative Profit of Builders and Validators')
    plt.xticks(index + bar_width / 2, [f'B{b_id}/V{v_id}' for b_id, v_id in zip(builder_ids, validator_ids)])
    plt.legend()
    
    plt.tight_layout()
    plt.show()

def plot_mev_transactions_comparison(total_mev_created, cumulative_mev_included_pbs, cumulative_mev_included_pos):
    plt.figure(figsize=(10, 6))
    
    x_axis = list(range(1, NUM_BLOCKS + 1))
    y_mev_created = [total_mev_created] * NUM_BLOCKS  
    
    plt.plot(x_axis, y_mev_created, label='Total MEV Created', linestyle='--', color='blue')
    plt.plot(x_axis, cumulative_mev_included_pbs, label='MEV Included in PBS', color='red')
    plt.plot(x_axis, cumulative_mev_included_pos, label='MEV Included in PoS', color='green')
    
    plt.title('MEV Transactions: Created vs Included')
    plt.xlabel('Block Number')
    plt.ylabel('Number of MEV Transactions')
    plt.legend()
    plt.show()

if __name__ == '__main__':

    users = [NormalUser(i) if random.random() > 0.1 else AttackUser(i) for i in range(NUM_USERS)]
    builders = [NormalBuilder(i, 0.5) if random.random() > 0.1 else AttackBuilder(i, 0.5) for i in range(NUM_BUILDERS)]
    validators = [Validator(i, random.choice([True, False])) for i in range(NUM_VALIDATORS)]
    proposers = [Proposer(i) for i in range(NUM_PROPOSERS)]

    total_mev_created = sum(user.mev_transactions_created for user in users)
    cumulative_mev_included_pbs, builder_profits = run_pbs(builders, proposers, NUM_BLOCKS)
    cumulative_mev_included_pos, validator_profits = run_pos(validators, NUM_BLOCKS)

    plot_cumulative_mev(cumulative_mev_included_pbs, cumulative_mev_included_pos)
    plot_ranked_profit_distribution(builder_profits, validator_profits)
    plot_mev_transactions_comparison(total_mev_created, cumulative_mev_included_pbs, cumulative_mev_included_pos)
