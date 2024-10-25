import random
from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from copy import deepcopy
import csv
import time
import multiprocessing as mp
import os

random.seed(16)

BLOCKNUM = 1000
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 20

# Determine the number of CPU cores and set the number of processes
num_cores = os.cpu_count()
num_processes = max(num_cores - 1, 1)  # Use all cores except one, but at least 1

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
            tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
            if tx:
                all_block_transactions.append(tx)
                user.broadcast_transactions(tx)
    
    builder_results = []
    for builder in builders:
        selected_transactions = builder.select_transactions(block_num)
        bid_value = builder.bid(selected_transactions)
        builder_results.append((builder.id, selected_transactions, bid_value))
    
    highest_bid_builder_id, highest_bid_transactions, highest_bid_value = max(builder_results, key=lambda x: x[2])
    highest_bid_builder = next(b for b in builders if b.id == highest_bid_builder_id)
    
    for position, tx in enumerate(highest_bid_transactions):
        tx.position = position
        tx.included_at = block_num
    
    all_block_transactions.extend(highest_bid_transactions)

    total_gas_fee = sum(tx.gas_fee for tx in highest_bid_transactions)
    total_mev = sum(tx.mev_potential for tx in highest_bid_transactions)

    mev_targets = [tx for tx in highest_bid_transactions if tx.mev_potential > 0]
    total_mev_captured_by_attackers = 0
    total_mev_captured_by_builders = 0
    for targeted_tx in mev_targets:
        targeting_txs = [tx for tx in highest_bid_transactions if tx.target_tx == targeted_tx.id]
        if targeting_txs:
            closest_tx = min(targeting_txs, key=lambda tx: abs(tx.position - targeted_tx.position))
            attacker = next((user for user in users if user.id == closest_tx.sender), None)
            if attacker:
                attacker.balance += targeted_tx.mev_potential
                total_mev_captured_by_attackers += targeted_tx.mev_potential
            else:
                builder = next((builder for builder in builders if builder.id == closest_tx.sender), None)
                if builder:
                    builder.balance += targeted_tx.mev_potential
                    total_mev_captured_by_builders += targeted_tx.mev_potential

    block_content = {
        "block_num": block_num,
        "builder_id": highest_bid_builder.id,
        "bid_value": highest_bid_value,
        "transactions": highest_bid_transactions
    }

    block_data = {
        "block_num": block_num,
        "builder_id": highest_bid_builder.id,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev,
        "total_mev_captured_by_attackers": total_mev_captured_by_attackers,
        "total_mev_captured_by_builders": total_mev_captured_by_builders
    }

    for builder in builders:
        builder.clear_mempool(block_num)

    return block_content, block_data, all_block_transactions

def simulate_pbs(users, builders):
    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_block, [(block_num, users, builders) for block_num in range(BLOCKNUM)])

    blocks, block_data, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]

    # Save transaction data to CSV
    with open('data/same_seed/pbs_transactions.csv', 'w', newline='') as f:
        if not all_transactions:
            return blocks

        fieldnames = all_transactions[0].to_dict().keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in all_transactions:
            writer.writerow(tx.to_dict())

    # Save block data to a separate CSV
    with open('data/same_seed/pbs_block_data.csv', 'w', newline='') as f:
        fieldnames = ['block_num', 'builder_id', 'total_gas_fee', 'total_mev_available', 
                      'total_mev_captured_by_attackers', 'total_mev_captured_by_builders']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block in block_data:
            writer.writerow(block)

    return blocks

if __name__ == "__main__":
    start_time = time.time()

    builders = [Builder(f"builder_{i}", i < (BUILDERNUM // 2)) for i in range(BUILDERNUM)]
    users = [User(f"user_{i}", i < (USERNUM // 2), builders) for i in range(USERNUM)]

    simulate_pbs(users, builders)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Simulation completed in {execution_time:.2f} seconds")
