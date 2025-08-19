"""Corrected PoS simulation with restaking dynamics using proper 32 ETH validator threshold and uniform node selection."""

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
USERNUM = 100  # Increased to 100 users as requested
PROPNUM = 50

VALIDATOR_THRESHOLD = 32 * 10**9  # 32 ETH in gwei - CORRECTED
MIN_VALIDATOR_NODES = 1  # Must have at least 1 node to be a validator
TOTAL_NETWORK_STAKE = 1000 * VALIDATOR_THRESHOLD
REINVESTMENT_PROBABILITY = 0.5

MAX_WORKERS = mp.cpu_count()
BATCH_SIZE = 500

random.seed(16)

def initialize_validators_with_stakes():
    """Initialize validators with proper stake requirements."""
    validator_list = []
    
    # Validators must have at least 1 node (32 ETH)
    stake_distribution = [
        (1, 0.45),   # 1 node (32 ETH)
        (2, 0.25),   # 2 nodes (64 ETH)
        (3, 0.15),   # 3 nodes (96 ETH)
        (5, 0.10),   # 5 nodes (160 ETH)
        (8, 0.05),   # 8 nodes (256 ETH)
    ]
    
    for i in range(PROPNUM):
        rand_val = random.random()
        cumulative_prob = 0
        selected_stake_multiplier = 1
        
        for stake_multiplier, probability in stake_distribution:
            cumulative_prob += probability
            if rand_val <= cumulative_prob:
                selected_stake_multiplier = stake_multiplier
                break
        
        initial_stake = VALIDATOR_THRESHOLD * selected_stake_multiplier
        is_attacker = i < PROPNUM // 2
        
        # All validators are restaking
        validator = Validator(f"validator_{i}", is_attacker, initial_stake, restaking_factor=True)
        validator_list.append(validator)
    
    return validator_list

def get_validator_nodes(validators):
    """Get all validator nodes for uniform selection."""
    nodes = []
    for validator in validators:
        # Each validator can have multiple validator nodes
        num_nodes = validator.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            for _ in range(num_nodes):
                nodes.append(validator)
    return nodes

def update_stake(participant, profit: int):
    """Update participant stake with restaking - SAME AS PBS."""
    participant.capital += profit
    
    # Apply reinvestment factor
    reinvested = int(profit * participant.reinvestment_factor)
    extracted = profit - reinvested
    # participant.capital -= extracted  # ❌ BUG: This was wrong!
    # The capital should keep the reinvested amount, only extract the non-reinvested portion
    
    # Update active stake based on validator nodes
    participant.active_stake = VALIDATOR_THRESHOLD * (participant.capital // VALIDATOR_THRESHOLD)
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)

def transaction_number():
    """Generate transaction count like in bidding.py."""
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
        # Select validator uniformly among validator nodes (not weighted by stake)
        validator_nodes = get_validator_nodes(validators)
        if not validator_nodes:
            continue
            
        selected_validator = random.choice(validator_nodes)
        
        # Users create multiple transactions over time (like in bidding.py)
        for user in users:
            num_transactions = transaction_number()
            for _ in range(num_transactions):
                tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
                if tx:
                    user.broadcast_transactions(tx)
                    selected_validator.mempool.append(tx)
        
        # Validator selects transactions using MEV strategy (like in bidding.py)
        selected_validator.selected_transactions = selected_validator.select_transactions(block_num)
        
        for position, tx in enumerate(selected_validator.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            # Restaking: use update_stake function - SAME AS PBS
            update_stake(selected_validator, int(block_reward))
        else:
            # Non-restaking: profit is extracted, but initial stake remains
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
    print(f"Starting Corrected Restaking PoS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    print(f"Attackers: {PROPNUM // 2} validators, {USERNUM // 2} users")
    print(f"Running sequentially to avoid multiprocessing race conditions")
    
    validators = initialize_validators_with_stakes()
    users = [User(f"user_{i}", i < USERNUM // 2) for i in range(USERNUM)]
    
    start_time = time.time()
    
    all_blocks = []
    
    # Run simulation sequentially to avoid multiprocessing race conditions
    for block_num in range(BLOCKNUM):
        if block_num % 1000 == 0:
            print(f"Processing block {block_num}/{BLOCKNUM}")
        
        # Select validator uniformly among validator nodes (not weighted by stake)
        validator_nodes = get_validator_nodes(validators)
        if not validator_nodes:
            continue
            
        selected_validator = random.choice(validator_nodes)
        
        # Users create multiple transactions over time (like in bidding.py) - SAME AS PBS
        for user in users:
            num_tx = random.randint(1, 5)  # 1-5 transactions per user per block - SAME AS PBS
            for _ in range(num_tx):
                tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
                if tx:
                    user.broadcast_transactions(tx)
                    selected_validator.mempool.append(tx)
        
        # Validator selects transactions using MEV strategy (like in bidding.py)
        selected_validator.selected_transactions = selected_validator.select_transactions(block_num)
        
        for position, tx in enumerate(selected_validator.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            # Restaking: use update_stake function - SAME AS PBS
            update_stake(selected_validator, int(block_reward))
        
        # Create block data AFTER updating stakes
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
    
    # Save results like in PBS
    save_results(all_blocks, validators)
    
    return all_blocks

def save_results(block_data, validators):
    """Save results to CSV files - SAME AS PBS."""
    output_dir = "data/same_seed/restaking_pos/"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save block data
    if block_data:
        with open(f"{output_dir}restaking_pos_blocks.csv", 'w', newline='') as f:
            fieldnames = block_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(block_data)
    
    # Save stake evolution
    with open(f"{output_dir}stake_evolution.csv", 'w', newline='') as f:
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
    
    filename = f"data/same_seed/restaking_pos/restaking_pos_blocks.csv"
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