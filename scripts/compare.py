import random
import uuid
import pandas as pd
import os
import numpy as np

random.seed(42)

NUM_USERS = 20
NUM_BUILDERS = 10
NUM_VALIDATORS = 10
BLOCK_CAPACITY = 10
NUM_TRANSACTIONS_PER_BLOCK = 20
NUM_BLOCKS = 10

FIXED_GAS_FEES = [0.05, 0.1]
MEV_POTENTIALS = [0.15, 0.2]

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
        fee = random.choice(FIXED_GAS_FEES)
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
        if target_tx and target_tx.is_mev:
            fee = target_tx.fee + 0.01
            tx = Transaction(fee, False, self.id, targeting=True, target_tx_id=target_tx.id, block_created=block_number)
            self.broadcast_transaction(tx)
            return tx
        else:
            fee = random.choice(FIXED_GAS_FEES)
            tx = Transaction(fee, False, self.id, block_created=block_number)
            self.broadcast_transaction(tx)
            return tx

class Builder(Participant):
    def __init__(self, is_attack):
        global builder_counter
        super().__init__(builder_counter)
        self.is_attack = is_attack
        builder_counter += 1

    def bid(self, block_bid_his, block_number):
        block_value = sum(tx.fee for tx in self.mempool_pbs if not tx.included and tx.block_created <= block_number)
        if block_bid_his:
            last_bid = max(block_bid_his[-1].values())
            new_bid = min(np.random.normal(last_bid, last_bid * 0.5), block_value)
            return new_bid
        else:
            return block_value * 0.5

    def select_transactions(self, block_number):
        available_transactions = [tx for tx in self.mempool_pbs if not tx.included and tx.block_created <= block_number]
        if self.is_attack:
            mev_transactions = [tx for tx in available_transactions if tx.is_mev]
            for tx in mev_transactions:
                front_run_tx = Transaction(tx.fee + 0.01, False, self.id, targeting=True, target_tx_id=tx.id, block_created=tx.block_created)
                self.broadcast_transaction(front_run_tx)

        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]

        for tx in selected_transactions:
            tx.included = True

        return selected_transactions

class Validator(Participant):
    def __init__(self, is_attack):
        global validator_counter
        super().__init__(validator_counter)
        self.is_attack = is_attack
        validator_counter += 1

    def select_transactions(self, block_number):
        available_transactions = [tx for tx in self.mempool_pos if not tx.included and tx.block_created <= block_number]
        available_transactions.sort(key=lambda x: x.fee, reverse=True)
        selected_transactions = available_transactions[:BLOCK_CAPACITY]

        for tx in selected_transactions:
            tx.included = True

        return selected_transactions

log_file = open('simulation_log.txt', 'w')

def log(msg):
    print(msg)
    log_file.write(msg + '\n')

def run_pbs(builders, num_blocks):
    cumulative_mev_transactions = [0] * num_blocks
    builder_profits = {builder.id: [] for builder in builders}
    block_data = []
    transaction_data = []

    targeting_tracker = {}

    for block_num in range(num_blocks):
        log(f"\n--- PBS Block {block_num + 1} ---")
        block_bid_his = []

        for counter in range(24):
            counter_bids = {}
            for builder in builders:
                bid = builder.bid(block_bid_his, block_num + 1)
                counter_bids[builder.id] = bid
                log(f"Builder {builder.id} ({'attack' if builder.is_attack else 'normal'}) bid: {bid:.2f}")
            block_bid_his.append(counter_bids)

        highest_bid = max(block_bid_his[-1].values())
        winning_builder_id = max(block_bid_his[-1], key=block_bid_his[-1].get)
        winning_builder = next(b for b in builders if b.id == winning_builder_id)
        log(f"Winning builder: {winning_builder_id} with bid: {highest_bid:.2f}")

        selected_transactions = winning_builder.select_transactions(block_num + 1)
        log(f"Transactions selected by builder {winning_builder.id}:")
        for tx in selected_transactions:
            log(f"  - TX ID: {tx.id}, Fee: {tx.fee}, MEV: {tx.is_mev}, Creator: {tx.creator_id}")

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

        # Log remaining mempool
        log("Remaining mempool for PBS after block inclusion:")
        for builder in builders:
            for tx in builder.mempool_pbs:
                log(f"  - TX ID: {tx.id}, Fee: {tx.fee}, Included: {tx.included}")

    builder_final_profits = {k: v[-1] for k, v in builder_profits.items() if v}

    return cumulative_mev_transactions, builder_final_profits, block_data, transaction_data

def run_pos(validators, num_blocks):
    cumulative_mev_transactions = []
    validator_profits = {validator.id: 0 for validator in validators}
    total_mev_transactions = 0
    block_data = []
    transaction_data = []

    targeting_tracker = {}

    for block_num in range(num_blocks):
        log(f"\n--- PoS Block {block_num + 1} ---")
        validator = random.choice(validators)
        selected_transactions = validator.select_transactions(block_num + 1)
        log(f"Transactions selected by validator {validator.id}:")
        for tx in selected_transactions:
            log(f"  - TX ID: {tx.id}, Fee: {tx.fee}, MEV: {tx.is_mev}, Creator: {tx.creator_id}")

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

        # Log remaining mempool
        log("Remaining mempool for PoS after block inclusion:")
        for validator in validators:
            for tx in validator.mempool_pos:
                log(f"  - TX ID: {tx.id}, Fee: {tx.fee}, Included: {tx.included}")

    return cumulative_mev_transactions, validator_profits, block_data, transaction_data

if __name__ == "__main__":
    users = [NormalUser() if i < NUM_USERS // 2 else AttackUser() for i in range(NUM_USERS)]
    builders = [Builder(i >= NUM_BUILDERS // 2) for i in range(NUM_BUILDERS)]
    validators = [Validator(i >= NUM_VALIDATORS // 2) for i in range(NUM_VALIDATORS)]

    all_participants = users + builders + validators

    for block_number in range(NUM_BLOCKS):
        for counter in range(24):
            attack_user = random.choice([u for u in users if isinstance(u, AttackUser)])
            normal_user = random.choice([u for u in users if isinstance(u, NormalUser)])

            # Attack user creates transaction
            target_tx_pbs = next((tx for tx in attack_user.mempool_pbs if tx.is_mev and not tx.included and tx.id not in [t.target_tx_id for t in attack_user.mempool_pbs if t.targeting]), None)
            target_tx_pos = next((tx for tx in attack_user.mempool_pos if tx.is_mev and not tx.included and tx.id not in [t.target_tx_id for t in attack_user.mempool_pos if t.targeting]), None)
            attack_user.create_transaction(target_tx_pbs, block_number=block_number + 1)
            attack_user.create_transaction(target_tx_pos, block_number=block_number + 1)

            # Normal user creates transaction
            normal_user.create_transaction(is_mev=random.choice([True, False]), block_number=block_number + 1)

    # Debugging to check the number of transactions created by each user 
    for user in users:
        log(f"User {user.id} created {len(user.mempool_pbs)} transactions")

    total_mev_created = sum(1 for user in users for tx in user.mempool_pbs if tx.is_mev)
    log(f"Total MEV Created: {total_mev_created}")

    cumulative_mev_included_pbs, builder_profits, block_data_pbs, transaction_data_pbs = run_pbs(builders, NUM_BLOCKS)
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

log_file.close()
