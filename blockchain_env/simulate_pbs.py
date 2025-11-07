"""PBS simulation module for blockchain environment."""

import gc
import math
import os
import random
import csv
import time
import tracemalloc
import multiprocessing as mp
from typing import List, Tuple, Dict, Any, Optional

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
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

# Create network participants (no network graph needed - using direct probability distribution)
# Set uniform transaction inclusion probability for all builders (between 0.4 and 0.8)
# This ensures fair distribution - no builder receives everything
uniform_builder_probability: float = random.uniform(0.4, 0.8)

proposer_list: List[Proposer] = [Proposer(f"proposer_{i}") for i in range(PROPOSERNUM)]
builder_list: List[Builder] = [Builder(f"builder_{i}", False, transaction_inclusion_probability=uniform_builder_probability) for i in range(BUILDERNUM)]  # is_attacker will be set in simulation
user_list: List[User] = [User(f"user_{i}", False) for i in range(USERNUM)]  # is_attacker will be set in simulation

# All receivers (builders and proposers) that should receive transactions
all_receivers: List[Any] = builder_list + proposer_list

def transaction_number() -> int:
    random_number: int = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def _get_all_nodes() -> Tuple[List[User], List[Builder], List[Proposer]]:
    """Get all users, builders, and proposers (no network graph needed)."""
    return user_list, builder_list, proposer_list

def _process_user_transactions(user_nodes: List[User], block_num: int, receivers: List[Any]) -> None:
    """Process user transactions for the block."""
    tx_count_by_user = {}
    for user in user_nodes:
        # Process pending mempool transactions (probability-based retry)
        user.process_pending_mempool(block_num)
        
        num_transactions: int = transaction_number()
        tx_count_by_user[user.id] = num_transactions
        for _ in range(num_transactions):
            if not user.is_attacker:
                tx: Transaction = user.create_transactions(block_num)
            else:
                tx: Transaction = user.launch_attack(block_num)

            if tx:
                # Broadcast directly to all receivers (builders and proposers)
                user.broadcast_transactions(tx, receivers)

def _process_builder_bids_round(builder_nodes: List[Builder], block_num: int, round_num: int, last_round_bids: List[float]) -> List[Tuple[str, List[Transaction], float]]:
    """Process builder bids for a single round and return results."""
    builder_results: List[Tuple[str, List[Transaction], float]] = []
    round_bids: List[float] = []
    
    for builder in builder_nodes:
        # Select transactions from current mempool
        selected_transactions: List[Transaction] = builder.select_transactions(block_num)
        # Place bid based on round and last round's bids
        bid_value: float = builder.bid(selected_transactions, round_num, last_round_bids)
        round_bids.append(bid_value)
        builder_results.append((builder.id, selected_transactions, bid_value))
    
    return builder_results, round_bids

def _process_proposer_bids(proposer_nodes: List[Proposer], builder_nodes: List[Builder], builder_results: List[Tuple[str, List[Transaction], float]], block_num: int) -> Tuple[Tuple[str, List[Transaction], float], Optional[Builder], Optional[Proposer]]:
    """Select a proposer at random and choose the highest bid for the block."""
    if not builder_results:
        return ("", [], 0.0), None, None

    winning_proposer: Optional[Proposer] = random.choice(proposer_nodes) if proposer_nodes else None
    if winning_proposer:
        winning_proposer.reset_for_new_block()

    max_bid_value: float = max(result[2] for result in builder_results)
    tolerance: float = max(1e-9, max_bid_value * 1e-9)
    top_bidders: List[Tuple[str, List[Transaction], float]] = [
        result for result in builder_results if abs(result[2] - max_bid_value) <= tolerance
    ]

    winning_entry: Tuple[str, List[Transaction], float] = random.choice(top_bidders)
    winning_builder_id: str = winning_entry[0]
    winning_builder: Optional[Builder] = next((b for b in builder_nodes if b.id == winning_builder_id), None)

    if winning_proposer:
        winning_proposer.receive_bid(winning_builder_id, winning_entry[2])
        winning_proposer.end_round()

    return winning_entry, winning_builder, winning_proposer

def _create_block_data(block_num: int, winning_bid: Tuple[str, List[Transaction], float], winning_builder: Optional[Builder], winning_proposer: Optional[Proposer]) -> Tuple[Dict[str, Any], List[Transaction]]:
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
            "builder_id": winning_builder.id if winning_builder else "",
            "proposer_id": winning_proposer.id if winning_proposer else "",
            "winning_bid": winning_bid[2],
            "total_gas_fee": total_gas_fee,
            "total_mev": total_mev
        }
    else:
        block_data: Dict[str, Any] = {
            "block_num": block_num,
            "builder_id": "",
            "proposer_id": "",
            "winning_bid": 0.0,
            "total_gas_fee": 0,
            "total_mev": 0
        }

    return block_data, all_block_transactions

def process_block(block_num: int, network_graph: Any = None) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Process a single block in the simulation.
    
    Each block has 5 rounds. In each round:
    - Builders retry receiving pending transactions (with probability)
    - New user transactions are created and broadcast (only in round 0)
    - Builders select transactions and place bids (reacting to other builders' bids)
    
    Args:
        block_num: Current block number
        network_graph: Deprecated - kept for backward compatibility, not used
    """
    # Get all nodes (no network graph needed)
    user_nodes, builder_nodes, proposer_nodes = _get_all_nodes()
    
    # All receivers that should get transactions
    receivers = builder_nodes + proposer_nodes
    
    # Each block has 5 rounds
    NUM_ROUNDS_PER_BLOCK = 5
    
    # Track bids across rounds for reactive bidding
    last_round_bids: List[float] = []
    final_builder_results: List[Tuple[str, List[Transaction], float]] = []
    
    # Process rounds: in each round, retry pending transactions, then bid
    for round_num in range(NUM_ROUNDS_PER_BLOCK):
        # First, process pending mempool for all receivers (retry with probability)
        for receiver in receivers:
            receiver.process_pending_mempool(round_num)
        
        # Process user transactions (new transactions created this round)
        # Only create transactions in the first round to avoid duplicates
        if round_num == 0:
            _process_user_transactions(user_nodes, block_num, receivers)
        
        # Process builder bids for this round (builders react to last round's bids)
        builder_results, round_bids = _process_builder_bids_round(builder_nodes, block_num, round_num, last_round_bids)
        
        # Update last_round_bids for next round
        last_round_bids = round_bids
        
        # Store final results (will be overwritten each round, keeping the last)
        final_builder_results = builder_results
    
    # After all rounds, process proposer bids (select winner from final round)
    winning_bid, winning_builder, winning_proposer = _process_proposer_bids(proposer_nodes, builder_nodes, final_builder_results, block_num)
    
    # Create block data
    block_data, all_block_transactions = _create_block_data(block_num, winning_bid, winning_builder, winning_proposer)
    
    # Clear mempools for ALL participants (users, builders, proposers) instantaneously
    # This removes transactions that have been included on-chain, regardless of propagation delay
    # Note: Since builders use deepcopy, we must remove by transaction ID, not object reference
    included_tx_ids = {tx.id for tx in all_block_transactions} if all_block_transactions else set()
    
    # Remove included transactions from all users' mempools (instantaneous, no propagation delay)
    for user in user_nodes:
        user.mempool = [tx for tx in user.mempool if tx.id not in included_tx_ids]
        user.clear_mempool(block_num)  # Also clear old transactions (created_at < block_num - 5)
    
    # Remove included transactions from all builders' mempools (instantaneous, no propagation delay)
    for builder in builder_nodes:
        builder.mempool = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
        builder.clear_mempool(block_num)  # Also clear old transactions (created_at < block_num - 5)
    
    # Remove included transactions from all proposers' mempools (instantaneous, no propagation delay)
    for proposer in proposer_nodes:
        proposer.mempool = [tx for tx in proposer.mempool if tx.id not in included_tx_ids]
        proposer.clear_mempool(block_num)  # Also clear old transactions (created_at < block_num - 5)

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
        results: List[Tuple[Dict[str, Any], List[Transaction]]] = pool.starmap(process_block, [(block_num, None) for block_num in range(BLOCKNUM)])

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
            'proposer_id',
            'winning_bid',
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

    for builder_count in range(BUILDERNUM + 1):
        for user_count in range(USERNUM + 1):
            start_time: float = time.time()
            run_simulation_in_process(builder_count, user_count)
            end_time: float = time.time()
            print(f"Simulation with {builder_count} attacker builders and {user_count} attacker users completed in {end_time - start_time:.2f} seconds")
