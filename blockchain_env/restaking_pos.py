"""PoS simulation with restaking dynamics for long-term centralization analysis."""

import random
import os
import csv
import time
import multiprocessing as mp
import numpy as np
from typing import List, Dict, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy

from blockchain_env.user import User
from blockchain_env.validator import Validator

BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 50
PROPNUM = 50

VALIDATOR_THRESHOLD = 32 * 10**9
TOTAL_NETWORK_STAKE = 1000 * VALIDATOR_THRESHOLD
REINVESTMENT_PROBABILITY = 0.5

MAX_WORKERS = mp.cpu_count()
BATCH_SIZE = 500

random.seed(16)

def initialize_validators_with_stakes():
    """Initialize validators with all doing restaking."""
    validator_list = []
    
    stake_distribution = [
        (1, 0.45),
        (2, 0.25),
        (3, 0.15),
        (5, 0.10),
        (8, 0.05),
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
        validator_weights = [v.active_stake / TOTAL_NETWORK_STAKE + 0.01 for v in validators]
        selected_validator = random.choices(validators, weights=validator_weights, k=1)[0]
        
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
        total_mev = sum(tx.mev_potential for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            # Restaking: add profit to capital, keep accumulating
            selected_validator.capital += block_reward
            # Update active stake based on total accumulated capital
            selected_validator.active_stake = VALIDATOR_THRESHOLD * (selected_validator.capital // VALIDATOR_THRESHOLD)
        else:
            # Non-restaking: profit is extracted, but initial stake remains
            # Only update active stake if they want to withdraw some stake
            pass
        
        block_data = {
            "block_num": block_num,
            "validator_id": selected_validator.id,
            "validator_capital": selected_validator.capital,
            "validator_restaking_factor": selected_validator.restaking_factor,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev,
            "block_reward": block_reward,
            "is_attacker": selected_validator.is_attacker
        }
        
        block_data_list.append(block_data)
        
        for validator in validators:
            validator.clear_mempool(block_num)
    
    return block_data_list

def simulate_restaking_pos():
    print(f"Starting Sequential Restaking PoS Simulation")
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
        
        # Process single block
        validator_weights = [v.active_stake / TOTAL_NETWORK_STAKE + 0.01 for v in validators]
        selected_validator = random.choices(validators, weights=validator_weights, k=1)[0]
        
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
        total_mev = sum(tx.mev_potential for tx in selected_validator.selected_transactions)
        block_reward = total_gas_fee + total_mev
        
        if selected_validator.restaking_factor:
            # Restaking: add profit to capital, keep accumulating
            selected_validator.capital += block_reward
            # Update active stake based on total accumulated capital
            selected_validator.active_stake = VALIDATOR_THRESHOLD * (selected_validator.capital // VALIDATOR_THRESHOLD)
        
        block_data = {
            "block_num": block_num,
            "validator_id": selected_validator.id,
            "validator_capital": selected_validator.capital,
            "validator_restaking_factor": selected_validator.restaking_factor,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev,
            "block_reward": block_reward,
            "is_attacker": selected_validator.is_attacker
        }
        
        all_blocks.append(block_data)
        
        for validator in validators:
            validator.clear_mempool(block_num)
    
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(all_blocks)} blocks")
    
    _save_block_data(all_blocks)
    
    return all_blocks

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
    print("Optimized Restaking PoS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    simulate_restaking_pos() 