import sys
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import random
import pandas as pd
import numpy as np

# Add project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

# Parameters
NUM_USERS = 20
NUM_BUILDERS = 50
NUM_VALIDATORS = 50
BLOCK_CAPACITY = 50
NUM_BLOCKS = 50
MEV_BUILDER_COUNTS = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
NUM_RUNS = 50

transaction_counter = 1

class Transaction:
    def __init__(self, fee, mev_potential, creator_id=None, targeting=False, target_tx_id=None, block_created=None, transaction_type="normal"):
        global transaction_counter
        self.id = transaction_counter
        transaction_counter += 1
        self.fee = fee
        self.mev_potential = mev_potential
        self.creator_id = creator_id
        self.included_pbs = False
        self.included_pos = False
        self.pbs_inclusion_time = None
        self.pos_inclusion_time = None
        self.successful_pbs = False
        self.successful_pos = False
        self.targeting = targeting
        self.target_tx_id = target_tx_id
        self.block_created = block_created
        self.transaction_type = transaction_type
        self.inclusion_log = []

    def log_inclusion(self, system, block_number, success=False):
        if system == 'pbs':
            self.included_pbs = True
            self.pbs_inclusion_time = block_number
            self.successful_pbs = success
        elif system == 'pos':
            self.included_pos = True
            self.pos_inclusion_time = block_number
            self.successful_pos = success

        self.inclusion_log.append({
            'system': system,
            'block_number': block_number,
            'success': success
        })

user_counter = 1
builder_counter = 1
validator_counter = 1

class Participant:
    def __init__(self, id):
        self.id = id
        self.mempool_pbs = []
        self.mempool_pos = []

    def create_transaction(self, all_participants, is_mev=False, block_number=None):
        fee = random.choice(SAMPLE_GAS_FEES)
        mev_potential = random.choice(MEV_POTENTIALS) if is_mev else 0
        tx = Transaction(fee, mev_potential, self.id, block_created=block_number)
        self.broadcast_transaction(all_participants, tx)
        return tx

    def broadcast_transaction(self, all_participants, tx):
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

    def create_transaction(self, all_participants, target_tx=None, block_number=None):
        if target_tx and target_tx.mev_potential > 0 and target_tx.id not in targeting_tracker:
            fee = target_tx.fee + 100000  # User must pay a fee 100,000 higher than the target
            mev_potential = target_tx.mev_potential
            tx = Transaction(fee, mev_potential, self.id, targeting=True, target_tx_id=target_tx.id, block_created=block_number, transaction_type="b_attack")
            self.broadcast_transaction(all_participants, tx)
            return tx
        else:
            fee = random.choice(SAMPLE_GAS_FEES)
            mev_potential = random.choice(MEV_POTENTIALS)
            tx = Transaction(fee, mev_potential, self.id, block_created=block_number)
            self.broadcast_transaction(all_participants, tx)
            return tx

class Builder(Participant):
    def __init__(self, is_attack):
        global builder_counter
        super().__init__(builder_counter)
        self.is_attack = is_attack
        builder_counter += 1

    def bid(self, block_bid_his, block_number):
        block_value = sum(tx.fee + tx.mev_potential for tx in self.mempool_pbs if not tx.included_pbs and tx.block_created <= block_number)
        
        if block_value == 0:
            return 0
        
        avg_percentage = 0.5  # Let's assume 50% of block value as the bid
        bid = avg_percentage * block_value
        
        if self.is_attack:
            bid = max(0, bid * 1.1)
        
        return bid

    def select_transactions(self, block_number):
        selected_transactions = [tx for tx in self.mempool_pbs if tx.targeting and not tx.included_pbs and tx.block_created <= block_number]
        
        # Builder can add their own attack transactions with fee = 0
        if self.is_attack:
            for tx in selected_transactions:
                if not any(tx.id == t.target_tx_id for t in selected_transactions if t != tx):
                    builder_attack_tx = Transaction(0, 0, self.id, targeting=True, target_tx_id=tx.id, block_created=block_number, transaction_type="b_attack")
                    selected_transactions.append(builder_attack_tx)

        return selected_transactions[:BLOCK_CAPACITY]

class Validator(Participant):
    def __init__(self, is_attack):
        global validator_counter
        super().__init__(validator_counter)
        self.is_attack = is_attack
        validator_counter += 1

    def select_transactions(self, block_number):
        selected_transactions = [tx for tx in self.mempool_pos if tx.targeting and not tx.included_pos and tx.block_created <= block_number]
        
        # Validator can add their own attack transactions with fee = 0
        if self.is_attack:
            for tx in selected_transactions:
                if not any(tx.id == t.target_tx_id for t in selected_transactions if t != tx):
                    validator_attack_tx = Transaction(0, 0, self.id, targeting=True, target_tx_id=tx.id, block_created=block_number, transaction_type="b_attack")
                    selected_transactions.append(validator_attack_tx)

        return selected_transactions[:BLOCK_CAPACITY]

def evaluate_user_initiated_attacks(selected_transactions):
    for tx in selected_transactions:
        if tx.transaction_type == "b_attack" and tx.target_tx_id:
            target_tx = next((t for t in selected_transactions if t.id == tx.target_tx_id), None)
            if not target_tx:
                tx.transaction_type = "failed"
            elif target_tx.creator_id == tx.creator_id:
                tx.transaction_type = "failed"
            elif target_tx.targeting and tx.fee < target_tx.fee:
                tx.transaction_type = "failed"
            elif any(t for t in selected_transactions if t.target_tx_id == tx.target_tx_id and t.fee > tx.fee):
                tx.transaction_type = "failed"
    return selected_transactions

def run_pbs(builders, num_blocks, users):
    cumulative_mev_transactions = [0] * num_blocks
    proposer_profits = {builder.id: [] for builder in builders}
    block_data = []
    transaction_data = []
    all_transactions_log = []

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
        winning_builders = [builder_id for builder_id, bid in block_bid_his[-1].items() if bid == highest_bid]
        winning_builder_id = random.choice(winning_builders)
        winning_builder = next(b for b in builders if b.id == winning_builder_id)

        selected_transactions = winning_builder.select_transactions(block_num + 1)

        selected_transactions = evaluate_user_initiated_attacks(selected_transactions)

        block_value = sum(tx.fee for tx in selected_transactions)
        profit = highest_bid
        proposer_profits[winning_builder_id].append(proposer_profits[winning_builder_id][-1] + profit if proposer_profits[winning_builder_id] else profit)

        mev_transactions_in_block = sum(1 for tx in selected_transactions if tx.mev_potential > 0)
        cumulative_mev_transactions[block_num] = cumulative_mev_transactions[block_num - 1] + mev_transactions_in_block if block_num > 0 else mev_transactions_in_block

        builder_type = 'attack' if winning_builder.is_attack else 'normal'
        
        block_data.append({
            'block_id': block_num + 1,
            'total_gas': block_value,
            'total_mev_captured': sum(tx.mev_potential for tx in selected_transactions if tx.mev_potential > 0),
            'block_bid': highest_bid,
            'builder_type': builder_type,
            'builder_id': winning_builder_id
        })

        included_tx_ids = set()
        for tx in selected_transactions:
            success = False
            if tx.target_tx_id and tx.target_tx_id in targeting_tracker:
                tx.fee = 0
                tx.mev_potential = 0
                tx.transaction_type = "failed"
            else:
                targeting_tracker[tx.target_tx_id] = tx.id if tx.target_tx_id else None
                success = True

            tx.log_inclusion('pbs', block_num + 1, success)

            included_tx_ids.add(tx.id)

            if 0 <= tx.creator_id - 1 < len(users):
                user_type = 'attack' if isinstance(users[tx.creator_id - 1], AttackUser) else 'normal'
            else:
                user_type = 'unknown'

            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': tx.mev_potential,
                'mev_captured': tx.fee if tx.mev_potential > 0 and tx.targeting else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.target_tx_id,
                'type_of_user': user_type,
                'block_number': block_num + 1,
                'block_created': tx.block_created,
                'builder_type': builder_type,
                'transaction_type': tx.transaction_type
            })

            all_transactions_log.append(tx)

        for builder in builders:
            builder.mempool_pbs = [tx for tx in builder.mempool_pbs if tx.id not in included_tx_ids]

    proposer_final_profits = {k: v[-1] for k, v in proposer_profits.items() if v}

    return cumulative_mev_transactions, proposer_final_profits, block_data, transaction_data, all_transactions_log

def run_pos(validators, num_blocks, users):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators}
    total_mev_transactions = 0
    block_data = []
    transaction_data = []
    all_transactions_log = []

    global targeting_tracker
    targeting_tracker = {}

    for block_num in range(num_blocks):
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions(block_num + 1)

        selected_transactions = evaluate_user_initiated_attacks(selected_transactions)

        mev_transactions_in_block = sum(tx.mev_potential > 0 for tx in selected_transactions)
        profit_from_block = sum(tx.fee for tx in selected_transactions)
        validator_profits[validator.id] += profit_from_block

        total_mev_transactions += mev_transactions_in_block
        cumulative_mev_transactions.append(total_mev_transactions)

        validator_type = 'attack' if validator.is_attack else 'normal'
        
        block_data.append({
            'block_id': block_num + 1,
            'total_gas': profit_from_block,
            'total_mev_captured': sum(tx.mev_potential for tx in selected_transactions if tx.mev_potential > 0),
            'validator_type': validator_type,
            'validator_id': validator.id 
        })

        included_tx_ids = set()
        for tx in selected_transactions:
            success = False
            if tx.target_tx_id and tx.target_tx_id in targeting_tracker:
                tx.fee = 0
                tx.mev_potential = 0
                tx.transaction_type = "failed"
            else:
                targeting_tracker[tx.target_tx_id] = tx.id if tx.target_tx_id else None
                success = True

            tx.log_inclusion('pos', block_num + 1, success)

            included_tx_ids.add(tx.id)

            if 0 <= tx.creator_id - 1 < len(users):
                user_type = 'attack' if isinstance(users[tx.creator_id - 1], AttackUser) else 'normal'
            else:
                user_type = 'unknown'

            transaction_data.append({
                'transaction_id': tx.id,
                'fee': tx.fee,
                'mev_potential': tx.mev_potential,
                'mev_captured': tx.fee if tx.mev_potential > 0 and tx.targeting else 0,
                'creator_id': tx.creator_id,
                'target_tx_id': tx.target_tx_id,
                'type_of_user': user_type,
                'block_number': block_num + 1,
                'block_created': tx.block_created,
                'validator_type': validator_type,
                'transaction_type': tx.transaction_type
            })

            all_transactions_log.append(tx)

        for validator in validators:
            validator.mempool_pos = [tx for tx in validator.mempool_pos if tx.id not in included_tx_ids]

    return cumulative_mev_transactions, validator_profits, block_data, transaction_data, all_transactions_log

def run_simulation(run_id, mev_count, is_attack_all=False, is_attack_none=False, is_attack_50_percent=False):
    if is_attack_all:
        users = [AttackUser() for i in range(NUM_USERS)]
        output_dir = 'data/100run_attackall'
    elif is_attack_none:
        users = [NormalUser() for i in range(NUM_USERS)]
        output_dir = 'data/100run_attacknon'
    elif is_attack_50_percent:
        users = [NormalUser() if i < NUM_USERS // 2 else AttackUser() for i in range(NUM_USERS)]
        output_dir = 'data/100_runs'
    else:
        return

    builders = [Builder(i < mev_count) for i in range(NUM_BUILDERS)]
    validators = [Validator(i < mev_count) for i in range(NUM_VALIDATORS)]

    all_participants = users + builders + validators

    global targeting_tracker
    targeting_tracker = {}

    for block_number in range(NUM_BLOCKS):
        for counter in range(24):
            user = random.choice(users)

            if isinstance(user, AttackUser):
                target_tx_pbs = max(
                    (tx for tx in user.mempool_pbs if tx.mev_potential > 0 and not tx.included_pbs and tx.id not in targeting_tracker),
                    default=None,
                    key=lambda tx: tx.fee
                )
                target_tx_pos = max(
                    (tx for tx in user.mempool_pos if tx.mev_potential > 0 and not tx.included_pos and tx.id not in targeting_tracker),
                    default=None,
                    key=lambda tx: tx.fee
                )
                
                if target_tx_pbs:
                    user.create_transaction(all_participants, target_tx_pbs, block_number=block_number + 1)
                else:
                    user.create_transaction(all_participants, block_number=block_number + 1)

                if target_tx_pos:
                    user.create_transaction(all_participants, target_tx_pos, block_number=block_number + 1)
                else:
                    user.create_transaction(all_participants, block_number=block_number + 1)
            else:
                user.create_transaction(all_participants, is_mev=random.choice([True, False]), block_number=block_number + 1)

    cumulative_mev_included_pbs, proposer_profits, block_data_pbs, transaction_data_pbs, all_transactions_pbs = run_pbs(builders, NUM_BLOCKS, users)
    cumulative_mev_included_pos, validator_profits, block_data_pos, transaction_data_pos, all_transactions_pos = run_pos(validators, NUM_BLOCKS, users)

    all_transactions_log = all_transactions_pbs + all_transactions_pos

    run_output_dir = f'{output_dir}/run{run_id}/mev{mev_count}'
    pbs_output_dir = os.path.join(run_output_dir, 'pbs')
    pos_output_dir = os.path.join(run_output_dir, 'pos')
    all_tx_output_dir = os.path.join(run_output_dir, 'all_transactions')
    os.makedirs(pbs_output_dir, exist_ok=True)
    os.makedirs(pos_output_dir, exist_ok=True)
    os.makedirs(all_tx_output_dir, exist_ok=True)

    block_data_pbs_df = pd.DataFrame(block_data_pbs)
    transaction_data_pbs_df = pd.DataFrame(transaction_data_pbs)
    block_data_pbs_df.to_csv(os.path.join(pbs_output_dir, 'block_data_pbs.csv'), index=False)
    transaction_data_pbs_df.to_csv(os.path.join(pbs_output_dir, 'transaction_data_pbs.csv'), index=False)

    block_data_pos_df = pd.DataFrame(block_data_pos)
    transaction_data_pos_df = pd.DataFrame(transaction_data_pos)
    block_data_pos_df.to_csv(os.path.join(pos_output_dir, 'block_data_pos.csv'), index=False)
    transaction_data_pos_df.to_csv(os.path.join(pos_output_dir, 'transaction_data_pos.csv'), index=False)

    all_transactions_df = pd.DataFrame([vars(tx) for tx in all_transactions_log])
    all_transactions_df.to_csv(os.path.join(all_tx_output_dir, 'all_transactions.csv'), index=False)

if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        futures = []
        for run_id in range(1, NUM_RUNS + 1):
            for mev_count in MEV_BUILDER_COUNTS:
                futures.append(executor.submit(run_simulation, run_id, mev_count, is_attack_50_percent=True))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")
