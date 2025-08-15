"""PoS simulation with restaking dynamics for long-term centralization analysis."""

import random
import os
import csv
import time
import multiprocessing as mp
import numpy as np
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from blockchain_env.user import User
from blockchain_env.network import Node

# Constants for optimized analysis
BLOCKNUM = 1000  # Reduced from 10,000 for faster execution
BLOCK_CAP = 100
USERNUM = 50
PROPNUM = 20

# Restaking parameters
VALIDATOR_THRESHOLD: int = 32 * 10**9  # 32 ETH in gwei
TOTAL_NETWORK_STAKE: int = 1000 * VALIDATOR_THRESHOLD  # 1000 active validators
REINVESTMENT_PROBABILITY: float = 0.5  # 50% chance of restaking

# Optimization parameters
MAX_WORKERS = 8  # Number of worker threads
BATCH_SIZE = 100  # Process blocks in batches

# Seed for reproducibility
random.seed(16)

class RestakingValidator(Node):
    """Validator with restaking dynamics for PoS consensus."""
    
    def __init__(self, validator_id: str, is_attacker: bool, initial_stake: int = 0):
        super().__init__(validator_id)
        self.capital = initial_stake  # Total accumulated capital
        self.active_stake = initial_stake  # Active stake (only full validator units)
        self.reinvestment_factor = random.random() < REINVESTMENT_PROBABILITY  # γ_i ∈ {0,1}
        self.profit_history = []  # Track profits over time
        self.stake_history = []  # Track stake evolution
        self.selected_transactions = []  # Transactions selected for this block
        self.is_attacker = is_attacker
        self.mempool = []
        
    def update_stake(self, profit: int) -> None:
        """Update capital and active stake based on profit and reinvestment."""
        # Add profit to capital
        self.capital += profit
        
        # Apply reinvestment factor
        if self.reinvestment_factor:
            # Reinvest profit (compound)
            reinvested_profit = profit
        else:
            # Extract all profit (no compounding)
            reinvested_profit = 0
        
        # Update capital with reinvestment
        self.capital += reinvested_profit
        
        # Update active stake only when crossing threshold boundaries
        # s_i(ℓ+1) = (32 × 10^9) × ⌊k_i(ℓ+1) / (32 × 10^9)⌋
        self.active_stake = VALIDATOR_THRESHOLD * (self.capital // VALIDATOR_THRESHOLD)
        
        # Record history
        self.profit_history.append(profit)
        self.stake_history.append(self.active_stake)
    
    def get_validator_count(self) -> int:
        """Get number of active validators this participant can run."""
        return self.active_stake // VALIDATOR_THRESHOLD
    
    def get_restaking_stake_ratio(self) -> float:
        """Get ratio of this participant's stake to total network stake."""
        return self.active_stake / TOTAL_NETWORK_STAKE
    
    def receive_block_reward(self, block_reward: int) -> None:
        """Receive block reward and update stake."""
        self.update_stake(block_reward)
    
    def select_transactions(self, max_transactions: int) -> List[Any]:
        """Select transactions from mempool."""
        # Simple selection - take first max_transactions
        return self.mempool[:max_transactions]
    
    def clear_mempool(self, block_num: int) -> None:
        """Clear mempool after block processing."""
        self.mempool = []

def initialize_validators_with_stakes() -> List[RestakingValidator]:
    """Initialize validators with realistic stake distribution."""
    
    validators = []
    
    for i in range(PROPNUM):
        # Realistic stake distribution: some have 32 ETH, some have multiples
        initial_stake = random.choice([
            VALIDATOR_THRESHOLD,      # 32 ETH
            VALIDATOR_THRESHOLD * 2,  # 64 ETH
            VALIDATOR_THRESHOLD * 5,  # 160 ETH
            VALIDATOR_THRESHOLD * 10, # 320 ETH
            VALIDATOR_THRESHOLD * 15, # 480 ETH
        ])
        # Set half of validators as attackers
        is_attacker = i < PROPNUM // 2
        validator = RestakingValidator(f"validator_{i}", is_attacker, initial_stake)
        validators.append(validator)
    
    return validators

def transaction_number() -> int:
    """Generate random transaction count for users."""
    random_number = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def process_block_batch(block_range: Tuple[int, int], 
                       users: List[User], 
                       validators: List[RestakingValidator]) -> List[Dict[str, Any]]:
    """Process a batch of blocks for multithreading."""
    
    block_data_list = []
    start_block, end_block = block_range
    
    for block_num in range(start_block, end_block):
        # Pre-sample validators for each block using stake-weighted selection
        # Higher stake = higher chance of being selected
        validator_weights = [v.get_restaking_stake_ratio() + 0.01 for v in validators]
        selected_validator = random.choices(validators, weights=validator_weights, k=1)[0]
        
        # Process user transactions using stable period data
        for user in users:
            num_transactions = transaction_number()
            for _ in range(num_transactions):
                tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
                if tx:
                    user.broadcast_transactions(tx)
                    # Add to selected validator's mempool
                    selected_validator.mempool.append(tx)
        
        # Selected validator processes transactions
        selected_validator.selected_transactions = selected_validator.select_transactions(BLOCK_CAP)
        
        # Assign transaction positions and inclusion times
        for position, tx in enumerate(selected_validator.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        # Calculate block rewards
        total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
        total_mev = sum(tx.mev_potential for tx in selected_validator.selected_transactions)
        
        # Award block reward to selected validator
        block_reward = total_gas_fee + total_mev
        selected_validator.receive_block_reward(block_reward)
        
        # Create block data with restaking information
        block_data = {
            "block_num": block_num,
            "validator_id": selected_validator.id,
            "validator_stake": selected_validator.active_stake,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev,
            "block_reward": block_reward,
            "validator_reinvestment_factor": selected_validator.reinvestment_factor,
            "validator_validator_count": selected_validator.get_validator_count()
        }
        
        block_data_list.append(block_data)
        
        # Clear validators' mempools
        for validator in validators:
            validator.clear_mempool(block_num)
    
    return block_data_list

def simulate_restaking_pos() -> List[Dict[str, Any]]:
    """Main simulation function for restaking PoS with multithreading."""
    
    print(f"Starting Optimized Restaking PoS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    print(f"Attackers: {PROPNUM // 2} validators, {USERNUM // 2} users")
    print(f"Using {MAX_WORKERS} worker threads")
    
    # Initialize validators with stakes
    validators = initialize_validators_with_stakes()
    
    # Create users with half as attackers
    users = [User(f"user_{i}", i < USERNUM // 2) for i in range(USERNUM)]
    
    # Run simulation with multithreading
    start_time = time.time()
    
    # Create block batches for parallel processing
    block_batches = []
    for i in range(0, BLOCKNUM, BATCH_SIZE):
        end_block = min(i + BATCH_SIZE, BLOCKNUM)
        block_batches.append((i, end_block))
    
    print(f"Processing {len(block_batches)} batches of {BATCH_SIZE} blocks each")
    
    all_blocks = []
    
    # Process blocks in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all batch jobs
        future_to_batch = {
            executor.submit(process_block_batch, batch, users, validators): batch 
            for batch in block_batches
        }
        
        # Collect results as they complete
        completed_batches = 0
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                batch_blocks = future.result()
                all_blocks.extend(batch_blocks)
                completed_batches += 1
                
                # Progress indicator
                if completed_batches % 5 == 0:
                    print(f"Completed {completed_batches}/{len(block_batches)} batches")
                    
            except Exception as exc:
                print(f'Batch {batch} generated an exception: {exc}')
    
    # Sort blocks by block number to ensure correct order
    all_blocks.sort(key=lambda x: x['block_num'])
    
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(all_blocks)} blocks")
    
    # Save results
    _save_block_data(all_blocks)
    _save_stake_evolution(validators)
    
    return all_blocks

def _save_block_data(block_data_list: List[Dict[str, Any]]) -> None:
    """Save block data to CSV under data/same_seed/restaking_pos/."""
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

def _save_stake_evolution(validators: List[RestakingValidator]) -> None:
    """Save stake evolution data for analysis."""
    filename = f"data/same_seed/restaking_pos/restaking_pos_stake_evolution.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['participant_id', 'participant_type', 'is_attacker', 'reinvestment_factor', 
                     'initial_stake', 'final_stake', 'final_capital', 'total_profit', 'validator_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Save validator data
        for validator in validators:
            writer.writerow({
                'participant_id': validator.id,
                'participant_type': 'validator',
                'is_attacker': validator.is_attacker,
                'reinvestment_factor': validator.reinvestment_factor,
                'initial_stake': validator.stake_history[0] if validator.stake_history else 0,
                'final_stake': validator.active_stake,
                'final_capital': validator.capital,
                'total_profit': sum(validator.profit_history),
                'validator_count': validator.get_validator_count()
            })

if __name__ == "__main__":
    # Example usage
    print("Optimized Restaking PoS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    # Run simulation
    simulate_restaking_pos() 