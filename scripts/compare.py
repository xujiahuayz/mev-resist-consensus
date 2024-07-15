import random
import numpy as np
import matplotlib.pyplot as plt
import uuid
import seaborn as sns
import pandas as pd
import os

random.seed(42)

NUM_USERS = 100
NUM_BUILDERS = 20
NUM_VALIDATORS = 20
BLOCK_CAPACITY = 50
NUM_TRANSACTIONS = 100
NUM_BLOCKS = 100

FIXED_GAS_FEES = [0.05, 0.1]
MEV_POTENTIALS = [0.15, 0.2]

class Transaction:
    def __init__(self, fee, is_mev, creator_id=None, targeted=False):
        # all transactions should have a unique id, a potential mev, a gas fee, a creator, and when created. Indicator should be set for included or not in a block, targeted or not.
        self.id = str(uuid.uuid4())
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id
        self.included = False
        self.targeted = targeted

class Participant:
    def __init__(self, id):
        # all participants should have a unique id and a pool of mempool with transactions
        self.id = id
        self.mempool = []

    def create_transaction(self, is_mev=False):
        # each participant can create a transaction with a gas fee of their choice and a mev potential that fits into some distribution
        # this transaction is broadcasted to the network to participants' mempool
        fee = random.choice(FIXED_GAS_FEES)
        if is_mev:
            fee = random.choice(MEV_POTENTIALS)
        tx = Transaction(fee, is_mev, self.id)
        self.broadcast_transaction(tx)
        return tx

    def broadcast_transaction(self, tx):
        for participant in all_participants:
            participant.mempool.append(tx)

class NormalUser(Participant):
    pass  # No need to redefine create_transaction as it inherits from Participant

class AttackUser(Participant):
    def create_transaction(self, target_tx=None):
        if target_tx and target_tx.is_mev:
            fee = target_tx.fee + 0.01
            tx = Transaction(fee, False, self.id, targeted=True)
            self.broadcast_transaction(tx)
            return tx
        else:
            fee = random.choice(FIXED_GAS_FEES)
            tx = Transaction(fee, False, self.id)
            self.broadcast_transaction(tx)
            return tx

class Builder(Participant):
    def __init__(self, id, is_attack):
        super().__init__(id)
        self.is_attack = is_attack

    def bid(self, block_bid_his):
        block_value = sum(tx.fee for tx in self.mempool if not tx.included)
        if block_bid_his:
            last_bid = max(block_bid_his[-1].values())
            new_bid = np.random.normal(last_bid, last_bid * 0.5)
            return min(new_bid, block_value)
        else:
            return block_value * 0.5

    def select_transactions(self):
        available_transactions = [tx for tx in self.mempool if not tx.included]
        if self.is_attack:
            mev_transactions = [tx for tx in available_transactions if tx.is_mev]
            for tx in mev_transactions:
                front_run_tx = Transaction(tx.fee + 0.01, False, self.id, targeted=True)
                self.broadcast_transaction(front_run_tx)
        
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]
        
        for tx in selected_transactions:
            tx.included = True
        
        return selected_transactions

class Validator(Participant):
    def select_transactions(self):
        available_transactions = [tx for tx in self.mempool if not tx.included]
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]
        
        for tx in selected_transactions:
            tx.included = True
        
        return selected_transactions

def run_pbs(builders, num_blocks):
    cumulative_mev_transactions = [0] * num_blocks
    builder_profits = {builder.id: [] for builder in builders}
    block_data = []
    transaction_data = []
    
    for block_num in range(num_blocks):
        print(f"Running PBS for Block {block_num + 1}")
        block_bid_his = []

        for counter in range(24):
            counter_bids = {}
            for builder in builders:
                bid = builder.bid(block_bid_his)
                counter_bids[builder.id] = bid
            block_bid_his.append(counter_bids)
        
        highest_bid = max(block_bid_his[-1].values())
        winning_builder_id = max(block_bid_his[-1], key=block_bid_his[-1].get)
        winning_builder = builders[winning_builder_id]
        
        selected_transactions = winning_builder.select_transactions()
        block_value = sum(tx.fee for tx in selected_transactions)
        profit = block_value - highest_bid
        builder_profits[winning_builder_id].append(builder_profits[winning_builder_id][-1] + profit if builder_profits[winning_builder_id] else profit)
        
        mev_transactions_in_block = sum(1 for tx in selected_transactions if tx.is_mev)
        cumulative_mev_transactions[block_num] = cumulative_mev_transactions[block_num - 1] + mev_transactions_in_block if block_num > 0 else mev_transactions_in_block
        
        block_data.append({
            'block_id': block_num + 1,
            'total_gas': block_value,
            'total_mev_captured': mev_transactions_in_block * max(MEV_POTENTIALS),
            'block_bid': highest_bid,
            'builder_type': 'attack' if winning_builder.is_attack else 'normal'
        })

        for tx in selected_transactions:
            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': max(MEV_POTENTIALS) if tx.is_mev else 0,
                'mev_captured': tx.fee if tx.is_mev and tx.targeted else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.id if tx.targeted else None,
                'type_of_user': 'attack' if isinstance(users[tx.creator_id], AttackUser) else 'normal',
                'block_number': block_num + 1
            })

    builder_final_profits = {k: v[-1] for k, v in builder_profits.items() if v}
    
    return cumulative_mev_transactions, builder_final_profits, block_data, transaction_data

def run_pos(validators, num_blocks):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators}
    total_mev_transactions = 0
    block_data = []
    transaction_data = []
    
    for block_num in range(num_blocks):
        print(f"Running PoS for Block {block_num + 1}")
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions()
        mev_transactions_in_block = sum(tx.is_mev for tx in selected_transactions)
        profit_from_block = sum(tx.fee for tx in selected_transactions)
        validator_profits[validator.id] += profit_from_block
        
        total_mev_transactions += mev_transactions_in_block
        cumulative_mev_transactions.append(total_mev_transactions)

        block_data.append({
            'block_id': block_num + 1,
            'total_gas': profit_from_block,
            'total_mev_captured': mev_transactions_in_block * max(MEV_POTENTIALS),
            'block_bid': None,
            'builder_type': 'validator'
        })
    
        for tx in selected_transactions:
            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': max(MEV_POTENTIALS) if tx.is_mev else 0,
                'mev_captured': tx.fee if tx.is_mev and tx.targeted else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.id if tx.targeted else None,
                'type_of_user': 'attack' if isinstance(users[tx.creator_id], AttackUser) else 'normal',
                'block_number': block_num + 1
            })
    
        print(f"Block {block_num + 1}:")
        print(f"Total MEV Transactions in Block: {mev_transactions_in_block}")
        print("Transactions in Winning Block:")
        for tx in selected_transactions:
            print(f"  - TX ID: {tx.id}, Fee: {tx.fee}, MEV: {tx.is_mev}")

    return cumulative_mev_transactions, validator_profits, block_data, transaction_data

def plot_cumulative_mev(cumulative_mev_pbs, cumulative_mev_pos):
    plt.figure(figsize=(10, 6))
    sns.lineplot(x=range(NUM_BLOCKS), y=cumulative_mev_pbs, label='PBS')
    sns.lineplot(x=range(NUM_BLOCKS), y=cumulative_mev_pos, label='PoS')
    plt.title('Cumulative MEV Transactions Included Over Blocks')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Number of MEV Transactions Included')
    plt.legend()
    plt.show()

def plot_ranked_profit_distribution(builder_profits, validator_profits):
    if not builder_profits or not validator_profits:
        print("No transactions to plot.")
        return
    
    sorted_builder_profits = sorted(builder_profits.items(), key=lambda x: x[1], reverse=True)
    sorted_validator_profits = sorted(validator_profits.items(), key=lambda x: x[1], reverse=True)
    
    builder_ids, builder_profits = zip(*sorted_builder_profits)
    validator_ids, validator_profits = zip(*sorted_validator_profits)
    
    # Adjust lengths to be the same by padding with zeros
    max_length = max(len(builder_profits), len(validator_profits))
    builder_profits = list(builder_profits) + [0] * (max_length - len(builder_profits))
    validator_profits = list(validator_profits) + [0] * (max_length - len(validator_profits))
    
    index = np.arange(max_length)
    bar_width = 0.35
    
    plt.figure(figsize=(12, 8))
    
    sns.barplot(x=index, y=builder_profits, color='b', alpha=0.6, label='Builders')
    sns.barplot(x=index + bar_width, y=validator_profits, color='g', alpha=0.6, label='Validators')
    
    plt.xlabel('Rank')
    plt.ylabel('Cumulative Profit')
    plt.title('Ranked Cumulative Profit of Builders and Validators')
    plt.xticks(index + bar_width / 2, index)
    plt.legend()
    
    plt.tight_layout()
    plt.show()

def plot_mev_transactions_comparison(total_mev_created, cumulative_mev_included_pbs, cumulative_mev_included_pos):
    plt.figure(figsize=(10, 6))
    
    x_axis = list(range(1, NUM_BLOCKS + 1))
    y_mev_created = [total_mev_created] * NUM_BLOCKS  
    
    sns.lineplot(x=x_axis, y=y_mev_created, label='Total MEV Created', linestyle='--', color='blue')
    sns.lineplot(x=x_axis, y=cumulative_mev_included_pbs, label='MEV Included in PBS', color='red')
    sns.lineplot(x=x_axis, y=cumulative_mev_included_pos, label='MEV Included in PoS', color='green')
    
    plt.title('MEV Transactions: Created vs Included')
    plt.xlabel('Block Number')
    plt.ylabel('Number of MEV Transactions')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    users = [NormalUser(i) if random.random() > 0.1 else AttackUser(i) for i in range(NUM_USERS)]
    builders = [Builder(i, random.random() > 0.5) for i in range(NUM_BUILDERS)]
    validators = [Validator(i) for i in range(NUM_VALIDATORS)]

    # Collect all participants in a global list
    all_participants = users + builders + validators

    for user in users:
        for _ in range(NUM_TRANSACTIONS // NUM_USERS):
            if isinstance(user, AttackUser):
                target_tx = next((tx for tx in user.mempool if tx.is_mev), None)
                user.create_transaction(target_tx)
            else:
                user.create_transaction()

    # Debugging to check the number of transactions created by each user 
    for user in users:
        print(f"User {user.id} created {len(user.mempool)} transactions")

    total_mev_created = sum(1 for user in users for tx in user.mempool if tx.is_mev)
    print(f"Total MEV Created: {total_mev_created}")

    cumulative_mev_included_pbs, builder_profits, block_data_pbs, transaction_data_pbs = run_pbs(builders, NUM_BLOCKS)
    cumulative_mev_included_pos, validator_profits, block_data_pos, transaction_data_pos = run_pos(validators, NUM_BLOCKS)

    plot_cumulative_mev(cumulative_mev_included_pbs, cumulative_mev_included_pos)
    plot_ranked_profit_distribution(builder_profits, validator_profits)
    plot_mev_transactions_comparison(total_mev_created, cumulative_mev_included_pbs, cumulative_mev_included_pos)

    os.makedirs('data', exist_ok=True)
    
    block_data_pbs_df = pd.DataFrame(block_data_pbs)
    block_data_pos_df = pd.DataFrame(block_data_pos)
    transaction_data_pbs_df = pd.DataFrame(transaction_data_pbs)
    transaction_data_pos_df = pd.DataFrame(transaction_data_pos)

    block_data_pbs_df.to_csv('data/block_data_pbs.csv', index=False)
    block_data_pos_df.to_csv('data/block_data_pos.csv', index=False)
    transaction_data_pbs_df.to_csv('data/transaction_data_pbs.csv', index=False)
    transaction_data_pos_df.to_csv('data/transaction_data_pos.csv', index=False)
