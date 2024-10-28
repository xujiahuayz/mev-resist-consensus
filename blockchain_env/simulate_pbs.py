import random
import os
import csv
import time
import multiprocessing as mp
from blockchain_env.user import User
from blockchain_env.builder import Builder

# Constants
BLOCKNUM = 1000
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 20

# Seed for reproducibility
random.seed(21)

# Determine the number of CPU cores and set the number of processes
num_cores = os.cpu_count()
num_processes = max(num_cores - 1, 1)  # Use all cores except one, but at least one

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
            tx = user.create_transactions(block_num)
            if tx:
                user.broadcast_transactions(tx)
    
    builder_results = []
    for builder in builders:
        selected_transactions = builder.select_transactions(block_num)
        bid_value = builder.bid(selected_transactions)
        builder_results.append((builder.id, selected_transactions, bid_value))
    
    highest_bid = max(builder_results, key=lambda x: x[2])
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

    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_block, [(block_num, users, builders) for block_num in range(BLOCKNUM)])
    
    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]

    # Save transaction data to CSV
    transaction_filename = f"data/same_seed/pbs_visible80/pbs_transactions_builders{num_attacker_builders}_users{num_attacker_users}.csv"
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)
    with open(transaction_filename, 'w', newline='') as f:
        if all_transactions:
            fieldnames = all_transactions[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in all_transactions:
                writer.writerow(tx.to_dict())

    # Save block data to a separate CSV
    block_filename = f"data/same_seed/pbs_visible80/pbs_block_data_builders{num_attacker_builders}_users{num_attacker_users}.csv"
    with open(block_filename, 'w', newline='') as f:
        fieldnames = ['block_num', 'builder_id', 'total_gas_fee', 'total_mev']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

    return block_data_list

if __name__ == "__main__":

    for num_attacker_builders in range(BUILDERNUM + 1):
        for num_attacker_users in range(USERNUM + 1):
            start_time = time.time()
            simulate_pbs(num_attacker_builders, num_attacker_users)
            end_time = time.time()
            round_time = end_time - start_time
            print(f"Simulation with {num_attacker_builders} attacker validators and
                {num_attacker_users} attacker users completed in {round_time:.2f} seconds")
