import random
import os
import csv
from blockchain_env.transaction import Transaction
from blockchain_env.user import User
from copy import deepcopy

BLOCK_CAP = 100
BLOCK_NUM = 100
USERNUM = 50
BUILDERNUM = 20

class ModifiedBuilder:
    def __init__(self, builder_id, is_attacker):
        self.id = builder_id
        self.is_attacker = is_attacker
        self.balance = 0
        self.mempool = []
        self.selected_transactions = []

    def launch_attack(self, block_num, target_transaction, attack_type):
        mev_potential = 0
        gas_fee = 0

        creator_id = self.id
        created_at = block_num
        target_tx = target_transaction

        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction):
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num):
        selected_transactions = []
        if self.is_attacker:
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    if transaction.mev_potential > 0:
                        attack_type = random.choice(['front', 'back'])
                        attack_transaction = self.launch_attack(block_num, transaction, attack_type)

                        if attack_type == 'front':
                            selected_transactions.append(attack_transaction)
                            selected_transactions.append(transaction)
                        elif attack_type == 'back':
                            selected_transactions.append(transaction)
                            selected_transactions.append(attack_transaction)

                        if len(selected_transactions) > BLOCK_CAP:
                            selected_transactions.pop()
                    else:
                        selected_transactions.append(transaction)
        else:
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    selected_transactions.append(transaction)

        return selected_transactions

    def bid(self, selected_transactions):
        total_gas_fee = sum(tx.gas_fee for tx in selected_transactions)
        block_value = total_gas_fee

        if self.is_attacker:
            mev_gain = sum(tx.target_tx.mev_potential for tx in selected_transactions if tx.target_tx)
            block_value += mev_gain

        bid = 0.5 * block_value
        bid_values = []

        for round_number in range(24):  # 24 bidding rounds
            # Dynamically adjust the mempool by removing transactions after they are "included" in bids
            gas_fees = [tx.gas_fee for tx in self.mempool]
            if not gas_fees:
                bid_values.append(bid)
                continue

            highest_bid = max(gas_fees)

            if highest_bid > bid:
                bid = min(highest_bid, bid + 0.1 * highest_bid)
            else:
                sorted_bids = sorted(gas_fees, reverse=True)
                if len(sorted_bids) > 1:
                    second_highest_bid = sorted_bids[1]
                    bid = max(0.5 * (highest_bid + second_highest_bid), bid)
                else:
                    bid = max(0.5 * highest_bid, bid)

            # Remove the transaction corresponding to the highest bid from the mempool
            self.mempool = [tx for tx in self.mempool if tx.gas_fee != highest_bid]

            bid_values.append(bid)

        return bid_values, block_value

    def get_mempool(self):
        return self.mempool

    def clear_mempool(self, block_num):
        timer = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]

def transaction_number():
    random_number = random.randint(0, 100)
    if random_number < 50:
        return 1
    elif random_number < 80:
        return 0
    elif random_number < 95:
        return 2
    else:
        return random.randint(3, 5)

def process_block(block_num, users, builders):
    all_block_transactions = []

    # Broadcast user transactions
    for user in users:
        num_transactions = transaction_number()
        for _ in range(num_transactions):
            tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
            if tx:
                user.broadcast_transactions(tx)

    builder_results = []
    for builder in builders:
        # Select transactions for the block
        selected_transactions = builder.select_transactions(block_num)

        # Simulate bidding across rounds
        bid_values, block_value = builder.bid(selected_transactions)
        builder_results.append((builder.id, bid_values, block_value))

    # Clear old transactions from mempools
    for builder in builders:
        builder.clear_mempool(block_num)

    return builder_results

def simulate_pbs():
    attack_variants = [0, 5, 10, 15, 20]

    for num_attack_builders in attack_variants:
        builders = [ModifiedBuilder(f"builder_{i}", i < num_attack_builders) for i in range(BUILDERNUM)]
        users = [User(f"user_{i}", i < USERNUM // 2, builders) for i in range(USERNUM)]

        output_file = f"data/same_seed/bid_builder{num_attack_builders}.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["block_num", "builder_id", "bid_round", "bid_value", "block_value"])

            for block_num in range(BLOCK_NUM):
                builder_results = process_block(block_num, users, builders)
                for builder_id, bid_values, block_value in builder_results:
                    for bid_round, bid_value in enumerate(bid_values):
                        # Record a single bid value for each round
                        writer.writerow([block_num, builder_id, bid_round, bid_value, block_value])

if __name__ == "__main__":
    simulate_pbs()
