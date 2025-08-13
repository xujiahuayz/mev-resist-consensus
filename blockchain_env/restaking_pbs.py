"""PBS simulation with restaking dynamics for long-term centralization analysis."""

import gc
import os
import random
import csv
import time
import tracemalloc
import multiprocessing as mp
import numpy as np
from typing import List, Tuple, Dict, Any

import networkx as nx

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.network import build_network
from blockchain_env.transaction import Transaction

# Constants - same as normal simulation for consistency
BLOCKNUM: int = 1000  # Same as simulate_pbs.py
BLOCK_CAP: int = 100
USERNUM: int = 50
BUILDERNUM: int = 20
PROPOSERNUM: int = 20

# Restaking parameters
VALIDATOR_THRESHOLD: int = 32 * 10**9  # 32 ETH in gwei
TOTAL_NETWORK_STAKE: int = 1000 * VALIDATOR_THRESHOLD  # 1000 active validators
REINVESTMENT_PROBABILITY: float = 0.5  # 50% chance of restaking

random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores: int = os.cpu_count()
num_processes: int = max(num_cores - 1, 1)

# Create network participants and build network once - same as normal simulation
proposer_list: List[Proposer] = []
for i in range(PROPOSERNUM):
    # Set restaking factor: True for restaking, False for no restaking
    restaking_factor = random.random() < REINVESTMENT_PROBABILITY
    # If no reinvestment, set restaking factor to 0 to ensure simulation runs properly
    if not restaking_factor:
        restaking_factor = 0
    
    proposer = Proposer(f"proposer_{i}", restaking_factor=restaking_factor)
    proposer_list.append(proposer)

builder_list: List[Builder] = []
for i in range(BUILDERNUM):
    # Set restaking factor: True for restaking, False for no restaking
    restaking_factor = random.random() < REINVESTMENT_PROBABILITY
    # If no reinvestment, set restaking factor to 0 to ensure simulation runs properly
    if not restaking_factor:
        restaking_factor = 0
    
    builder = Builder(f"builder_{i}", False, initial_stake=32*10**9, restaking_factor=restaking_factor)
    builder_list.append(builder)

user_list: List[User] = []
for i in range(USERNUM):
    # Set restaking factor: True for restaking, False for no restaking
    restaking_factor = random.random() < REINVESTMENT_PROBABILITY
    # If no reinvestment, set restaking factor to 0 to ensure simulation runs properly
    if not restaking_factor:
        restaking_factor = 0
    
    user = User(f"user_{i}", False, restaking_factor=restaking_factor)
    user_list.append(user)

network: Any = build_network(user_list, builder_list, proposer_list)

# Calculate and save network metrics once - same as normal simulation
network_metrics = {}
for node_id in network.nodes():
    node = network.nodes[node_id]['node']
    # Calculate average latency to all other nodes
    latencies = []
    for other_id in network.nodes():
        if other_id != node_id:
            try:
                # Get shortest path latency
                path = nx.shortest_path(network, node_id, other_id, weight='weight')
                path_latency = sum(network[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                latencies.append(path_latency)
            except nx.NetworkXNoPath:
                continue
    network_metrics[node_id] = {
        'avg_latency': sum(latencies) / len(latencies) if latencies else float('inf'),
        'degree': network.degree(node_id)
    }

# Save network metrics to CSV - same as normal simulation
metrics_filename: str = "data/same_seed/restaking_pbs_network_p0.05/network_metrics.csv"
os.makedirs(os.path.dirname(metrics_filename), exist_ok=True)
with open(metrics_filename, 'w', newline='', encoding='utf-8') as file:
    fieldnames: List[str] = ['node_id', 'avg_latency', 'degree']
    writer: csv.DictWriter = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for node_id, metrics in network_metrics.items():
        writer.writerow({
            'node_id': node_id,
            'avg_latency': metrics['avg_latency'],
            'degree': metrics['degree']
        })

def transaction_number() -> int:
    """Same transaction number function as normal simulation."""
    random_number: int = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def _extract_network_nodes(network_graph: Any) -> Tuple[List[User], List[Builder], List[Proposer]]:
    """Extract users, builders, and proposers from the network graph."""
    user_nodes: List[User] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], User)]
    builder_nodes: List[Builder] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], Builder)]
    proposer_nodes: List[Proposer] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], Proposer)]
    return user_nodes, builder_nodes, proposer_nodes

def _process_user_transactions(user_nodes: List[User], block_num: int) -> None:
    """Process user transactions for the block - same as normal simulation."""
    for user in user_nodes:
        num_transactions: int = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx: Transaction = user.create_transactions(block_num)
            else:
                tx: Transaction = user.launch_attack(block_num)

            if tx:
                user.broadcast_transactions(tx)

def _process_builder_bids(builder_nodes: List[Builder], block_num: int) -> List[float]:
    """Process builder bids for the block."""
    bids: List[float] = []
    for builder in builder_nodes:
        builder.select_transactions(block_num)
        block_value: float = builder.calculate_block_value()
        bid: float = builder.bid(builder.selected_transactions)
        bids.append(bid)
    return bids

def _select_winning_builder(builder_nodes: List[Builder], bids: List[float]) -> Tuple[Builder, float]:
    """Select the winning builder based on bids."""
    winning_bid_index: int = bids.index(max(bids))
    winning_builder: Builder = builder_nodes[winning_bid_index]
    winning_bid: float = bids[winning_bid_index]
    return winning_builder, winning_bid

def _finalize_block(winning_builder: Builder, proposer_nodes: List[Proposer], block_num: int) -> None:
    """Finalize the block and update stakes."""
    # Assign transaction positions and inclusion times
    for position, tx in enumerate(winning_builder.selected_transactions):
        tx.position = position
        tx.included_at = block_num
    
    # Calculate block rewards
    total_gas_fee = sum(tx.gas_fee for tx in winning_builder.selected_transactions)
    total_mev = sum(tx.mev_potential for tx in winning_builder.selected_transactions)
    
    # Award rewards for restaking
    block_reward = total_gas_fee + total_mev
    winning_builder.receive_block_reward(block_reward)
    
    # Award proposer reward
    if proposer_nodes:
        selected_proposer = random.choice(proposer_nodes)
        proposer_reward = total_gas_fee * 0.1  # 10% of gas fees to proposer
        selected_proposer.receive_proposer_reward(proposer_reward)
    
    # Clear mempools
    for builder in builder_list:
        builder.clear_mempool(block_num)

def process_restaking_block(block_num: int, user_nodes: List[User], builder_nodes: List[Builder], proposer_nodes: List[Proposer]) -> Dict[str, Any]:
    """Process a single block with restaking dynamics."""
    # Process user transactions
    _process_user_transactions(user_nodes, block_num)
    
    # Process builder bids
    bids = _process_builder_bids(builder_nodes, block_num)
    
    # Select winning builder
    winning_builder, winning_bid = _select_winning_builder(builder_nodes, bids)
    
    # Finalize block
    _finalize_block(winning_builder, proposer_nodes, block_num)
    
    # Calculate block metrics
    total_gas_fee = sum(tx.gas_fee for tx in winning_builder.selected_transactions)
    total_mev = sum(tx.mev_potential for tx in winning_builder.selected_transactions)
    
    # Calculate restaking metrics
    total_network_stake = sum(builder.active_stake for builder in builder_nodes)
    gini_coefficient = calculate_gini_coefficient([builder.active_stake for builder in builder_nodes])
    
    block_data = {
        "block_num": block_num,
        "builder_id": winning_builder.id,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev,
        "winning_bid": winning_bid,
        "total_network_stake": total_network_stake,
        "gini_coefficient": gini_coefficient,
        "builder_stakes": [builder.active_stake for builder in builder_nodes]
    }
    
    return block_data, winning_builder.selected_transactions

def calculate_gini_coefficient(stakes: List[int]) -> float:
    """Calculate Gini coefficient for stake distribution."""
    if not stakes or sum(stakes) == 0:
        return 0.0
    
    sorted_stakes = sorted(stakes)
    n = len(sorted_stakes)
    cumsum = np.cumsum(sorted_stakes)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

def simulate_restaking_pbs(attacker_builders: int, attacker_users: int) -> List[Dict[str, Any]]:
    """Simulate PBS with restaking dynamics."""
    # Set attacker flags
    for i, builder in enumerate(builder_list):
        builder.is_attacker = i < attacker_builders
    
    for i, user in enumerate(user_list):
        user.is_attacker = i < attacker_users
    
    # Extract nodes from network
    user_nodes, builder_nodes, proposer_nodes = _extract_network_nodes(network)
    
    # Run simulation
    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_restaking_block, 
                             [(block_num, user_nodes, builder_nodes, proposer_nodes) 
                              for block_num in range(BLOCKNUM)])
    
    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]
    
    # Save results
    save_restaking_pbs_results(block_data_list, all_transactions, attacker_builders, attacker_users)
    
    return block_data_list

def save_restaking_pbs_results(block_data_list: List[Dict], all_transactions: List[Transaction], attacker_builders: int, attacker_users: int) -> None:
    """Save restaking PBS results to CSV files."""
    # Define filenames
    transaction_filename = f"data/same_seed/restaking_pbs_visible80/restaking_pbs_transactions_builders{attacker_builders}_users{attacker_users}.csv"
    block_filename = f"data/same_seed/restaking_pbs_visible80/restaking_pbs_block_data_builders{attacker_builders}_users{attacker_users}.csv"
    
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)
    
    # Save transaction data
    if all_transactions:
        with open(transaction_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = all_transactions[0].to_dict().keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in all_transactions:
                writer.writerow(tx.to_dict())
    
    # Save block data
    with open(block_filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['block_num', 'builder_id', 'total_gas_fee', 'total_mev_available', 
                     'winning_bid', 'total_network_stake', 'gini_coefficient', 'builder_stakes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

if __name__ == "__main__":
    for num_attacker_builders in range(BUILDERNUM + 1):
        for num_attacker_users in range(USERNUM + 1):
            start_time = time.time()
            print(f"Running restaking PBS simulation with {num_attacker_builders} attacker builders and {num_attacker_users} attacker users...")
            
            # Run the simulation
            simulate_restaking_pbs(num_attacker_builders, num_attacker_users)
            
            # Calculate and print the time taken
            end_time = time.time()
            round_time = end_time - start_time
            print(f"Restaking PBS simulation completed in {round_time:.2f} seconds")
            print(f"Results saved for {num_attacker_builders} attacker builders and {num_attacker_users} attacker users")
            print("-" * 80) 