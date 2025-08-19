"""Optimized PBS simulation with restaking dynamics and parallel batch processing."""

import os
import random
import csv
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from typing import List, Dict, Any, Tuple

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.transaction import Transaction

# Constants
BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 100
BUILDERNUM = 50
PROPOSERNUM = 50
MAX_ROUNDS = 24

VALIDATOR_THRESHOLD = 32 * 10**9  # 32 ETH in gwei
MIN_VALIDATOR_NODES = 1

# Optimization settings
MAX_WORKERS = min(mp.cpu_count() - 1, 8)  # Leave 1 core free, max 8 workers
BATCH_SIZE = 1000  # Process 1000 blocks per batch

random.seed(16)

def create_participants_with_config(attacker_builders, attacker_users):
    """Create participants with configurable attacker counts."""
    # Create builders
    builders = []
    for i in range(BUILDERNUM):
        is_attacker = i < attacker_builders
        
        stake_distribution = [
            (1, 0.45),   # 1 node (32 ETH)
            (2, 0.25),   # 2 nodes (64 ETH)
            (3, 0.15),   # 3 nodes (96 ETH)
            (5, 0.10),   # 5 nodes (160 ETH)
            (8, 0.05),   # 8 nodes (256 ETH)
        ]
        
        rand_val = random.random()
        cumulative_prob = 0
        selected_stake_multiplier = 1
        
        for stake_multiplier, probability in stake_distribution:
            cumulative_prob += probability
            if rand_val <= cumulative_prob:
                selected_stake_multiplier = stake_multiplier
                break
        
        initial_stake = VALIDATOR_THRESHOLD * selected_stake_multiplier
        
        builder = Builder(f"builder_{i}", is_attacker)
        
        # Add restaking properties
        builder.capital = initial_stake
        builder.active_stake = initial_stake
        builder.initial_stake = initial_stake
        builder.reinvestment_factor = random.random()
        builder.profit_history = []
        builder.stake_history = [builder.capital]
        builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
        builder.bid_history = []
        builder.mempool = []
        builder.selected_transactions = []
        
        builders.append(builder)
    
    # Create proposers
    proposers = []
    for i in range(PROPOSERNUM):
        proposer = Proposer(f"proposer_{i}")
        
        stake_distribution = [
            (1, 0.45),   # 1 node (32 ETH)
            (2, 0.25),   # 2 nodes (64 ETH)
            (3, 0.15),   # 3 nodes (96 ETH)
            (5, 0.10),   # 5 nodes (160 ETH)
            (8, 0.05),   # 8 nodes (256 ETH)
        ]
        
        rand_val = random.random()
        cumulative_prob = 0
        selected_stake_multiplier = 1
        
        for stake_multiplier, probability in stake_distribution:
            cumulative_prob += probability
            if rand_val <= cumulative_prob:
                selected_stake_multiplier = stake_multiplier
                break
        
        initial_stake = VALIDATOR_THRESHOLD * selected_stake_multiplier
        
        # Add restaking properties
        proposer.capital = initial_stake
        proposer.active_stake = initial_stake
        proposer.initial_stake = initial_stake
        proposer.reinvestment_factor = random.random()
        proposer.profit_history = []
        proposer.stake_history = [proposer.capital]
        
        proposers.append(proposer)
    
    # Create users with configurable attacker count
    users = []
    for i in range(USERNUM):
        is_attacker = i < attacker_users
        user = User(f"user_{i}", is_attacker)
        users.append(user)
    
    return builders, proposers, users

def get_validator_nodes(participants):
    """Get all validator nodes for uniform selection - every 32 ETH is a node."""
    nodes = []
    for participant in participants:
        num_nodes = participant.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            # Add one entry per validator node for uniform selection
            for _ in range(num_nodes):
                nodes.append(participant)
    return nodes

def update_stake(participant, profit: int):
    """Update participant stake with restaking."""
    participant.capital += profit
    
    # Update active stake based on validator nodes (32 ETH increments)
    participant.active_stake = VALIDATOR_THRESHOLD * (participant.capital // VALIDATOR_THRESHOLD)
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)

def calculate_block_value(builder, selected_transactions):
    """Calculate block value exactly like in bidding.py."""
    if not selected_transactions:
        return 0.0
    
    # Gas fees from all transactions
    gas_fee = sum(tx.gas_fee for tx in selected_transactions)
    
    # MEV value only for attackers who initiated attacks
    mev_value = 0.0
    if builder.is_attacker:
        for tx in selected_transactions:
            # Check if this transaction targets another transaction (attack transaction)
            if hasattr(tx, 'target_tx') and tx.target_tx:
                # MEV value comes from the target transaction's potential
                mev_value += tx.target_tx.mev_potential
    
    return gas_fee + mev_value

def process_block_optimized(builders, proposers, users, block_num):
    """Optimized block processing with minimal object creation."""
    
    # 1. Generate and distribute transactions efficiently
    for user in users:
        tx_count = random.randint(1, 5)
        for _ in range(tx_count):
            if user.is_attacker:
                tx = user.launch_attack(block_num)
            else:
                tx = user.create_transactions(block_num)
            
            if tx:
                # Distribute to all builders
                for builder in builders:
                    builder.mempool.append(tx)
    
    # 2. Get validator nodes and select proposer uniformly
    all_staking_participants = builders + proposers
    validator_nodes = get_validator_nodes(all_staking_participants)
    
    if not validator_nodes:
        return None
    
    selected_proposer = random.choice(validator_nodes)
    
    # 3. Process based on proposer type
    if selected_proposer in builders:
        # Builder-proposer case: Direct building
        winning_builder = selected_proposer
        winning_builder.selected_transactions = winning_builder.select_transactions(block_num)
        
        if not winning_builder.selected_transactions:
            return None
        
        block_value = calculate_block_value(winning_builder, winning_builder.selected_transactions)
        
        if block_value > 0:
            update_stake(winning_builder, int(block_value))
        
        winning_bid = block_value
        proposer_type = "builder"
        
    else:
        # Pure proposer case: Run optimized auction
        auction_end = random.randint(20, MAX_ROUNDS)
        
        # Pre-select transactions for all builders once
        builder_selections = []
        for builder in builders:
            builder.selected_transactions = builder.select_transactions(block_num)
            block_value = calculate_block_value(builder, builder.selected_transactions)
            builder_selections.append((builder, block_value))
        
        # Run simplified auction
        last_round_bids = [0.0] * len(builders)
        
        for round_num in range(auction_end):
            round_bids = []
            
            for i, (builder, block_value) in enumerate(builder_selections):
                if block_value > 0:
                    # Simplified bidding for performance
                    if builder.strategy == "reactive":
                        highest_last_bid = max(last_round_bids, default=0.0)
                        bid = min(highest_last_bid * 1.1, block_value) if highest_last_bid > 0 else block_value * 0.5
                    elif builder.strategy == "late_enter":
                        bid = 0.0 if round_num < 18 else min(1.05 * max(last_round_bids, default=0.0), block_value)
                    else:
                        bid = 0.5 * block_value
                    
                    bid = max(0, min(bid, block_value))
                else:
                    bid = 0.0
                
                builder.bid_history.append(bid)
                round_bids.append(bid)
            
            last_round_bids = round_bids
        
        # Select winner
        if not last_round_bids or max(last_round_bids) == 0:
            return None
        
        winning_idx = last_round_bids.index(max(last_round_bids))
        winning_builder, final_block_value = builder_selections[winning_idx]
        winning_bid = last_round_bids[winning_idx]
        
        # Award rewards: proposer gets bid, builder gets (block_value - bid)
        proposer_reward = int(winning_bid)
        builder_reward = int(max(0, final_block_value - winning_bid))
        
        update_stake(selected_proposer, proposer_reward)
        if builder_reward > 0:
            update_stake(winning_builder, builder_reward)
        
        proposer_type = "proposer"
    
    # 4. Clear mempools efficiently with included transactions
    if winning_builder and winning_builder.selected_transactions:
        included_tx_ids = {tx.id for tx in winning_builder.selected_transactions}
        
        for builder in builders:
            builder.mempool[:] = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
        
        # Set transaction metadata
        for position, tx in enumerate(winning_builder.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        # Create block data
        total_gas = sum(tx.gas_fee for tx in winning_builder.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in winning_builder.selected_transactions 
                       if hasattr(tx, 'target_tx') and tx.target_tx and winning_builder.is_attacker)
        
        return {
            "block_num": block_num,
            "builder_id": winning_builder.id,
            "proposer_id": selected_proposer.id,
            "proposer_type": proposer_type,
            "builder_stake": winning_builder.active_stake,
            "proposer_stake": selected_proposer.active_stake,
            "builder_is_attacker": winning_builder.is_attacker,
            "total_gas_fee": total_gas,
            "total_mev_available": total_mev,
            "bid_value": winning_bid,
            "block_value": calculate_block_value(winning_builder, winning_builder.selected_transactions),
            "num_transactions": len(winning_builder.selected_transactions)
        }
    
    return None

def process_block_batch(args):
    """Process a batch of blocks in parallel."""
    start_block, end_block, builders, proposers, users = args
    batch_blocks = []
    
    # Set random seed for this batch to ensure reproducibility
    random.seed(16 + start_block)
    
    for block_num in range(start_block, end_block):
        block_data = process_block_optimized(builders, proposers, users, block_num)
        if block_data:
            batch_blocks.append(block_data)
    
    return batch_blocks

def create_participant_copies(builders, proposers, users):
    """Create deep copies of participants for parallel processing."""
    builder_copies = []
    for builder in builders:
        new_builder = Builder(builder.id, builder.is_attacker)
        new_builder.capital = builder.capital
        new_builder.active_stake = builder.active_stake
        new_builder.initial_stake = builder.initial_stake
        new_builder.reinvestment_factor = builder.reinvestment_factor
        new_builder.profit_history = []
        new_builder.stake_history = [new_builder.capital]
        new_builder.strategy = builder.strategy
        new_builder.bid_history = []
        new_builder.mempool = []
        new_builder.selected_transactions = []
        builder_copies.append(new_builder)
    
    proposer_copies = []
    for proposer in proposers:
        new_proposer = Proposer(proposer.id)
        new_proposer.capital = proposer.capital
        new_proposer.active_stake = proposer.active_stake
        new_proposer.initial_stake = proposer.initial_stake
        new_proposer.reinvestment_factor = proposer.reinvestment_factor
        new_proposer.profit_history = []
        new_proposer.stake_history = [new_proposer.capital]
        proposer_copies.append(new_proposer)
    
    user_copies = [User(user.id, user.is_attacker) for user in users]
    
    return builder_copies, proposer_copies, user_copies

def run_optimized_simulation(attacker_builders, attacker_users):
    """Run simulation with optimized parallel processing."""
    print(f"\nRunning optimized simulation: {attacker_builders} attacker builders, {attacker_users} attacker users")
    print(f"Using {MAX_WORKERS} parallel workers with batch size {BATCH_SIZE}")
    
    # Create participants
    builders, proposers, users = create_participants_with_config(attacker_builders, attacker_users)
    
    # Create batches for parallel processing
    batches = []
    for start_block in range(0, BLOCKNUM, BATCH_SIZE):
        end_block = min(start_block + BATCH_SIZE, BLOCKNUM)
        # Each batch gets independent copies to avoid state conflicts
        batch_builders, batch_proposers, batch_users = create_participant_copies(builders, proposers, users)
        batches.append((start_block, end_block, batch_builders, batch_proposers, batch_users))
    
    start_time = time.time()
    all_blocks = []
    
    # Process batches in parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {executor.submit(process_block_batch, batch): batch for batch in batches}
        
        completed_batches = 0
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            start_block, end_block, _, _, _ = batch
            try:
                batch_result = future.result()
                all_blocks.extend(batch_result)
                completed_batches += 1
                
                # Progress update
                progress = completed_batches / len(batches) * 100
                elapsed = time.time() - start_time
                eta = elapsed / completed_batches * (len(batches) - completed_batches) / 60 if completed_batches > 0 else 0
                
                print(f"Completed batch {completed_batches}/{len(batches)} ({progress:.1f}%) | "
                      f"Blocks {start_block}-{end_block-1} | "
                      f"Results: {len(batch_result)} | "
                      f"ETA: {eta:.1f} min")
                
            except Exception as e:
                print(f"Batch {start_block}-{end_block-1} failed: {e}")
    
    # Sort blocks by block number
    all_blocks.sort(key=lambda x: x['block_num'])
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Simulation completed in {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Speed: {BLOCKNUM/total_time:.1f} blocks/second")
    print(f"Successful blocks: {len(all_blocks)}/{BLOCKNUM}")
    
    # Save results with original naming convention
    save_results(all_blocks, builders, proposers, attacker_builders, attacker_users)
    
    return all_blocks

def get_validator_nodes(participants):
    """Get all validator nodes for uniform selection - every 32 ETH is a node."""
    nodes = []
    for participant in participants:
        num_nodes = participant.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            # Add one entry per validator node for uniform selection
            for _ in range(num_nodes):
                nodes.append(participant)
    return nodes

def update_stake(participant, profit: int):
    """Update participant stake with restaking."""
    participant.capital += profit
    
    # Update active stake based on validator nodes (32 ETH increments)
    participant.active_stake = VALIDATOR_THRESHOLD * (participant.capital // VALIDATOR_THRESHOLD)
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)

def calculate_block_value(builder, selected_transactions):
    """Calculate block value exactly like in bidding.py."""
    if not selected_transactions:
        return 0.0
    
    # Gas fees from all transactions
    gas_fee = sum(tx.gas_fee for tx in selected_transactions)
    
    # MEV value only for attackers who initiated attacks
    mev_value = 0.0
    if builder.is_attacker:
        for tx in selected_transactions:
            # Check if this transaction targets another transaction (attack transaction)
            if hasattr(tx, 'target_tx') and tx.target_tx:
                # MEV value comes from the target transaction's potential
                mev_value += tx.target_tx.mev_potential
    
    return gas_fee + mev_value

def process_block_optimized(builders, proposers, users, block_num):
    """Optimized block processing with minimal object creation."""
    
    # 1. Generate and distribute transactions efficiently
    for user in users:
        tx_count = random.randint(1, 5)
        for _ in range(tx_count):
            if user.is_attacker:
                tx = user.launch_attack(block_num)
            else:
                tx = user.create_transactions(block_num)
            
            if tx:
                # Distribute to all builders
                for builder in builders:
                    builder.mempool.append(tx)
    
    # 2. Get validator nodes and select proposer uniformly
    all_staking_participants = builders + proposers
    validator_nodes = get_validator_nodes(all_staking_participants)
    
    if not validator_nodes:
        return None
    
    selected_proposer = random.choice(validator_nodes)
    
    # 3. Process based on proposer type
    if selected_proposer in builders:
        # Builder-proposer case: Direct building
        winning_builder = selected_proposer
        winning_builder.selected_transactions = winning_builder.select_transactions(block_num)
        
        if not winning_builder.selected_transactions:
            return None
        
        block_value = calculate_block_value(winning_builder, winning_builder.selected_transactions)
        
        if block_value > 0:
            update_stake(winning_builder, int(block_value))
        
        winning_bid = block_value
        proposer_type = "builder"
        
    else:
        # Pure proposer case: Run optimized auction
        auction_end = random.randint(20, MAX_ROUNDS)
        
        # Pre-select transactions for all builders once
        builder_selections = []
        for builder in builders:
            builder.selected_transactions = builder.select_transactions(block_num)
            block_value = calculate_block_value(builder, builder.selected_transactions)
            builder_selections.append((builder, block_value))
        
        # Run simplified auction
        last_round_bids = [0.0] * len(builders)
        
        for round_num in range(auction_end):
            round_bids = []
            
            for i, (builder, block_value) in enumerate(builder_selections):
                if block_value > 0:
                    # Simplified bidding for performance
                    if builder.strategy == "reactive":
                        highest_last_bid = max(last_round_bids, default=0.0)
                        bid = min(highest_last_bid * 1.1, block_value) if highest_last_bid > 0 else block_value * 0.5
                    elif builder.strategy == "late_enter":
                        bid = 0.0 if round_num < 18 else min(1.05 * max(last_round_bids, default=0.0), block_value)
                    else:
                        bid = 0.5 * block_value
                    
                    bid = max(0, min(bid, block_value))
                else:
                    bid = 0.0
                
                builder.bid_history.append(bid)
                round_bids.append(bid)
            
            last_round_bids = round_bids
        
        # Select winner
        if not last_round_bids or max(last_round_bids) == 0:
            return None
        
        winning_idx = last_round_bids.index(max(last_round_bids))
        winning_builder, final_block_value = builder_selections[winning_idx]
        winning_bid = last_round_bids[winning_idx]
        
        # Award rewards: proposer gets bid, builder gets (block_value - bid)
        proposer_reward = int(winning_bid)
        builder_reward = int(max(0, final_block_value - winning_bid))
        
        update_stake(selected_proposer, proposer_reward)
        if builder_reward > 0:
            update_stake(winning_builder, builder_reward)
        
        proposer_type = "proposer"
    
    # 4. Clear mempools efficiently with included transactions
    if winning_builder and winning_builder.selected_transactions:
        included_tx_ids = {tx.id for tx in winning_builder.selected_transactions}
        
        for builder in builders:
            # In-place filtering for efficiency
            builder.mempool[:] = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
        
        # Set transaction metadata
        for position, tx in enumerate(winning_builder.selected_transactions):
            tx.position = position
            tx.included_at = block_num
        
        # Create block data
        total_gas = sum(tx.gas_fee for tx in winning_builder.selected_transactions)
        total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in winning_builder.selected_transactions 
                       if hasattr(tx, 'target_tx') and tx.target_tx and winning_builder.is_attacker)
        
        return {
            "block_num": block_num,
            "builder_id": winning_builder.id,
            "proposer_id": selected_proposer.id,
            "proposer_type": proposer_type,
            "builder_stake": winning_builder.active_stake,
            "proposer_stake": selected_proposer.active_stake,
            "builder_is_attacker": winning_builder.is_attacker,
            "total_gas_fee": total_gas,
            "total_mev_available": total_mev,
            "bid_value": winning_bid,
            "block_value": calculate_block_value(winning_builder, winning_builder.selected_transactions),
            "num_transactions": len(winning_builder.selected_transactions)
        }
    
    return None

def save_results(block_data, builders, proposers, attacker_builders, attacker_users):
    """Save results to CSV files using SAME directory structure as PoS."""
    # Use SAME output directory as PoS simulation
    output_dir = "data/same_seed/pos_visible80/"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save block data with PBS prefix to distinguish from PoS
    if block_data:
        block_filename = f"{output_dir}pbs_restaking_block_data_builders{attacker_builders}_users{attacker_users}.csv"
        with open(block_filename, 'w', newline='') as f:
            fieldnames = block_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(block_data)
        print(f"Saved {len(block_data)} blocks to {block_filename}")
    
    # Save stake evolution with PBS prefix
    stake_filename = f"{output_dir}pbs_restaking_stake_evolution_builders{attacker_builders}_users{attacker_users}.csv"
    with open(stake_filename, 'w', newline='') as f:
        fieldnames = ['participant_id', 'participant_type', 'is_attacker', 'reinvestment_factor',
                     'initial_stake', 'final_stake', 'total_profit', 'num_validator_nodes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for builder in builders:
            writer.writerow({
                'participant_id': builder.id,
                'participant_type': 'builder',
                'is_attacker': builder.is_attacker,
                'reinvestment_factor': builder.reinvestment_factor,
                'initial_stake': builder.initial_stake,
                'final_stake': builder.active_stake,
                'total_profit': sum(builder.profit_history),
                'num_validator_nodes': builder.active_stake // VALIDATOR_THRESHOLD
            })
        
        for proposer in proposers:
            writer.writerow({
                'participant_id': proposer.id,
                'participant_type': 'proposer',
                'is_attacker': False,
                'reinvestment_factor': proposer.reinvestment_factor,
                'initial_stake': proposer.initial_stake,
                'final_stake': proposer.active_stake,
                'total_profit': sum(proposer.profit_history),
                'num_validator_nodes': proposer.active_stake // VALIDATOR_THRESHOLD
            })
    
    print(f"Stake evolution saved to {stake_filename}")

def print_final_statistics(builders, proposers):
    """Print final simulation statistics."""
    all_participants = builders + proposers
    
    # Calculate stake distribution
    total_stake = sum(p.active_stake for p in all_participants)
    builder_stake = sum(b.active_stake for b in builders)
    proposer_stake = sum(p.active_stake for p in proposers)
    
    # Calculate validator node counts
    total_validator_nodes = sum(p.active_stake // VALIDATOR_THRESHOLD for p in all_participants)
    builder_validator_nodes = sum(b.active_stake // VALIDATOR_THRESHOLD for b in builders)
    proposer_validator_nodes = sum(p.active_stake // VALIDATOR_THRESHOLD for p in proposers)
    
    print(f"\nFinal Statistics:")
    print(f"Total stake: {total_stake / 10**9:.1f} ETH")
    print(f"Builder stake: {builder_stake / 10**9:.1f} ETH ({builder_stake/total_stake*100:.1f}%)")
    print(f"Proposer stake: {proposer_stake / 10**9:.1f} ETH ({proposer_stake/total_stake*100:.1f}%)")
    print(f"Total validator nodes: {total_validator_nodes}")
    print(f"Builder validator nodes: {builder_validator_nodes} ({builder_validator_nodes/total_validator_nodes*100:.1f}%)")
    print(f"Proposer validator nodes: {proposer_validator_nodes} ({proposer_validator_nodes/total_validator_nodes*100:.1f}%)")

if __name__ == "__main__":
    print("Starting PBS Restaking Simulation - SAME PARAMETERS AS POS")
    print("=" * 80)
    
    # Run single simulation with same parameters as PoS
    attacker_builders = BUILDERNUM // 2  # Half are attackers
    attacker_users = USERNUM // 2        # Half are attackers
    run_optimized_simulation(attacker_builders, attacker_users)