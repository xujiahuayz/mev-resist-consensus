import random
import os
import csv
import time
import multiprocessing as mp
import numpy as np

from blockchain_env.user import User
from blockchain_env.validator import Validator

BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 100
PROPNUM = 100  # Back to 100 to match PBS total nodes

VALIDATOR_THRESHOLD = 32 * 10**9
MIN_VALIDATOR_NODES = 1
TOTAL_NETWORK_STAKE = 1000 * VALIDATOR_THRESHOLD
REINVESTMENT_PROBABILITY = 0.5

MAX_WORKERS = mp.cpu_count()
BATCH_SIZE = 500

random.seed(16)

def initialize_validators_with_stakes():
    validator_list = []
    
    # Define specific stake levels with guaranteed attack/benign distribution
    # Match PBS builder distribution exactly: 2 of each for 8, 4 of each for 5, 6 of each for 3, 10 of each for 2, rest for 1
    stake_levels = [
        (8, 2, 2),   # 8 ETH: 2 attack, 2 benign
        (5, 4, 4),   # 5 ETH: 4 attack, 4 benign  
        (3, 6, 6),   # 3 ETH: 6 attack, 6 benign
        (2, 10, 10), # 2 ETH: 10 attack, 10 benign
    ]
    
    validator_count = 0
    attack_count = 0
    benign_count = 0
    
    # Create validators with specific stake levels first
    for stake_multiplier, num_attack, num_benign in stake_levels:
        initial_stake = VALIDATOR_THRESHOLD * stake_multiplier
        
        # Create attack validators for this stake level
        for _ in range(num_attack):
            if validator_count >= PROPNUM:
                break
            validator = Validator(f"validator_{validator_count}", True, initial_stake, restaking_factor=True)
            validator_list.append(validator)
            validator_count += 1
            attack_count += 1
        
        # Create benign validators for this stake level
        for _ in range(num_benign):
            if validator_count >= PROPNUM:
                break
            validator = Validator(f"validator_{validator_count}", False, initial_stake, restaking_factor=True)
            validator_list.append(validator)
            validator_count += 1
            benign_count += 1
    
    # Fill remaining validator slots with 1 ETH stake validators
    # Ensure we maintain the requested attack/benign ratio for remaining slots
    remaining_slots = PROPNUM - validator_count
    remaining_attack_needed = PROPNUM // 2 - attack_count
    remaining_benign_needed = (PROPNUM - PROPNUM // 2) - benign_count
    
    # Create remaining attack validators with 1 ETH stake
    for _ in range(min(remaining_attack_needed, remaining_slots)):
        if validator_count >= PROPNUM:
            break
        validator = Validator(f"validator_{validator_count}", True, VALIDATOR_THRESHOLD, restaking_factor=True)
        validator_list.append(validator)
        validator_count += 1
    
    # Create remaining benign validators with 1 ETH stake
    for _ in range(min(remaining_benign_needed, PROPNUM - validator_count)):
        if validator_count >= PROPNUM:
            break
        validator = Validator(f"validator_{validator_count}", False, VALIDATOR_THRESHOLD, restaking_factor=True)
        validator_list.append(validator)
        validator_count += 1
    
    return validator_list

def get_validator_nodes(validators):
    nodes = []
    for validator in validators:
        num_nodes = validator.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            for _ in range(num_nodes):
                nodes.append(validator)
    return nodes

def update_stake(participant, profit: int):
    participant.capital += profit
    
    reinvested = int(profit * participant.reinvestment_factor)
    extracted = profit - reinvested

    participant.active_stake = VALIDATOR_THRESHOLD * (participant.capital // VALIDATOR_THRESHOLD)
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)

def transaction_number():
    random_number = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def process_block_batch(args):
    block_range, users, validators = args
    block_data_list = []
    start_block, end_block = block_range
    
    for block_num in range(start_block, end_block):
        validator_nodes = get_validator_nodes(validators)
        if not validator_nodes:
            continue
            
        selected_validator = random.choice(validator_nodes)
        
        for user in users:
            num_transactions = transaction_number()
            for _ in range(num_transactions):
                tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
                if tx:
                    user.broadcast_transactions(tx)
                    selected_validator.mempool.append(tx)
        
        selected_validator.selected_transactions = selected_validator.select_transactions(block_num)
        
        for position, tx in enumerate(selected_validator.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            update_stake(selected_validator, int(block_reward))
        else:
            pass
        
        block_data = {
            "block_num": block_num,
            "validator_id": selected_validator.id,
            "validator_capital": selected_validator.capital,
            "validator_restaking_factor": selected_validator.restaking_factor,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev,
            "block_reward": block_reward,
            "is_attacker": selected_validator.is_attacker,
            "num_validator_nodes": selected_validator.active_stake // VALIDATOR_THRESHOLD
        }
        
        block_data_list.append(block_data)
        
        for validator in validators:
            validator.clear_mempool(block_num)
    
    return block_data_list

def simulate_restaking_pos():
    print("Starting Corrected Restaking PoS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    print(f"Attackers: {PROPNUM // 2} validators, {USERNUM // 2} users")
    print("Running sequentially to avoid multiprocessing race conditions")
    
    validators = initialize_validators_with_stakes()
    users = [User(f"user_{i}", i < USERNUM // 2) for i in range(USERNUM)]
    
    start_time = time.time()
    
    all_blocks = []
    
    for block_num in range(BLOCKNUM):
        if block_num % 1000 == 0:
            print(f"Processing block {block_num}/{BLOCKNUM}")
        
        validator_nodes = get_validator_nodes(validators)
        if not validator_nodes:
            continue
            
        selected_validator = random.choice(validator_nodes)
        
        for user in users:
            num_tx = random.randint(1, 5)
            for _ in range(num_tx):
                tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
                if tx:
                    user.broadcast_transactions(tx)
                    selected_validator.mempool.append(tx)
        
        selected_validator.selected_transactions = selected_validator.select_transactions(block_num)
        
        for position, tx in enumerate(selected_validator.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            update_stake(selected_validator, int(block_reward))
        
        block_data = {
            "block_num": block_num,
            "validator_id": selected_validator.id,
            "validator_capital": selected_validator.capital,
            "validator_restaking_factor": selected_validator.restaking_factor,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev,
            "block_reward": block_reward,
            "is_attacker": selected_validator.is_attacker,
            "num_validator_nodes": selected_validator.active_stake // VALIDATOR_THRESHOLD
        }
        
        all_blocks.append(block_data)
        
        for validator in validators:
            validator.clear_mempool(block_num)
    
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(all_blocks)} blocks")
    
    save_results(all_blocks, validators)
    
    return all_blocks

def save_results(block_data, validators):
    output_dir = "data/same_seed/restaking_pos/"
    os.makedirs(output_dir, exist_ok=True)
    
    if block_data:
        with open(f"{output_dir}restaking_pos_blocks.csv", 'w', newline='', encoding='utf-8') as f:
            fieldnames = block_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(block_data)
    
    with open(f"{output_dir}stake_evolution.csv", 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['participant_id', 'participant_type', 'is_attacker', 'reinvestment_factor',
                     'initial_stake', 'final_stake', 'total_profit', 'num_validator_nodes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for validator in validators:
            writer.writerow({
                'participant_id': validator.id,
                'participant_type': 'validator',
                'is_attacker': validator.is_attacker,
                'reinvestment_factor': validator.reinvestment_factor,
                'initial_stake': validator.initial_stake,
                'final_stake': validator.active_stake,
                'total_profit': sum(validator.profit_history),
                'num_validator_nodes': validator.active_stake // VALIDATOR_THRESHOLD
            })
    
    print(f"Results saved to {output_dir}")

def _save_block_data(block_data_list):
    if not block_data_list:
        return
    
    filename = "data/same_seed/restaking_pos/restaking_pos_blocks.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = block_data_list[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

if __name__ == "__main__":
    print("Corrected Restaking PoS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    simulate_restaking_pos()
