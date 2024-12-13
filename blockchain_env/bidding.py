"""We simulate only the bidding with 24 rounds in this file"""

import random
import os
import csv
import time
import multiprocessing as mp
from blockchain_env.user import User
from blockchain_env.transaction import Transaction
from copy import deepcopy

# Constants
BLOCKNUM = 100
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 20

# Seed for reproducibility
random.seed(16)

class Builder:
    def __init__(self, builder_id, is_attacker):
        self.id = builder_id
        self.is_attacker = is_attacker
        self.balance = 0
        self.mempool = []
        self.selected_transactions = []

    def launch_attack(self, block_num, target_transaction, attack_type):
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        mev_potential = 0
        gas_fee = 0

        creator_id = self.id
        created_at = block_num
        target_tx = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction):
        # Builder receives transaction and adds to mempool
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num):
        selected_transactions = []
        if self.is_attacker:
            # Sort transactions by mev potential + gas fee for attackers
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
            # Sort transactions by gas fee for non-attackers
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    selected_transactions.append(transaction)

        return selected_transactions

    def bid(self, selected_transactions):
        total_gas_fee = sum(tx.gas_fee for tx in selected_transactions)
        
        # Initial block value is based on total gas fee
        block_value = total_gas_fee
        
        # Check if the builder is an attacker and has launched any attack
        if self.is_attacker:
            # Sum the MEV potential of targeted transactions if any attacks are launched
            mev_gain = sum(tx.target_tx.mev_potential for tx in selected_transactions if tx.target_tx)
            block_value += mev_gain  # Add MEV profit to block value for attackers

        # Initial bid is 50% of the adjusted block value
        bid = 0.5 * block_value

        # Reactive strategy over 5 rounds of bidding
        for _ in range(24):
            # Get current highest bid from history in the builder's mempool
            gas_fees = [tx.gas_fee for tx in self.mempool]
            if len(gas_fees) == 0:
                break  # If no transactions in the mempool, exit the loop

            highest_bid = max(gas_fees)
            
            if highest_bid > bid:
                # Increase bid by 0.1 times the highest bid
                bid = min(highest_bid, bid + 0.1 * highest_bid)
            else:
                # Get the second highest bid if possible, else use the current bid
                sorted_bids = sorted(gas_fees, reverse=True)
                if len(sorted_bids) > 1:
                    second_highest_bid = sorted_bids[1]
                    bid = max(0.5 * (highest_bid + second_highest_bid), bid)
                else:
                    bid = max(0.5 * highest_bid, bid)

        # Return the final bid for this builder
        return bid

    def get_mempool(self):
        return self.mempool
    
    def clear_mempool(self, block_num):
        # clear any transsaction that is already included onchain, and also clear pending transactions that has been in mempool for too long
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

    for user in users:
        num_transactions = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx = user.create_transactions(block_num)
            else:
                tx = user.launch_attack(block_num)
            if tx:
                user.broadcast_transactions(tx)

    builder_results = []
    for builder in builders:
        selected_transactions = builder.select_transactions(block_num)
        bid_values, block_value = builder.bid(selected_transactions)
        builder_results.append((builder.id, selected_transactions, bid_values, block_value))

    highest_bid = max(builder_results, key=lambda x: x[3])
    highest_bid_builder = next(b for b in builders if b.id == highest_bid[0])

    for position, tx in enumerate(highest_bid[1]):
        tx.position = position
        tx.included_at = block_num

    all_block_transactions.extend(highest_bid[1])
    total_gas_fee = sum(tx.gas_fee for tx in highest_bid[1])
    total_mev = sum(tx.mev_potential for tx in highest_bid[1])

    block_data = {
        "block_num": block_num,
        "builder_id": highest_bid_builder.id,
        "total_gas_fee": total_gas_fee,
        "total_mev": total_mev
    }

    for builder in builders:
        builder.clear_mempool(block_num)

    return block_data, all_block_transactions

def simulate_pbs(num_attacker_builders, num_attacker_users):
    builders = [Builder(f"builder_{i}", i < num_attacker_builders) for i in range(BUILDERNUM)]
    users = [User(f"user_{i}", i < num_attacker_users, builders) for i in range(USERNUM)]

    for block_num in range(BLOCKNUM):
        block_data, all_block_transactions = process_block(block_num, users, builders)

if __name__ == "__main__":
    simulate_pbs(num_attacker_builders=5, num_attacker_users=USERNUM // 2)