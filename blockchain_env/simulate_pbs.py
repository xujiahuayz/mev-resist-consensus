"""PBS simulation module for blockchain environment."""

import gc
import os
import random
import csv
import time
import tracemalloc
import multiprocessing as mp
from typing import List, Tuple, Dict, Any

import networkx as nx

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.network import build_network
from blockchain_env.transaction import Transaction

# Constants
BLOCKNUM: int = 1000
BLOCK_CAP: int = 100
USERNUM: int = 50
BUILDERNUM: int = 20
PROPOSERNUM: int = 20

random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores: int = os.cpu_count()
num_processes: int = max(num_cores - 1, 1)  # Use all cores except one, but at least one

# Create network participants and build network once
proposer_list: List[Proposer] = [Proposer(f"proposer_{i}") for i in range(PROPOSERNUM)]
builder_list: List[Builder] = [Builder(f"builder_{i}", False) for i in range(BUILDERNUM)]  # is_attacker will be set in simulation
user_list: List[User] = [User(f"user_{i}", False) for i in range(USERNUM)]  # is_attacker will be set in simulation
network: Any = build_network(user_list, builder_list, proposer_list)

# Calculate and save network metrics once
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

# Save network metrics to CSV
metrics_filename: str = "data/same_seed/pbs_network_p0.05/network_metrics.csv"
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
    """Process user transactions for the block."""
    for user in user_nodes:
        num_transactions: int = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx: Transaction = user.create_transactions(block_num)
            else:
                tx: Transaction = user.launch_attack(block_num)

            if tx:
                user.broadcast_transactions(tx)

def _process_builder_bids(builder_nodes: List[Builder], block_num: int) -> List[Tuple[str, List[Transaction], float]]:
    """Process builder bids and return results."""
    builder_results: List[Tuple[str, List[Transaction], float]] = []
    for builder in builder_nodes:
        # Process any received messages (transactions)
        messages: List[Any] = builder.receive_messages()
        for msg in messages:
            if hasattr(builder, 'receive_transaction'):
                builder.receive_transaction(msg.content)

        selected_transactions: List[Transaction] = builder.select_transactions(block_num)
        bid_value: float = builder.bid(selected_transactions)
        builder_results.append((builder.id, selected_transactions, bid_value))
    return builder_results

def _process_proposer_bids(proposer_nodes: List[Proposer], builder_nodes: List[Builder], builder_results: List[Tuple[str, List[Transaction], float]], block_num: int) -> Tuple[Tuple[str, List[Transaction], float], Builder]:
    """Process proposer bids and return winning bid and builder."""
    winning_bid: Tuple[str, List[Transaction], float] = ("", [], 0.0)
    winning_builder: Builder = builder_nodes[0]  # Default to first builder

    for proposer in proposer_nodes:
        # Reset proposer state for new block
        proposer.reset_for_new_block()

        # Process each builder's bid
        for builder_id, _transactions, bid_amount in builder_results:
            # Send bid to proposer through network
            builder: Builder = next(b for b in builder_nodes if b.id == builder_id)
            builder.send_message(proposer.id, bid_amount, block_num)

        # Process received bids
        messages: List[Any] = proposer.receive_messages()
        for msg in messages:
            proposer.receive_bid(msg.sender_id, msg.content)

        # Select winning bid
        winner: Tuple[str, float] = proposer.select_winner()
        if winner:
            winning_builder_id, _ = winner
            winning_bid = next(result for result in builder_results if result[0] == winning_builder_id)
            winning_builder = next(b for b in builder_nodes if b.id == winning_builder_id)
            break  # First proposer to select a winner wins

    return winning_bid, winning_builder

def _create_block_data(block_num: int, winning_bid: Tuple[str, List[Transaction], float], winning_builder: Builder) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Create block data and transactions from winning bid."""
    all_block_transactions: List[Transaction] = []
    
    if winning_bid[0]:
        for position, tx in enumerate(winning_bid[1]):
            tx.position = position
            tx.included_at = block_num

        all_block_transactions.extend(winning_bid[1])
        total_gas_fee: float = sum(tx.gas_fee for tx in winning_bid[1])
        total_mev: float = sum(tx.mev_potential for tx in winning_bid[1])

        block_data: Dict[str, Any] = {
            "block_num": block_num,
            "builder_id": winning_builder.id,
            "total_gas_fee": total_gas_fee,
            "total_mev": total_mev
        }
    else:
        block_data: Dict[str, Any] = {
            "block_num": block_num,
            "builder_id": "",
            "total_gas_fee": 0,
            "total_mev": 0
        }

    return block_data, all_block_transactions

def process_block(block_num: int, network_graph: Any) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Process a single block in the simulation."""
    # Extract network nodes
    user_nodes, builder_nodes, proposer_nodes = _extract_network_nodes(network_graph)
    
    # Process user transactions
    _process_user_transactions(user_nodes, block_num)
    
    # Process builder bids
    builder_results = _process_builder_bids(builder_nodes, block_num)
    
    # Process proposer bids
    winning_bid, winning_builder = _process_proposer_bids(proposer_nodes, builder_nodes, builder_results, block_num)
    
    # Create block data
    block_data, all_block_transactions = _create_block_data(block_num, winning_bid, winning_builder)
    
    # Clear mempools for all builders
    for builder in builder_nodes:
        builder.clear_mempool(block_num)

    return block_data, all_block_transactions


def _set_attacker_status(attacker_builder_count: int, attacker_user_count: int) -> None:
    """Set attacker status for builders and users."""
    for i, builder in enumerate(builder_list):
        builder.is_attacker = i < attacker_builder_count
    for i, user in enumerate(user_list):
        user.is_attacker = i < attacker_user_count

def _run_simulation_blocks() -> Tuple[List[Dict[str, Any]], List[Transaction]]:
    """Run simulation blocks and return results."""
    with mp.Pool(processes=num_processes) as pool:
        results: List[Tuple[Dict[str, Any], List[Transaction]]] = pool.starmap(process_block, [(block_num, network) for block_num in range(BLOCKNUM)])

    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]
    return list(block_data_list), all_transactions

def _save_transaction_data(all_transactions: List[Transaction], attacker_builder_count: int, attacker_user_count: int) -> None:
    """Save transaction data to CSV."""
    transaction_filename: str = f"data/same_seed/pbs_network_p0.05/pbs_transactions_builders{attacker_builder_count}_users{attacker_user_count}.csv"
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)
    with open(transaction_filename, 'w', newline='', encoding='utf-8') as csv_file:
        if all_transactions:
            tx_fieldnames: List[str] = list(all_transactions[0].to_dict().keys())
            tx_writer: csv.DictWriter = csv.DictWriter(csv_file, fieldnames=tx_fieldnames)
            tx_writer.writeheader()
            for tx in all_transactions:
                tx_writer.writerow(tx.to_dict())

def _save_block_data(block_data_list: List[Dict[str, Any]], attacker_builder_count: int, attacker_user_count: int) -> None:
    """Save block data to CSV."""
    block_filename: str = f"data/same_seed/pbs_network_p0.05/pbs_block_data_builders{attacker_builder_count}_users{attacker_user_count}.csv"
    with open(block_filename, 'w', newline='', encoding='utf-8') as csv_file:
        block_fieldnames: List[str] = [
            'block_num',
            'builder_id',
            'total_gas_fee',
            'total_mev'
        ]
        block_writer: csv.DictWriter = csv.DictWriter(csv_file, fieldnames=block_fieldnames)
        block_writer.writeheader()
        for block_data in block_data_list:
            block_writer.writerow(block_data)

def simulate_pbs(attacker_builder_count: int, attacker_user_count: int) -> List[Dict[str, Any]]:
    """Simulate PBS with given attacker counts."""
    # Set attacker status for builders and users
    _set_attacker_status(attacker_builder_count, attacker_user_count)

    # Run simulation blocks
    block_data_list, all_transactions = _run_simulation_blocks()

    # Save transaction data to CSV
    _save_transaction_data(all_transactions, attacker_builder_count, attacker_user_count)

    # Save block data to a separate CSV
    _save_block_data(block_data_list, attacker_builder_count, attacker_user_count)

    # Run garbage collection to clear memory
    gc.collect()

    return block_data_list

def run_simulation_in_process(attacker_builder_count: int, attacker_user_count: int) -> None:
    """Run each simulation in a separate process to avoid state leakage."""
    process: mp.Process = mp.Process(target=simulate_pbs, args=(attacker_builder_count, attacker_user_count))
    process.start()
    process.join()  # Wait for the process to complete

if __name__ == "__main__":
    tracemalloc.start()  # Start tracking memory usage, for diagnostic purposes

    for builder_count in range(1, BUILDERNUM + 1):
        for user_count in range(USERNUM + 1):
            start_time: float = time.time()
            run_simulation_in_process(builder_count, user_count)
            end_time: float = time.time()
            print(f"Simulation with {builder_count} attacker builders and {user_count} attacker users completed in {end_time - start_time:.2f} seconds")
