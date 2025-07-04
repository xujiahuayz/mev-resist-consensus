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
PROPNUM = 20

# Seed for reproducibility
random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores = os.cpu_count()
num_processes = max(num_cores - 1, 1)  # Use all cores except one, but at least one

def transaction_number():
    random_number = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def process_block(block_num, users, validators):
    # Pre-sample validators for each block using `random.choices`
    selected_validators = random.choices(validators, k=BLOCKNUM)

    all_block_transactions = []
    for user in users:
        num_transactions = transaction_number()
        for _ in range(num_transactions):
            tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
            if tx:
                user.broadcast_transactions(tx)

    # Randomly select a proposer
    selected_validator = selected_validators[block_num]
    selected_validator.selected_transactions = selected_validator.select_transactions(BLOCK_CAP)

    # Assign transaction positions and inclusion times
    for position, tx in enumerate(selected_validator.selected_transactions):
        tx.position = position
        tx.included_at = block_num

    all_block_transactions.extend(selected_validator.selected_transactions)

    # Clear validators' mempools
    for validator in validators:
        validator.clear_mempool(block_num)

    total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
    total_mev = sum(tx.mev_potential for tx in selected_validator.selected_transactions)

    block_data = {
        "block_num": block_num,
        "validator_id": selected_validator.id,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev
    }

    return block_data, selected_validator.selected_transactions

def simulate_pos(attacker_validators, attacker_users):
    validators = [Builder(f"validator_{i}", i < attacker_validators) for i in range(PROPNUM)]
    users = [User(f"user_{i}", i < attacker_users) for i in range(USERNUM)]

    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_block, [(block_num, users, validators) for block_num in range(BLOCKNUM)])

    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]

    # Define dynamic filenames
    transaction_filename = f"data/same_seed/pos_visible80/pos_transactions_validators{attacker_validators}_users{attacker_users}.csv"
    block_filename = f"data/same_seed/pos_visible80/pos_block_data_validators{attacker_validators}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)

    # Save transaction data to CSV
    with open(transaction_filename, 'w', newline='', encoding='utf-8') as f:
        if all_transactions:
            fieldnames = all_transactions[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in all_transactions:
                writer.writerow(tx.to_dict())

    # Save block data to a separate CSV
    with open(block_filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['block_num', 'validator_id', 'total_gas_fee', 'total_mev_available']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

    return block_data_list

if __name__ == "__main__":
    for num_attacker_validators in range(PROPNUM + 1):
        for num_attacker_users in range(USERNUM + 1):
            start_time = time.time()
            # Run the simulation for the current parameter set
            simulate_pos(num_attacker_validators, num_attacker_users)
            # Calculate and print the time taken for this round
            end_time = time.time()
            round_time = end_time - start_time
            print(f"Simulation with {num_attacker_validators} attacker validators and {num_attacker_users} attacker users completed in {round_time:.2f} seconds")
