import os
import random
import csv
import time
import multiprocessing as mp
from typing import List, Tuple, Dict, Any
from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.network import build_network
from blockchain_env.transaction import Transaction
import gc
import tracemalloc
import networkx as nx
import numpy as np

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
proposers: List[Proposer] = [Proposer(f"proposer_{i}") for i in range(PROPOSERNUM)]
builders: List[Builder] = [Builder(f"builder_{i}", False) for i in range(BUILDERNUM)]  # is_attacker will be set in simulation
users: List[User] = [User(f"user_{i}", False) for i in range(USERNUM)]  # is_attacker will be set in simulation
network: Any = build_network(users, builders, proposers)

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
metrics_filename: str = f"data/same_seed/pbs_network_p0.05/network_metrics.csv"
os.makedirs(os.path.dirname(metrics_filename), exist_ok=True)
with open(metrics_filename, 'w', newline='') as f:
    fieldnames: List[str] = ['node_id', 'avg_latency', 'degree']
    writer: csv.DictWriter = csv.DictWriter(f, fieldnames=fieldnames)
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
    elif random_number < 80:
        return 0
    elif random_number < 95:
        return 2
    else:
        return random.randint(3, 5)

def process_block(block_num: int, network: Any) -> Tuple[Dict[str, Any], List[Transaction]]:
    all_block_transactions: List[Transaction] = []

    # Get all users, builders, and proposers from the network
    users: List[User] = [data['node'] for node_id, data in network.nodes(data=True) if isinstance(data['node'], User)]
    builders: List[Builder] = [data['node'] for node_id, data in network.nodes(data=True) if isinstance(data['node'], Builder)]
    proposers: List[Proposer] = [data['node'] for node_id, data in network.nodes(data=True) if isinstance(data['node'], Proposer)]

    # Process user transactions
    for user in users:
        num_transactions: int = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx: Transaction = user.create_transactions(block_num)
            else:
                tx: Transaction = user.launch_attack(block_num)

            if tx:
                user.broadcast_transactions(tx)

    # Process builder bids
    builder_results: List[Tuple[str, List[Transaction], float]] = []
    for builder in builders:
        # Process any received messages (transactions)
        messages: List[Any] = builder.receive_messages()
        for msg in messages:
            if hasattr(builder, 'receive_transaction'):
                builder.receive_transaction(msg.content)

        selected_transactions: List[Transaction] = builder.select_transactions(block_num)
        bid_value: float = builder.bid(selected_transactions)
        builder_results.append((builder.id, selected_transactions, bid_value))

    # Process proposer bids
    winning_bid: Tuple[str, List[Transaction], float] = ("", [], 0.0)
    winning_builder: Builder = builders[0]  # Default to first builder

    for proposer in proposers:
        # Reset proposer state for new block
        proposer.reset_for_new_block()

        # Process each builder's bid
        for builder_id, transactions, bid_amount in builder_results:
            # Send bid to proposer through network
            builder: Builder = next(b for b in builders if b.id == builder_id)
            builder.send_message(proposer.id, bid_amount, block_num)

        # Process received bids
        messages: List[Any] = proposer.receive_messages()
        for msg in messages:
            proposer.receive_bid(msg.sender_id, msg.content)

        # Select winning bid
        winner: Tuple[str, float] = proposer.select_winner()
        if winner:
            winning_builder_id, winning_bid_amount = winner
            winning_bid = next(result for result in builder_results if result[0] == winning_builder_id)
            winning_builder = next(b for b in builders if b.id == winning_builder_id)
            break  # First proposer to select a winner wins

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

    # Clear mempools for all builders
    for builder in builders:
        builder.clear_mempool(block_num)

    return block_data, all_block_transactions


def simulate_pbs(num_attacker_builders: int, num_attacker_users: int) -> List[Dict[str, Any]]:
    # Set attacker status for builders and users
    for i, builder in enumerate(builders):
        builder.is_attacker = i < num_attacker_builders
    for i, user in enumerate(users):
        user.is_attacker = i < num_attacker_users

    # Initialize a fresh pool for each simulation run
    with mp.Pool(processes=num_processes) as pool:
        results: List[Tuple[Dict[str, Any], List[Transaction]]] = pool.starmap(process_block, [(block_num, network) for block_num in range(BLOCKNUM)])

    # Gather results
    block_data_list: List[Dict[str, Any]]
    all_transactions: List[Transaction]
    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]

    # Save transaction data to CSV
    transaction_filename: str = f"data/same_seed/pbs_network_p0.05/pbs_transactions_builders{num_attacker_builders}_users{num_attacker_users}.csv"
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)
    with open(transaction_filename, 'w', newline='') as f:
        if all_transactions:
            fieldnames: List[str] = list(all_transactions[0].to_dict().keys())
            writer: csv.DictWriter = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tx in all_transactions:
                writer.writerow(tx.to_dict())

    # Save block data to a separate CSV
    block_filename: str = f"data/same_seed/pbs_network_p0.05/pbs_block_data_builders{num_attacker_builders}_users{num_attacker_users}.csv"
    with open(block_filename, 'w', newline='') as f:
        fieldnames: List[str] = [
            'block_num',
            'builder_id',
            'total_gas_fee',
            'total_mev'
        ]
        writer: csv.DictWriter = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

    # Run garbage collection to clear memory
    gc.collect()

    return block_data_list

def run_simulation_in_process(num_attacker_builders: int, num_attacker_users: int) -> None:
    """Run each simulation in a separate process to avoid state leakage."""
    process: mp.Process = mp.Process(target=simulate_pbs, args=(num_attacker_builders, num_attacker_users))
    process.start()
    process.join()  # Wait for the process to complete

if __name__ == "__main__":
    tracemalloc.start()  # Start tracking memory usage, for diagnostic purposes

    for num_attacker_builders in range(1, BUILDERNUM + 1):
        for num_attacker_users in range(USERNUM + 1):
            start_time: float = time.time()
            run_simulation_in_process(num_attacker_builders, num_attacker_users)
            end_time: float = time.time()
            print(f"Simulation with {num_attacker_builders} attacker builders and {num_attacker_users} attacker users completed in {end_time - start_time:.2f} seconds")
