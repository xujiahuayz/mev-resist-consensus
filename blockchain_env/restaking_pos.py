"""PoS simulation with restaking dynamics for long-term centralization analysis."""

import random
import os
import csv
import time
import multiprocessing as mp
import numpy as np
from typing import List, Dict, Any, Tuple

from blockchain_env.user import User
from blockchain_env.builder import Builder

# Constants for long-term analysis
BLOCKNUM = 10000  # Extended to 10,000 blocks for convergence analysis
BLOCK_CAP = 100
USERNUM = 100
PROPNUM = 50

# Restaking parameters
VALIDATOR_THRESHOLD: int = 32 * 10**9  # 32 ETH in gwei
TOTAL_NETWORK_STAKE: int = 100 * VALIDATOR_THRESHOLD  # 1000 active validators
REINVESTMENT_PROBABILITY: float = 0.5  # 50% chance of restaking

# Seed for reproducibility
random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores = os.cpu_count()
num_processes = max(num_cores - 1, 1)

class RestakingValidator(Builder):
    """Validator with restaking dynamics for PoS consensus."""
    
    def __init__(self, validator_id: str, is_attacker: bool, initial_stake: int = 0):
        super().__init__(validator_id, is_attacker)
        self.capital = initial_stake  # Total accumulated capital
        self.active_stake = initial_stake  # Active stake (only full validator units)
        self.reinvestment_factor = random.random() < REINVESTMENT_PROBABILITY  # γ_i ∈ {0,1}
        self.profit_history = []  # Track profits over time
        self.stake_history = []  # Track stake evolution
        self.selected_transactions = []  # Transactions selected for this block
        
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
    
    def get_stake_ratio(self) -> float:
        """Get ratio of this participant's stake to total network stake."""
        return self.active_stake / TOTAL_NETWORK_STAKE
    
    def receive_block_reward(self, block_reward: int) -> None:
        """Receive block reward and update stake."""
        self.update_stake(block_reward)

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
        validator = RestakingValidator(f"validator_{i}", False, initial_stake)
        validators.append(validator)
    
    return validators

def calculate_centralization_metrics(validators: List[RestakingValidator]) -> Dict[str, float]:
    """Calculate centralization metrics including Gini coefficient."""
    
    stakes = [v.active_stake for v in validators]
    total_stake = sum(stakes)
    
    if total_stake == 0:
        return {'gini': 0.0, 'concentration_ratio': 0.0, 'herfindahl_index': 0.0}
    
    # Calculate stake ratios
    stake_ratios = [s / total_stake for s in stakes]
    
    # Gini coefficient
    sorted_ratios = sorted(stake_ratios)
    n = len(sorted_ratios)
    gini = (2 * sum(i * ratio for i, ratio in enumerate(sorted_ratios, 1)) - (n + 1) * sum(sorted_ratios)) / (n * sum(sorted_ratios))
    
    # Concentration ratio (top 5 participants)
    sorted_stakes = sorted(stakes, reverse=True)
    top_5_stake = sum(sorted_stakes[:5])
    concentration_ratio = top_5_stake / total_stake
    
    # Herfindahl-Hirschman Index
    herfindahl = sum(ratio**2 for ratio in stake_ratios)
    
    return {
        'gini': gini,
        'concentration_ratio': concentration_ratio,
        'herfindahl_index': herfindahl,
        'total_participants': len(validators),
        'total_stake': total_stake
    }

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

def process_block(block_num: int, 
                 users: List[User], 
                 validators: List[RestakingValidator]) -> Tuple[Dict[str, Any], List[Any]]:
    """Process a single block with restaking dynamics."""
    
    # Pre-sample validators for each block using stake-weighted selection
    # Higher stake = higher chance of being selected
    validator_weights = [v.get_stake_ratio() + 0.01 for v in validators]  # Add small constant to avoid zero weights
    selected_validator = random.choices(validators, weights=validator_weights, k=1)[0]
    
    all_block_transactions = []
    
    # Process user transactions
    for user in users:
        num_transactions = transaction_number()
        for _ in range(num_transactions):
            tx = user.launch_attack(block_num) if user.is_attacker else user.create_transactions(block_num)
            if tx:
                user.broadcast_transactions(tx)
    
    # Selected validator processes transactions
    selected_validator.selected_transactions = selected_validator.select_transactions(BLOCK_CAP)
    
    # Assign transaction positions and inclusion times
    for position, tx in enumerate(selected_validator.selected_transactions):
        tx.position = position
        tx.included_at = block_num
    
    all_block_transactions.extend(selected_validator.selected_transactions)
    
    # Calculate block rewards
    total_gas_fee = sum(tx.gas_fee for tx in selected_validator.selected_transactions)
    total_mev = sum(tx.mev_potential for tx in selected_validator.selected_transactions)
    
    # Award block reward to selected validator
    block_reward = total_gas_fee + total_mev
    selected_validator.receive_block_reward(block_reward)
    
    # Calculate centralization metrics
    centralization_metrics = calculate_centralization_metrics(validators)
    
    # Create block data with restaking information
    block_data = {
        "block_num": block_num,
        "validator_id": selected_validator.id,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev,
        "block_reward": block_reward,
        "validator_stake": selected_validator.active_stake,
        "validator_stake_ratio": selected_validator.get_stake_ratio(),
        "validator_validator_count": selected_validator.get_validator_count(),
        "validator_reinvestment_factor": selected_validator.reinvestment_factor,
        "gini_coefficient": centralization_metrics['gini'],
        "concentration_ratio": centralization_metrics['concentration_ratio'],
        "herfindahl_index": centralization_metrics['herfindahl_index'],
        "total_network_stake": centralization_metrics['total_stake']
    }
    
    # Clear validators' mempools
    for validator in validators:
        validator.clear_mempool(block_num)
    
    return block_data, selected_validator.selected_transactions

def simulate_restaking_pos(attacker_validators: int, attacker_users: int) -> List[Dict[str, Any]]:
    """Main simulation function for restaking PoS."""
    
    print(f"Starting Restaking PoS Simulation")
    print(f"Blocks: {BLOCKNUM}, Attackers: {attacker_validators} validators, {attacker_users} users")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    
    # Initialize validators with stakes
    validators = initialize_validators_with_stakes()
    users = [User(f"user_{i}", i < attacker_users) for i in range(USERNUM)]
    
    # Set attacker status for validators
    for i, validator in enumerate(validators):
        validator.is_attacker = i < attacker_validators
    
    # Run simulation
    start_time = time.time()
    
    all_blocks = []
    all_transactions = []
    
    for block_num in range(BLOCKNUM):
        block_data, transactions = process_block(block_num, users, validators)
        all_blocks.append(block_data)
        all_transactions.extend(transactions)
        
        # Progress indicator for long simulations
        if block_num % 1000 == 0:
            print(f"Processed block {block_num}/{BLOCKNUM}")
    
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    
    # Save results
    _save_transaction_data(all_transactions, attacker_validators, attacker_users)
    _save_block_data(all_blocks, attacker_validators, attacker_users)
    _save_stake_evolution(validators, attacker_validators, attacker_users)
    
    # Print final centralization metrics
    final_metrics = calculate_centralization_metrics(validators)
    
    print(f"\nFinal Centralization Metrics:")
    print(f"Gini Coefficient: {final_metrics['gini']:.4f}")
    print(f"Top 5 Concentration Ratio: {final_metrics['concentration_ratio']:.4f}")
    print(f"Herfindahl Index: {final_metrics['herfindahl_index']:.4f}")
    print(f"Total Network Stake: {final_metrics['total_stake'] / 10**9:.1f} ETH")
    
    return all_blocks

def _save_transaction_data(all_transactions: List[Any], 
                          attacker_validators: int, 
                          attacker_users: int) -> None:
    """Save transaction data to CSV."""
    if not all_transactions:
        return
    
    filename = f"data/restaking_pos/restaking_pos_transactions_validators{attacker_validators}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if all_transactions:
            fieldnames = all_transactions[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in all_transactions:
                writer.writerow(tx.to_dict())

def _save_block_data(block_data_list: List[Dict[str, Any]], 
                    attacker_validators: int, 
                    attacker_users: int) -> None:
    """Save block data to CSV."""
    if not block_data_list:
        return
    
    filename = f"data/restaking_pos/restaking_pos_blocks_validators{attacker_validators}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = block_data_list[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

def _save_stake_evolution(validators: List[RestakingValidator], 
                         attacker_validators: int, 
                         attacker_users: int) -> None:
    """Save stake evolution data for analysis."""
    filename = f"data/restaking_pos/restaking_pos_stake_evolution_validators{attacker_validators}_users{attacker_users}.csv"
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

def run_simulation_in_process(attacker_validators: int, attacker_users: int) -> None:
    """Run simulation in a separate process."""
    try:
        simulate_restaking_pos(attacker_validators, attacker_users)
    except Exception as e:
        print(f"Error in simulation: {e}")

def run_parallel_simulations(attacker_configs: List[Tuple[int, int]]) -> None:
    """Run multiple simulations in parallel."""
    print(f"Running {len(attacker_configs)} simulations in parallel using {num_processes} processes")
    
    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(run_simulation_in_process, attacker_configs)
    
    print("All parallel simulations completed!")

if __name__ == "__main__":
    # Example usage
    print("Restaking PoS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    # Run simulation with different attacker configurations
    attacker_configs = [
        (0, 0),   # No attackers
        (5, 10),  # 5 attacker validators, 10 attacker users
        (10, 20), # 10 attacker validators, 20 attacker users
    ]
    
    # Run simulations sequentially
    for validator_attackers, user_attackers in attacker_configs:
        print(f"\nRunning simulation with {validator_attackers} attacker validators and {user_attackers} attacker users")
        simulate_restaking_pos(validator_attackers, user_attackers)
    
    # Optionally run parallel simulations
    # run_parallel_simulations(attacker_configs) 