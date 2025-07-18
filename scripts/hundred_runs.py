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
MEV_BUILDER_COUNTS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
NUM_RUNS = 50

TRANSACTION_COUNTER = 1
targeting_tracker = {}  # Global tracking for targeting transactions

class Transaction:
    def __init__(self, fee, mev_potential, creator_id=None, targeting=False, target_tx_id=None, block_created=None, transaction_type="normal"):
        global TRANSACTION_COUNTER
        self.id = TRANSACTION_COUNTER
        TRANSACTION_COUNTER += 1
        self.fee = fee
        self.mev_potential = mev_potential
        self.creator_id = creator_id
        self.included_pbs = False  # Separate inclusion flag for PBS
        self.included_pos = False  # Separate inclusion flag for PoS
        self.pbs_inclusion_time = None  # When it was included in PBS, if ever
        self.pos_inclusion_time = None  # When it was included in PoS, if ever
        self.successful_pbs = False  # Track if successfully attacked in PBS
        self.successful_pos = False  # Track if successfully attacked in PoS
        self.targeting = targeting
        self.target_tx_id = target_tx_id
        self.block_created = block_created
        self.transaction_type = transaction_type
        self.inclusion_log = []  # Track all inclusion details

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

USER_COUNTER = 1
BUILDER_COUNTER = 1
VALIDATOR_COUNTER = 1

class Participant:
    def __init__(self, participant_id):
        self.id = participant_id
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
        global USER_COUNTER
        super().__init__(USER_COUNTER)
        USER_COUNTER += 1

class AttackUser(Participant):
    def __init__(self):
        global USER_COUNTER
        super().__init__(USER_COUNTER)
        USER_COUNTER += 1

    def create_transaction(self, all_participants, target_tx=None, block_number=None):
        if target_tx and target_tx.mev_potential > 0 and target_tx.id not in targeting_tracker:
            higher_fees = [x for x in SAMPLE_GAS_FEES if x > target_tx.fee]
            fee = random.choice(higher_fees) if higher_fees else target_tx.fee + 1  # Use a default value if no higher fees are found
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
        global BUILDER_COUNTER
        super().__init__(BUILDER_COUNTER)
        self.is_attack = is_attack
        BUILDER_COUNTER += 1
        self.average_bid_percentage = 0.5  # Initial average bid percentage set to 50%

    def bid(self, block_bid_his, block_number):
        block_value = sum(tx.fee + tx.mev_potential for tx in self.mempool_pbs if not tx.included_pbs and tx.block_created <= block_number)

        if block_value == 0:
            return 0

        if block_bid_his:
            avg_percentage = np.mean([bid / block_value for round_bids in block_bid_his for bid in round_bids.values() if bid <= block_value])
            self.average_bid_percentage = avg_percentage

        initial_bid = self.average_bid_percentage * block_value

        if self.is_attack:
            bid = min(max(0, initial_bid * 1.1), block_value)
        else:
            bid = min(max(0, initial_bid), block_value)

        return bid

    def select_transactions(self, block_number):
        return select_transactions_common(self, block_number, self.mempool_pbs, 'pbs')

class Validator(Participant):
    def __init__(self, is_attack):
        global VALIDATOR_COUNTER
        super().__init__(VALIDATOR_COUNTER)
        self.is_attack = is_attack
        VALIDATOR_COUNTER += 1

    def select_transactions(self, block_number):
        return select_transactions_common(self, block_number, self.mempool_pos, 'pos')

def select_transactions_common(participant, block_number, mempool, system='pbs'):
    available_transactions = [tx for tx in mempool if not tx.included_pbs and tx.block_created <= block_number] if system == 'pbs' else [tx for tx in mempool if not tx.included_pos and tx.block_created <= block_number]
    selected_transactions = []

    if participant.is_attack:
        available_transactions.sort(key=lambda x: x.fee + x.mev_potential, reverse=True)
        targeted_tx_ids = set()
        attack_count = 0
        for tx in available_transactions:
            if len(selected_transactions) >= BLOCK_CAPACITY:
                break
            if tx.id in targeted_tx_ids:
                continue
            selected_transactions.append(tx)
            if tx.mev_potential > 0 and attack_count == 0:
                if tx.id not in targeting_tracker:
                    targeting_tracker[tx.id] = True
                    targeted_tx_ids.add(tx.id)
                    higher_fees = [x for x in SAMPLE_GAS_FEES if x > tx.fee]
                    fee = random.choice(higher_fees) if higher_fees else tx.fee + 1
                    attack_tx = Transaction(fee, tx.mev_potential, participant.id, targeting=True, target_tx_id=tx.id, block_created=tx.block_created, transaction_type="b_attack")
                    selected_transactions.append(attack_tx)
                    attack_count += 1
    else:
        available_transactions.sort(key=lambda x: x.fee + x.mev_potential, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]

    for tx in selected_transactions:
        if system == 'pbs':
            tx.included_pbs = True
        else:
            tx.included_pos = True

    return selected_transactions

def run_pbs(builders, num_blocks, users):
    cumulative_mev_transactions = [0] * num_blocks
    proposer_profits = {builder.id: [] for builder in builders}
    block_data = []
    transaction_data = []
    all_transactions_log = []  # Log for all transactions

    global targeting_tracker
    targeting_tracker = {}

    for block_num in range(num_blocks):
        block_bid_his = []

        for _ in range(24):
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

            all_transactions_log.append(tx)  # Log the transaction details

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
    all_transactions_log = []  # Log for all transactions

    global targeting_tracker
    targeting_tracker = {}

    for block_num in range(num_blocks):
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions(block_num + 1)

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

            all_transactions_log.append(tx)  # Log the transaction details

        for validator in validators:
            validator.mempool_pos = [tx for tx in validator.mempool_pos if tx.id not in included_tx_ids]

    return cumulative_mev_transactions, validator_profits, block_data, transaction_data, all_transactions_log

def run_simulation(run_id, mev_count):
    users = [NormalUser() if i < NUM_USERS // 2 else AttackUser() for i in range(NUM_USERS)]
    builders = [Builder(i < mev_count) for i in range(NUM_BUILDERS)]
    validators = [Validator(i < mev_count) for i in range(NUM_VALIDATORS)]

    all_participants = users + builders + validators

    global targeting_tracker
    targeting_tracker = {}

    for block_number in range(NUM_BLOCKS):
        for _ in range(24):
            attack_user = random.choice([u for u in users if isinstance(u, AttackUser)])
            normal_user = random.choice([u for u in users if isinstance(u, NormalUser)])

            # Attack user creates transaction
            target_tx_pbs = max(
                (tx for tx in attack_user.mempool_pbs if tx.mev_potential > 0 and not tx.included_pbs and tx.id not in targeting_tracker),
                default=None,
                key=lambda tx: tx.fee
            )
            target_tx_pos = max(
                (tx for tx in attack_user.mempool_pos if tx.mev_potential > 0 and not tx.included_pos and tx.id not in targeting_tracker),
                default=None,
                key=lambda tx: tx.fee
            )
            if target_tx_pbs:
                attack_user.create_transaction(all_participants, target_tx_pbs, block_number=block_number + 1)
            if target_tx_pos:
                attack_user.create_transaction(all_participants, target_tx_pos, block_number=block_number + 1)

            # Normal user creates transaction
            normal_user.create_transaction(all_participants, is_mev=random.choice([True, False]), block_number=block_number + 1)

    cumulative_mev_included_pbs, proposer_profits, block_data_pbs, transaction_data_pbs, all_transactions_pbs = run_pbs(builders, NUM_BLOCKS, users)
    cumulative_mev_included_pos, validator_profits, block_data_pos, transaction_data_pos, all_transactions_pos = run_pos(validators, NUM_BLOCKS, users)

    # Combine all transactions logs for both systems
    all_transactions_log = all_transactions_pbs + all_transactions_pos

    # Create directory for current MEV builder count
    run_output_dir = f'data/100_runs/run{run_id}/mev{mev_count}'
    pbs_output_dir = os.path.join(run_output_dir, 'pbs')
    pos_output_dir = os.path.join(run_output_dir, 'pos')
    all_tx_output_dir = os.path.join(run_output_dir, 'all_transactions')
    os.makedirs(pbs_output_dir, exist_ok=True)
    os.makedirs(pos_output_dir, exist_ok=True)
    os.makedirs(all_tx_output_dir, exist_ok=True)

    # Save PBS results
    block_data_pbs_df = pd.DataFrame(block_data_pbs)
    transaction_data_pbs_df = pd.DataFrame(transaction_data_pbs)
    block_data_pbs_df.to_csv(os.path.join(pbs_output_dir, 'block_data_pbs.csv'), index=False)
    transaction_data_pbs_df.to_csv(os.path.join(pbs_output_dir, 'transaction_data_pbs.csv'), index=False)

    # Save PoS results
    block_data_pos_df = pd.DataFrame(block_data_pos)
    transaction_data_pos_df = pd.DataFrame(transaction_data_pos)
    block_data_pos_df.to_csv(os.path.join(pos_output_dir, 'block_data_pos.csv'), index=False)
    transaction_data_pos_df.to_csv(os.path.join(pos_output_dir, 'transaction_data_pos.csv'), index=False)

    # Save all transactions log
    all_transactions_df = pd.DataFrame([vars(tx) for tx in all_transactions_log])
    all_transactions_df.to_csv(os.path.join(all_tx_output_dir, 'all_transactions.csv'), index=False)

if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        futures = []
        for run_id in range(1, NUM_RUNS + 1):
            for mev_count in MEV_BUILDER_COUNTS:
                futures.append(executor.submit(run_simulation, run_id, mev_count))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")
