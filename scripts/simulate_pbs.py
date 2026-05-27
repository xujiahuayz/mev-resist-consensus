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

import pandas as pd

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.transaction import Transaction
from blockchain_env.empirical_metrics import ordering_inversions_from_tx_df
from blockchain_env.sim_config import BLOCKS_PER_SIM, USERS, BUILDERS, PROPOSERS, NETWORK_P
from blockchain_env.network import build_network

# Constants — sourced from sim_config (single source of truth across scripts)
BLOCKNUM: int = BLOCKS_PER_SIM
BLOCK_CAP: int = 100
USERNUM: int = USERS
BUILDERNUM: int = BUILDERS
PROPOSERNUM: int = PROPOSERS

random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores: int = os.cpu_count()
num_processes: int = max(num_cores - 1, 1)  # Use all cores except one, but at least one

# Create network participants
proposer_list: List[Proposer] = [Proposer(f"proposer_{i}") for i in range(PROPOSERNUM)]
builder_list: List[Builder] = [Builder(f"builder_{i}", False) for i in range(BUILDERNUM)]
user_list: List[User] = [User(f"user_{i}", False) for i in range(USERNUM)]

# Build Erdős–Rényi graph and set each node's transaction-visibility probability
# from its realized degree: better-connected nodes see more mempool transactions.
_er_graph = build_network(user_list, builder_list, proposer_list, p=NETWORK_P)
_n_total = USERNUM + BUILDERNUM + PROPOSERNUM
for _node in user_list + builder_list + proposer_list:
    _deg = _er_graph.degree[_node.id]
    _node.transaction_inclusion_probability = _deg / (_n_total - 1) if _n_total > 1 else 1.0

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

MAX_AUCTION_ROUNDS: int = 24  # Full slot duration per EIP-7732 (0.5 s × 24 = 12 s)

def _process_block_adaptive(
    block_num: int,
    proposer: Any,
    commit_round: int,
) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Process one block with adaptive auction duration.

    Runs all MAX_AUCTION_ROUNDS rounds so the proposer can observe bids beyond
    commit_round. The winner is selected from the highest bid at commit_round;
    bids in later rounds are recorded in proposer.all_observed_bids and used by
    proposer.adjust_auction_duration to adapt commit_round for the next block.

    Args:
        block_num:    Current block number.
        proposer:     Pre-selected proposer for this block (already reset).
        commit_round: Number of rounds after which the winner is committed (T_s).
    """
    user_nodes, builder_nodes, proposer_nodes = _get_all_nodes()
    receivers = builder_nodes + proposer_nodes

    last_round_bids: List[float] = []
    committed_results: List[Tuple[str, List[Transaction], float]] = []

    for round_num in range(MAX_AUCTION_ROUNDS):
        for receiver in receivers:
            receiver.process_pending_mempool(round_num)

        if round_num == 0:
            _process_user_transactions(user_nodes, block_num, receivers)

        builder_results, round_bids = _process_builder_bids_round(
            builder_nodes, block_num, round_num, last_round_bids
        )

        # Proposer records the highest bid each round for adaptive T_s tracking
        if round_bids:
            proposer.receive_bid("max_bid", max(round_bids))
        proposer.end_round()

        # Commit winner at T_s; rounds beyond T_s are observed only
        if round_num == commit_round - 1:
            committed_results = builder_results

        last_round_bids = round_bids

    # Select winner from the committed round's results
    if committed_results:
        max_bid_value: float = max(r[2] for r in committed_results)
        tolerance: float = max(1e-9, max_bid_value * 1e-9)
        top_bidders = [r for r in committed_results if abs(r[2] - max_bid_value) <= tolerance]
        winning_entry = random.choice(top_bidders)
        winning_builder = next((b for b in builder_nodes if b.id == winning_entry[0]), None)
    else:
        winning_entry = ("", [], 0.0)
        winning_builder = None

    block_data, all_block_transactions = _create_block_data(
        block_num, winning_entry, winning_builder, proposer
    )

    included_tx_ids = {tx.id for tx in all_block_transactions} if all_block_transactions else set()
    for user in user_nodes:
        user.mempool = [tx for tx in user.mempool if tx.id not in included_tx_ids]
        user.clear_mempool(block_num)
    for builder in builder_nodes:
        builder.mempool = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
        builder.clear_mempool(block_num)
    for prop in proposer_nodes:
        prop.mempool = [tx for tx in prop.mempool if tx.id not in included_tx_ids]
        prop.clear_mempool(block_num)

    return block_data, all_block_transactions


def process_block(block_num: int, network_graph: Any = None) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Process a single block (parallel-compatible, fixed commit_round=12).

    Kept for backward compatibility with pool.starmap callers. The main simulation
    now uses _run_simulation_blocks_adaptive (sequential) which calls
    _process_block_adaptive with the proposer's adaptive T_s.

    Args:
        block_num: Current block number
        network_graph: Deprecated - not used
    """
    proposer = random.choice(proposer_list)
    proposer.reset_for_new_block()
    return _process_block_adaptive(block_num, proposer, commit_round=12)


def _set_attacker_status(attacker_builder_count: int, attacker_user_count: int) -> None:
    """Set attacker status for builders and users."""
    for i, builder in enumerate(builder_list):
        builder.is_attacker = i < attacker_builder_count
    for i, user in enumerate(user_list):
        user.is_attacker = i < attacker_user_count

def _run_simulation_blocks(
    pool_initializer: Optional[Any] = None,
    pool_initargs: Optional[tuple] = None,
) -> Tuple[List[Dict[str, Any]], List[Transaction]]:
    """Run simulation blocks in parallel (fixed commit_round=12, no adaptive T_s)."""
    pool_kw: Dict[str, Any] = {"processes": num_processes}
    if pool_initializer is not None:
        pool_kw["initializer"] = pool_initializer
        pool_kw["initargs"] = pool_initargs or ()
    with mp.Pool(**pool_kw) as pool:
        results: List[Tuple[Dict[str, Any], List[Transaction]]] = pool.starmap(process_block, [(block_num, None) for block_num in range(BLOCKNUM)])

    block_data_list, all_transactions = zip(*results)
    all_transactions = [tx for block_txs in all_transactions for tx in block_txs]
    return list(block_data_list), all_transactions


def _run_simulation_blocks_adaptive(
    pool_initializer: Optional[Any] = None,
    pool_initargs: Optional[tuple] = None,
) -> Tuple[List[Dict[str, Any]], List[Transaction]]:
    """Run simulation blocks sequentially with adaptive auction duration (T_s mechanism).

    Each block pre-selects a proposer that observes all MAX_AUCTION_ROUNDS rounds
    and commits the winner at T_s. After each block, proposer.adjust_auction_duration
    updates T_s for the next block based on whether competitive bids arrived before
    or after the previous commitment round, implementing:

        T_s = T_{s-1} + 1  if any bid > b_w arrived after round T_{s-1}
        T_s = T_{s-1} - 1  if any bid > b_w arrived only before round T_{s-1}
        T_s = T_{s-1}      otherwise
    """
    if pool_initializer is not None:
        pool_initializer(*(pool_initargs or ()))

    T_s: int = 12  # Initial commit round; adapts within [1, 24] across blocks
    prev_winning_bid: Optional[Tuple[str, float]] = None
    prev_end_round: Optional[int] = None

    block_data_list: List[Dict[str, Any]] = []
    all_transactions: List[Transaction] = []

    for block_num in range(BLOCKNUM):
        proposer = random.choice(proposer_list)
        proposer.reset_for_new_block()
        proposer.max_rounds = T_s

        block_data, block_txs = _process_block_adaptive(block_num, proposer, T_s)

        # Adapt T_s for the next block: proposer inspects bids from this block
        # against the previous block's winning bid and commitment round
        proposer.adjust_auction_duration(prev_winning_bid, prev_end_round)
        T_s = proposer.max_rounds

        winning_bid_amount: float = block_data.get("winning_bid", 0.0)
        prev_winning_bid = (block_data.get("builder_id", ""), winning_bid_amount)
        prev_end_round = T_s

        block_data_list.append(block_data)
        all_transactions.extend(block_txs)

    return block_data_list, all_transactions

def _save_transaction_data(
    all_transactions: List[Transaction],
    attacker_builder_count: int,
    attacker_user_count: int,
    output_dir: Optional[str] = None,
) -> None:
    """Save transaction data to CSV."""
    base: str = output_dir if output_dir else "data/same_seed/pbs_network_p0.05"
    transaction_filename: str = os.path.join(base, f"pbs_transactions_builders{attacker_builder_count}_users{attacker_user_count}.csv")
    os.makedirs(os.path.dirname(transaction_filename), exist_ok=True)
    with open(transaction_filename, 'w', newline='', encoding='utf-8') as csv_file:
        if all_transactions:
            tx_fieldnames: List[str] = list(all_transactions[0].to_dict().keys())
            tx_writer: csv.DictWriter = csv.DictWriter(csv_file, fieldnames=tx_fieldnames)
            tx_writer.writeheader()
            for tx in all_transactions:
                tx_writer.writerow(tx.to_dict())

def _save_block_data(
    block_data_list: List[Dict[str, Any]],
    attacker_builder_count: int,
    attacker_user_count: int,
    output_dir: Optional[str] = None,
) -> None:
    """Save block data to CSV."""
    base: str = output_dir if output_dir else "data/same_seed/pbs_network_p0.05"
    block_filename: str = os.path.join(base, f"pbs_block_data_builders{attacker_builder_count}_users{attacker_user_count}.csv")
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


def _save_block_inversions(
    all_transactions: List[Any],
    attacker_builder_count: int,
    attacker_user_count: int,
    output_dir: Optional[str] = None,
) -> None:
    """Save per-block ordering inversions — commensurable with empirical ordering_inversions.csv."""
    base: str = output_dir if output_dir else "data/same_seed/pbs_network_p0.05"
    inv_filename: str = os.path.join(
        base, f"pbs_block_inversions_builders{attacker_builder_count}_users{attacker_user_count}.csv"
    )
    if all_transactions:
        tx_df = pd.DataFrame(tx.to_dict() for tx in all_transactions)
        tx_df = tx_df.dropna(subset=["included_at"])
        inv_df = ordering_inversions_from_tx_df(
            tx_df,
            block_key="included_at",
            order_key="position",
            priority_key="gas_fee",
            id_key="id",
        )
        inv_df.to_csv(inv_filename, index=False)
    else:
        pd.DataFrame(columns=[
            "block_number", "num_transactions", "inversion_count",
            "inversion_rate", "max_possible_inversions",
        ]).to_csv(inv_filename, index=False)

def simulate_pbs(
    attacker_builder_count: int,
    attacker_user_count: int,
    output_dir: Optional[str] = None,
    pool_initializer: Optional[Any] = None,
    pool_initargs: Optional[tuple] = None,
) -> List[Dict[str, Any]]:
    """Simulate PBS with given attacker counts. Optional output_dir and pool_initializer for by-period runs."""
    # Set attacker status for builders and users
    _set_attacker_status(attacker_builder_count, attacker_user_count)

    # Run simulation blocks sequentially with adaptive auction duration (T_s mechanism)
    block_data_list, all_transactions = _run_simulation_blocks_adaptive(
        pool_initializer=pool_initializer,
        pool_initargs=pool_initargs,
    )

    # Save transaction data to CSV
    _save_transaction_data(all_transactions, attacker_builder_count, attacker_user_count, output_dir)

    # Save block data to a separate CSV
    _save_block_data(block_data_list, attacker_builder_count, attacker_user_count, output_dir)

    # Save per-block ordering inversions
    _save_block_inversions(all_transactions, attacker_builder_count, attacker_user_count, output_dir)

    # Run garbage collection to clear memory
    gc.collect()

    return block_data_list

def run_simulation_in_process(
    attacker_builder_count: int,
    attacker_user_count: int,
    output_dir: Optional[str] = None,
    pool_initializer: Optional[Any] = None,
    pool_initargs: Optional[tuple] = None,
) -> None:
    """Run each simulation in a separate process to avoid state leakage."""
    kwargs = {}
    if output_dir is not None:
        kwargs["output_dir"] = output_dir
    if pool_initializer is not None:
        kwargs["pool_initializer"] = pool_initializer
        kwargs["pool_initargs"] = pool_initargs or ()
    process: mp.Process = mp.Process(
        target=simulate_pbs,
        args=(attacker_builder_count, attacker_user_count),
        kwargs=kwargs,
    )
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
