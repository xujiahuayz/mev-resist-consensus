import random
import os
import csv
import time
import multiprocessing as mp
from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.network import build_network

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

# Create network participants and build network once (same as PBS)
validator_list = [Builder(f"validator_{i}", False) for i in range(PROPNUM)]  # is_attacker will be set in simulation
user_list = [User(f"user_{i}", False) for i in range(USERNUM)]  # is_attacker will be set in simulation
# For POS, we use validators instead of builders/proposers, but we need empty list for build_network
network = build_network(user_list, validator_list, [])

def transaction_number():
    random_number = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def process_block(block_num, network_graph):
    """Process a single block in the POS simulation."""
    # Extract network nodes
    from blockchain_env.network import Node
    user_nodes = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], User)]
    validator_nodes = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], Builder)]
    
    # Process user transactions
    for user in user_nodes:
        num_transactions = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx = user.create_transactions(block_num)
            else:
                tx = user.launch_attack(block_num)
            if tx:
                user.broadcast_transactions(tx)
    
    # Process messages for validators (transaction propagation)
    for validator in validator_nodes:
        messages = validator.receive_messages(current_round=block_num)
        for msg in messages:
            if hasattr(validator, 'receive_transaction'):
                validator.receive_transaction(msg.content)
    
    # Randomly select a validator for this block
    selected_validator = random.choice(validator_nodes)
    selected_transactions = selected_validator.select_transactions(block_num)
    
    # Assign transaction positions and inclusion times
    for position, tx in enumerate(selected_transactions):
        tx.position = position
        tx.included_at = block_num
    
    # Clear mempools for ALL participants (users and validators) instantaneously
    # This removes transactions that have been included on-chain, regardless of propagation delay
    included_tx_ids = {tx.id for tx in selected_transactions} if selected_transactions else set()
    
    # Remove included transactions from all users' mempools
    for user in user_nodes:
        user.mempool = [tx for tx in user.mempool if tx.id not in included_tx_ids]
        user.clear_mempool(block_num)
    
    # Remove included transactions from all validators' mempools
    for validator in validator_nodes:
        validator.mempool = [tx for tx in validator.mempool if tx.id not in included_tx_ids]
        validator.clear_mempool(block_num)
    
    total_gas_fee = sum(tx.gas_fee for tx in selected_transactions)
    total_mev = sum(tx.mev_potential for tx in selected_transactions)

    block_data = {
        "block_num": block_num,
        "validator_id": selected_validator.id,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev
    }

    return block_data, selected_transactions

def _set_attacker_status(attacker_validator_count, attacker_user_count):
    """Set attacker status for validators and users."""
    for i, validator in enumerate(validator_list):
        validator.is_attacker = i < attacker_validator_count
    for i, user in enumerate(user_list):
        user.is_attacker = i < attacker_user_count

def run_simulation_in_process(attacker_validator_count, attacker_user_count):
    """Run each simulation in a separate process to avoid state leakage."""
    process = mp.Process(target=simulate_pos, args=(attacker_validator_count, attacker_user_count))
    process.start()
    process.join()  # Wait for the process to complete

def simulate_pos(attacker_validators, attacker_users):
    # Set attacker status for validators and users
    _set_attacker_status(attacker_validators, attacker_users)

    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_block, [(block_num, network) for block_num in range(BLOCKNUM)])

    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]

    # Define dynamic filenames (using same network configuration as PBS)
    transaction_filename = f"data/same_seed/pos_network_p0.05/pos_transactions_validators{attacker_validators}_users{attacker_users}.csv"
    block_filename = f"data/same_seed/pos_network_p0.05/pos_block_data_validators{attacker_validators}_users{attacker_users}.csv"
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
            run_simulation_in_process(num_attacker_validators, num_attacker_users)
            # Calculate and print the time taken for this round
            end_time = time.time()
            round_time = end_time - start_time
            print(f"POS Simulation with {num_attacker_validators} attacker validators and {num_attacker_users} attacker users completed in {round_time:.2f} seconds")
