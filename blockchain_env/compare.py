import random
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

random.seed(42)

NUM_USERS = 20
NUM_BUILDERS = 20
NUM_VALIDATORS = 20
BLOCK_CAPACITY = 10
NUM_TRANSACTIONS_PER_BLOCK = 20
NUM_BLOCKS = 100


transaction_counter = 1

class Transaction:
    def __init__(self, fee, is_mev, creator_id=None, targeting=False, target_tx_id=None, block_created=None):
        global transaction_counter
        self.id = transaction_counter
        transaction_counter += 1
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id
        self.included = False
        self.targeting = targeting
        self.target_tx_id = target_tx_id
        self.block_created = block_created

user_counter = 1
builder_counter = 1
validator_counter = 1

class Participant:
    def __init__(self, id):
        self.id = id
        self.mempool_pbs = []
        self.mempool_pos = []

    def create_transaction(self, is_mev=False, block_number=None):
        fee = random.choice(SAMPLE_GAS_FEES)
        if is_mev:
            fee = random.choice(MEV_POTENTIALS)
        tx = Transaction(fee, is_mev, self.id, block_created=block_number)
        self.broadcast_transaction(tx)
        return tx

    def broadcast_transaction(self, tx):
        for participant in all_participants:
            participant.mempool_pbs.append(tx)
            participant.mempool_pos.append(tx)

class NormalUser(Participant):
    def __init__(self):
        global user_counter
        super().__init__(user_counter)
        user_counter += 1

class AttackUser(Participant):
    def __init__(self):
        global user_counter
        super().__init__(user_counter)
        user_counter += 1

    def create_transaction(self, target_tx=None, block_number=None):
        global targeting_tracker
        if target_tx and target_tx.is_mev and target_tx.id not in targeting_tracker:
            fee = target_tx.fee + 1
            tx = Transaction(fee, False, self.id, targeting=True, target_tx_id=target_tx.id, block_created=block_number)
            self.broadcast_transaction(tx)
            return tx
        else:
            fee = random.choice(SAMPLE_GAS_FEES)
            tx = Transaction(fee, False, self.id, block_created=block_number)
            self.broadcast_transaction(tx)
            return tx

class Builder(Participant):
    def __init__(self, is_attack):
        global builder_counter
        super().__init__(builder_counter)
        self.is_attack = is_attack
        builder_counter += 1
        self.average_bid_percentage = 0.5  # Initial average bid percentage set to 50%

    def bid(self, block_bid_his, block_number):
        block_value = sum(tx.fee + (tx.fee if tx.is_mev else 0) for tx in self.mempool_pbs if not tx.included and tx.block_created <= block_number)
        
        if block_bid_his:
            # Calculate the average bid percentage from the last block bids
            avg_percentage = np.mean([bid / block_value for round_bids in block_bid_his for bid in round_bids.values() if bid <= block_value])
            self.average_bid_percentage = avg_percentage
        
        initial_bid = self.average_bid_percentage * block_value
        
        # Attack builders bid slightly more aggressively
        if self.is_attack:
            bid = min(max(0, initial_bid * 1.1), block_value)
        else:
            bid = min(max(0, initial_bid), block_value)
        
        return bid

    def select_transactions(self, block_number):
        return select_transactions_common(self, block_number, self.mempool_pbs)

class Validator(Participant):
    def __init__(self, is_attack):
        global validator_counter
        super().__init__(validator_counter)
        self.is_attack = is_attack
        validator_counter += 1

    def select_transactions(self, block_number):
        return select_transactions_common(self, block_number, self.mempool_pos)

def select_transactions_common(participant, block_number, mempool):
    available_transactions = [tx for tx in mempool if not tx.included and tx.block_created <= block_number]
    selected_transactions = []

    if participant.is_attack:
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        targeted_tx_ids = set()  # To keep track of already targeted transactions
        for tx in available_transactions:
            if len(selected_transactions) >= BLOCK_CAPACITY:
                break
            if tx.id in targeted_tx_ids:
                continue  # Skip if this transaction has already been targeted
            selected_transactions.append(tx)
            if tx.is_mev:
                if tx.id not in targeting_tracker:
                    targeting_tracker[tx.id] = True
                    targeted_tx_ids.add(tx.id)
                    attack_tx = Transaction(0, False, participant.id, targeting=True, target_tx_id=tx.id, block_created=tx.block_created)
                    selected_transactions.append(attack_tx)
    else:
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]

    for tx in selected_transactions:
        tx.included = True

    return selected_transactions

def run_pbs(builders, num_blocks):
    cumulative_mev_transactions = [0] * num_blocks
    proposer_profits = {builder.id: [] for builder in builders}
    block_data = []
    transaction_data = []

    global targeting_tracker
    targeting_tracker = {}

    for block_num in range(num_blocks):
        block_bid_his = []

        for counter in range(24):
            counter_bids = {}
            for builder in builders:
                bid = builder.bid(block_bid_his, block_num + 1)
                counter_bids[builder.id] = bid
            block_bid_his.append(counter_bids)

        highest_bid = max(block_bid_his[-1].values())
        winning_builder_id = max(block_bid_his[-1], key=block_bid_his[-1].get)
        winning_builder = next(b for b in builders if b.id == winning_builder_id)

        selected_transactions = winning_builder.select_transactions(block_num + 1)

        block_value = sum(tx.fee for tx in selected_transactions)
        profit = highest_bid  # Proposer's profit is the winning bid
        proposer_profits[winning_builder_id].append(proposer_profits[winning_builder_id][-1] + profit if proposer_profits[winning_builder_id] else profit)

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
            if tx.target_tx_id and tx.target_tx_id in targeting_tracker:
                tx.fee = 0  # Mark as failed attack
            else:
                targeting_tracker[tx.target_tx_id] = tx.id if tx.target_tx_id else None

            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': max(MEV_POTENTIALS) if tx.is_mev else 0,
                'mev_captured': tx.fee if tx.is_mev and tx.targeting else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.target_tx_id,
                'type_of_user': 'attack' if isinstance(users[tx.creator_id - 1], AttackUser) else 'normal',
                'block_number': block_num + 1,
                'block_created': tx.block_created
            })

        # Remove included transactions from mempool
        for builder in builders:
            builder.mempool_pbs = [tx for tx in builder.mempool_pbs if not tx.included]

    proposer_final_profits = {k: v[-1] for k, v in proposer_profits.items() if v}

    return cumulative_mev_transactions, proposer_final_profits, block_data, transaction_data

def run_pos(validators, num_blocks):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators}
    total_mev_transactions = 0
    block_data = []
    transaction_data = []

    global targeting_tracker
    targeting_tracker = {}

    for block_num in range(num_blocks):
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions(block_num + 1)

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
            'validator_type': 'attack' if validator.is_attack else 'normal'
        })

        for tx in selected_transactions:
            if tx.target_tx_id and tx.target_tx_id in targeting_tracker:
                tx.fee = 0  # Mark as failed attack
            else:
                targeting_tracker[tx.target_tx_id] = tx.id if tx.target_tx_id else None

            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': max(MEV_POTENTIALS) if tx.is_mev else 0,
                'mev_captured': tx.fee if tx.is_mev and tx.targeting else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.target_tx_id,
                'type_of_user': 'attack' if isinstance(users[tx.creator_id - 1], AttackUser) else 'normal',
                'block_number': block_num + 1,
                'block_created': tx.block_created
            })

        # Remove included transactions from mempool
        for validator in validators:
            validator.mempool_pos = [tx for tx in validator.mempool_pos if not tx.included]

    return cumulative_mev_transactions, validator_profits, block_data, transaction_data

if __name__ == "__main__":
    users = [NormalUser() if i < NUM_USERS // 2 else AttackUser() for i in range(NUM_USERS)]
    builders = [Builder(i >= NUM_BUILDERS // 2) for i in range(NUM_BUILDERS)]
    validators = [Validator(i >= NUM_VALIDATORS // 2) for i in range(NUM_VALIDATORS)]

    all_participants = users + builders + validators

    global targeting_tracker
    targeting_tracker = {}

    for block_number in range(NUM_BLOCKS):
        for counter in range(24):
            attack_user = random.choice([u for u in users if isinstance(u, AttackUser)])
            normal_user = random.choice([u for u in users if isinstance(u, NormalUser)])

            # Attack user creates transaction
            target_tx_pbs = max(
                (tx for tx in attack_user.mempool_pbs if tx.is_mev and not tx.included and tx.id not in targeting_tracker),
                default=None,
                key=lambda tx: tx.fee
            )
            target_tx_pos = max(
                (tx for tx in attack_user.mempool_pos if tx.is_mev and not tx.included and tx.id not in targeting_tracker),
                default=None,
                key=lambda tx: tx.fee
            )
            attack_user.create_transaction(target_tx_pbs, block_number=block_number + 1)
            attack_user.create_transaction(target_tx_pos, block_number=block_number + 1)

            # Normal user creates transaction
            normal_user.create_transaction(is_mev=random.choice([True, False]), block_number=block_number + 1)

    cumulative_mev_included_pbs, proposer_profits, block_data_pbs, transaction_data_pbs = run_pbs(builders, NUM_BLOCKS)
    cumulative_mev_included_pos, validator_profits, block_data_pos, transaction_data_pos = run_pos(validators, NUM_BLOCKS)

    os.makedirs('data', exist_ok=True)

    block_data_pbs_df = pd.DataFrame(block_data_pbs)
    block_data_pos_df = pd.DataFrame(block_data_pos)
    transaction_data_pbs_df = pd.DataFrame(transaction_data_pbs)
    transaction_data_pos_df = pd.DataFrame(transaction_data_pos)

    block_data_pbs_df.to_csv('data/block_data_pbs.csv', index=False)
    block_data_pos_df.to_csv('data/block_data_pos.csv', index=False)
    transaction_data_pbs_df.to_csv('data/transaction_data_pbs.csv', index=False)
    transaction_data_pos_df.to_csv('data/transaction_data_pos.csv', index=False)
