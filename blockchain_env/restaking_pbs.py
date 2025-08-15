"""PBS simulation with restaking dynamics for long-term centralization analysis."""

import gc
import os
import random
import csv
import time
import multiprocessing as mp
import numpy as np
from typing import List, Tuple, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy

import networkx as nx

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.network import build_network
from blockchain_env.transaction import Transaction

BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 50
PROPOSERNUM = 50

VALIDATOR_THRESHOLD = 32 * 10**9
TOTAL_NETWORK_STAKE = 1000 * VALIDATOR_THRESHOLD

MAX_WORKERS = mp.cpu_count()
BATCH_SIZE = 500

random.seed(16)

def initialize_network_with_stakes():
    """Initialize network with all participants doing restaking."""
    proposer_list = []
    builder_list = []
    
    stake_distribution = [
        (1, 0.45),
        (2, 0.25),
        (3, 0.15),
        (5, 0.10),
        (8, 0.05),
    ]
    
    for i in range(PROPOSERNUM):
        rand_val = random.random()
        cumulative_prob = 0
        selected_stake_multiplier = 1
        
        for stake_multiplier, probability in stake_distribution:
            cumulative_prob += probability
            if rand_val <= cumulative_prob:
                selected_stake_multiplier = stake_multiplier
                break
        
        initial_stake = VALIDATOR_THRESHOLD * selected_stake_multiplier
        proposer = Proposer(f"proposer_{i}", restaking_factor=True)  # All restaking
        proposer.capital = initial_stake
        proposer.active_stake = initial_stake
        proposer_list.append(proposer)
    
    for i in range(BUILDERNUM):
        rand_val = random.random()
        cumulative_prob = 0
        selected_stake_multiplier = 1
        
        for stake_multiplier, probability in stake_distribution:
            cumulative_prob += probability
            if rand_val <= cumulative_prob:
                selected_stake_multiplier = stake_multiplier
                break
        
        initial_stake = VALIDATOR_THRESHOLD * selected_stake_multiplier
        is_attacker = i < BUILDERNUM // 2
        builder = Builder(f"builder_{i}", is_attacker, initial_stake, restaking_factor=True)  # All restaking
        builder_list.append(builder)
    
    user_list = [User(f"user_{i}", i < USERNUM // 2) for i in range(USERNUM)]
    network = build_network(user_list, builder_list, proposer_list)
    
    return network, builder_list, proposer_list

def _extract_network_nodes(network_graph):
    """Extract users, builders, and proposers from the network graph."""
    user_nodes = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], User)]
    builder_nodes = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], Builder)]
    proposer_nodes = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], Proposer)]
    return user_nodes, builder_nodes, proposer_nodes

def _process_user_transactions(user_nodes, block_num):
    """Process user transactions for the block."""
    all_transactions = []
    
    for user in user_nodes:
        num_transactions = random.randint(0, 5)
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx = user.create_transactions(block_num)
            else:
                tx = user.launch_attack(block_num)

            if tx:
                user.broadcast_transactions(tx)
                all_transactions.append(tx)
    
    return all_transactions

def _process_builder_bids(builder_nodes, transactions, block_num):
    """Process builder bids using existing bidding mechanism."""
    builder_results = []
    
    # Distribute transactions to builders
    for i, tx in enumerate(transactions):
        builder_idx = i % len(builder_nodes)
        builder_nodes[builder_idx].mempool.append(tx)
    
    for builder in builder_nodes:
        # Use existing transaction selection logic
        selected_transactions = builder.select_transactions(block_num)
        
        if selected_transactions:
            # Use existing bidding logic
            bid_value = builder.bid(selected_transactions)
            
            builder_results.append((builder.id, selected_transactions, bid_value))
    
    return builder_results

def _process_proposer_selection_and_block_choice(proposer_nodes, builder_nodes, builder_results, block_num):
    """Process proposer selection and implement simplified builder-proposer logic."""
    if not builder_results:
        return None, None, None
    
    # All participants (builders + proposers) can be selected as proposers
    # Selection probability is proportional to their stake
    all_participants = []
    all_stakes = []
    
    # Add builders
    for builder in builder_nodes:
        all_participants.append(('builder', builder))
        all_stakes.append(builder.active_stake)
    
    # Add pure proposers
    for proposer in proposer_nodes:
        all_participants.append(('proposer', proposer))
        all_stakes.append(proposer.active_stake)
    
    # Normalize stakes to avoid zero weights
    min_stake = min(all_stakes) if all_stakes else 1
    normalized_stakes = [stake / min_stake + 0.01 for stake in all_stakes]
    
    # Select proposer based on stake-weighted probability
    selected_participant_type, selected_participant = random.choices(all_participants, weights=normalized_stakes, k=1)[0]
    
    # Handle proposer selection and block choice
    if selected_participant_type == 'builder':
        # Builder is also proposer - they build their own block and take full reward
        selected_builder = selected_participant
        
        # Check if selected builder has a block in this round
        selected_builder_has_block = any(bid[0] == selected_builder.id for bid in builder_results)
        
        if selected_builder_has_block:
            # Builder has a block - they choose their own block and get full reward
            selected_builder_bid = next(bid for bid in builder_results if bid[0] == selected_builder.id)
            winning_bid = selected_builder_bid
            winning_builder = selected_builder
            
            # Builder gets the full block value (no proposer fee)
            if selected_builder.restaking_factor:
                selected_builder.capital += winning_bid[2]
                selected_builder.active_stake = VALIDATOR_THRESHOLD * (selected_builder.capital // VALIDATOR_THRESHOLD)
            
            return winning_bid, winning_builder, selected_builder
        else:
            # Selected builder doesn't have a block - choose highest bid from others
            winning_bid = max(builder_results, key=lambda x: x[2])
            winning_builder_id = winning_bid[0]
            winning_builder = next(b for b in builder_nodes if b.id == winning_builder_id)
            
            # Award rewards: 90% to winning builder, 10% to proposer
            if winning_builder.restaking_factor:
                winning_builder.capital += winning_bid[2] * 0.9
                winning_builder.active_stake = VALIDATOR_THRESHOLD * (winning_builder.capital // VALIDATOR_THRESHOLD)
            
            if selected_builder.restaking_factor:
                selected_builder.capital += winning_bid[2] * 0.1
                selected_builder.active_stake = VALIDATOR_THRESHOLD * (selected_builder.capital // VALIDATOR_THRESHOLD)
            
            return winning_bid, winning_builder, selected_builder
        
    else:
        # Pure proposer was selected - normal auction mechanism
        selected_proposer = selected_participant
        
        # Select winning builder bid (highest bid value)
        winning_bid = max(builder_results, key=lambda x: x[2])
        winning_builder_id = winning_bid[0]
        winning_builder = next(b for b in builder_nodes if b.id == winning_builder_id)
        
        block_reward = winning_bid[2]
        proposer_reward = block_reward * 0.1  # 10% to proposer
        
        # Winning builder gets 90% of block value
        if winning_builder.restaking_factor:
            winning_builder.capital += block_reward - proposer_reward
            winning_builder.active_stake = VALIDATOR_THRESHOLD * (winning_builder.capital // VALIDATOR_THRESHOLD)
        
        # Proposer gets 10%
        if selected_proposer.restaking_factor:
            selected_proposer.capital += proposer_reward
            selected_proposer.active_stake = VALIDATOR_THRESHOLD * (selected_proposer.capital // VALIDATOR_THRESHOLD)
        
        return winning_bid, winning_builder, selected_proposer

def _create_block_data(block_num, winning_bid, winning_builder, selected_participant):
    """Create block data with restaking information."""
    if not winning_bid:
        return {}
    
    builder_id, transactions, bid_value = winning_bid
    
    for position, tx in enumerate(transactions):
        tx.position = position
        tx.included_at = block_num
    
    total_gas_fee = sum(tx.gas_fee for tx in transactions)
    total_mev_available = sum(tx.mev_potential for tx in transactions)
    
    # Determine if selected participant is a builder or proposer
    is_builder_proposer = hasattr(selected_participant, 'is_attacker')
    
    block_data = {
        "block_num": block_num,
        "builder_id": builder_id,
        "proposer_id": selected_participant.id,
        "proposer_type": "builder" if is_builder_proposer else "proposer",
        "builder_initial_stake": winning_builder.capital - sum(winning_builder.profit_history) if hasattr(winning_builder, 'profit_history') else winning_builder.capital,
        "builder_current_stake": winning_builder.capital,
        "builder_is_attacker": winning_builder.is_attacker,
        "proposer_initial_stake": selected_participant.capital - sum(selected_participant.profit_history) if hasattr(selected_participant, 'profit_history') else selected_participant.capital,
        "proposer_current_stake": selected_participant.capital,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev_available,
        "bid_value": bid_value,
        "block_reward": bid_value
    }
    
    return block_data

def process_block_batch(block_range, builder_nodes, proposer_nodes, user_nodes):
    """Process a batch of blocks efficiently."""
    start_block, end_block = block_range
    block_data_list = []
    
    for block_num in range(start_block, end_block):
        # Process user transactions
        transactions = _process_user_transactions(user_nodes, block_num)
        
        # Process builder bids
        builder_results = _process_builder_bids(builder_nodes, transactions, block_num)
        
        # Process proposer selection and block choice
        winning_bid, winning_builder, selected_proposer = _process_proposer_selection_and_block_choice(
            proposer_nodes, builder_nodes, builder_results, block_num
        )
        
        if winning_bid and winning_builder and selected_proposer:
            block_data = _create_block_data(block_num, winning_bid, winning_builder, selected_proposer)
            if block_data:
                block_data_list.append(block_data)
        
        # Clear mempools efficiently
        for builder in builder_nodes:
            builder.clear_mempool(block_num)
    
    return block_data_list

def simulate_restaking_pbs():
    """Main simulation function for restaking PBS with proper state passing between batches."""
    print(f"Starting Optimized Restaking PBS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"All participants are restaking")
    print(f"Attackers: {BUILDERNUM // 2} builders, {USERNUM // 2} users")
    print(f"Using {MAX_WORKERS} worker processes with proper state passing")
    
    network, builder_nodes, proposer_nodes = initialize_network_with_stakes()
    user_nodes, _, _ = _extract_network_nodes(network)
    
    start_time = time.time()
    
    block_batches = []
    for i in range(0, BLOCKNUM, BATCH_SIZE):
        end_block = min(i + BATCH_SIZE, BLOCKNUM)
        block_batches.append((i, end_block))
    
    print(f"Processing {len(block_batches)} batches of {BATCH_SIZE} blocks each")
    
    all_blocks = []
    
    # Process batches sequentially but with proper state passing
    for batch_idx, (start_block, end_block) in enumerate(block_batches):
        print(f"Processing batch {batch_idx + 1}/{len(block_batches)}: blocks {start_block}-{end_block}")
        
        # Process this batch
        batch_blocks = process_block_batch((start_block, end_block), builder_nodes, proposer_nodes, user_nodes)
        all_blocks.extend(batch_blocks)
        
        # Update progress
        if (batch_idx + 1) % 5 == 0:
            elapsed = time.time() - start_time
            avg_time_per_batch = elapsed / (batch_idx + 1)
            remaining_batches = len(block_batches) - (batch_idx + 1)
            estimated_remaining = remaining_batches * avg_time_per_batch
            print(f"Progress: {batch_idx + 1}/{len(block_batches)} batches completed")
            print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {estimated_remaining:.1f}s")
    
    all_blocks.sort(key=lambda x: x['block_num'])
    
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(all_blocks)} blocks")
    
    _save_block_data(all_blocks)
    
    print(f"Results saved to data/same_seed/restaking_pbs/")
    
    return all_blocks

def _save_block_data(block_data_list):
    """Save block data to CSV under data/same_seed/restaking_pbs/."""
    if not block_data_list:
        return
    
    filename = f"data/same_seed/restaking_pbs/restaking_pbs_blocks.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = block_data_list[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

if __name__ == "__main__":
    print("Optimized Restaking PBS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    simulate_restaking_pbs() 