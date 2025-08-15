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
from concurrent.futures import ThreadPoolExecutor, as_completed

import networkx as nx

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.network import build_network
from blockchain_env.transaction import Transaction

# Constants for optimized analysis
BLOCKNUM: int = 1000  # Reduced from 10,000 for faster execution
BLOCK_CAP: int = 100
USERNUM: int = 50
BUILDERNUM: int = 20
PROPOSERNUM: int = 20

# Restaking parameters
VALIDATOR_THRESHOLD: int = 32 * 10**9  # 32 ETH in gwei
TOTAL_NETWORK_STAKE: int = 1000 * VALIDATOR_THRESHOLD  # 1000 active validators
REINVESTMENT_PROBABILITY: float = 0.5  # 50% chance of restaking

# Optimization parameters
MAX_WORKERS = 8  # Number of worker threads
BATCH_SIZE = 100  # Process blocks in batches

random.seed(16)

class RestakingParticipant:
    """Base class for participants with restaking dynamics."""
    
    def __init__(self, participant_id: str, initial_stake: int = 0):
        self.id = participant_id
        self.capital = initial_stake  # Total accumulated capital
        self.active_stake = initial_stake  # Active stake (only full validator units)
        self.reinvestment_factor = random.random() < REINVESTMENT_PROBABILITY  # γ_i ∈ {0,1}
        self.profit_history = []  # Track profits over time
        self.stake_history = []  # Track stake evolution
        
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

class RestakingBuilder(Builder, RestakingParticipant):
    """Builder with restaking dynamics."""
    
    def __init__(self, builder_id: str, is_attacker: bool, initial_stake: int = 0):
        Builder.__init__(self, builder_id, is_attacker)
        RestakingParticipant.__init__(self, builder_id, initial_stake)
    
    def receive_block_reward(self, block_reward: int) -> None:
        """Receive block reward and update stake."""
        self.update_stake(block_reward)

class RestakingProposer(Proposer, RestakingParticipant):
    """Proposer with restaking dynamics."""
    
    def __init__(self, proposer_id: str, is_attacker: bool, initial_stake: int = 0):
        Proposer.__init__(self, proposer_id)
        RestakingParticipant.__init__(self, proposer_id, initial_stake)
        self.is_attacker = is_attacker
    
    def receive_proposer_reward(self, proposer_reward: int) -> None:
        """Receive proposer reward and update stake."""
        self.update_stake(proposer_reward)

def initialize_network_with_stakes() -> Tuple[Any, List[RestakingBuilder], List[RestakingProposer]]:
    """Initialize network with realistic stake distribution."""
    
    # Create participants with heterogeneous initial stakes
    proposer_list = []
    builder_list = []
    
    # Initialize proposers with varying initial stakes
    for i in range(PROPOSERNUM):
        # Realistic stake distribution: some have 32 ETH, some have multiples
        initial_stake = random.choice([
            VALIDATOR_THRESHOLD,      # 32 ETH
            VALIDATOR_THRESHOLD * 2,  # 64 ETH
            VALIDATOR_THRESHOLD * 5,  # 160 ETH
            VALIDATOR_THRESHOLD * 10, # 320 ETH
        ])
        # Set half of proposers as attackers
        is_attacker = i < PROPOSERNUM // 2
        proposer = RestakingProposer(f"proposer_{i}", is_attacker, initial_stake)
        proposer_list.append(proposer)
    
    # Initialize builders with varying initial stakes
    for i in range(BUILDERNUM):
        initial_stake = random.choice([
            VALIDATOR_THRESHOLD,      # 32 ETH
            VALIDATOR_THRESHOLD * 2,  # 64 ETH
            VALIDATOR_THRESHOLD * 3,  # 96 ETH
            VALIDATOR_THRESHOLD * 8,  # 256 ETH
        ])
        # Set half of builders as attackers
        is_attacker = i < BUILDERNUM // 2
        builder = RestakingBuilder(f"builder_{i}", is_attacker, initial_stake)
        builder_list.append(builder)
    
    # Create users (no stake for users) - will use stable period data
    user_list = [User(f"user_{i}", i < USERNUM // 2) for i in range(USERNUM)]
    
    # Build network
    network = build_network(user_list, builder_list, proposer_list)
    
    return network, builder_list, proposer_list

def transaction_number() -> int:
    """Generate random transaction count for users."""
    random_number: int = random.randint(0, 100)
    if random_number < 50:
        return 1
    if random_number < 80:
        return 0
    if random_number < 95:
        return 2
    return random.randint(3, 5)

def _extract_network_nodes(network_graph: Any) -> Tuple[List[User], List[RestakingBuilder], List[RestakingProposer]]:
    """Extract users, builders, and proposers from the network graph."""
    user_nodes: List[User] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], User)]
    builder_nodes: List[RestakingBuilder] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], RestakingBuilder)]
    proposer_nodes: List[RestakingProposer] = [data['node'] for node_id, data in network_graph.nodes(data=True) if isinstance(data['node'], RestakingProposer)]
    return user_nodes, builder_nodes, proposer_nodes

def _process_user_transactions(user_nodes: List[User], block_num: int) -> List[Transaction]:
    """Process user transactions for the block using stable period data."""
    all_transactions = []
    
    for user in user_nodes:
        num_transactions: int = transaction_number()
        for _ in range(num_transactions):
            if not user.is_attacker:
                # Use stable period data for gas fees and MEV
                tx: Transaction = user.create_transactions(block_num)
            else:
                tx: Transaction = user.launch_attack(block_num)

            if tx:
                user.broadcast_transactions(tx)
                all_transactions.append(tx)
    
    return all_transactions

def _process_builder_bids(builder_nodes: List[RestakingBuilder], 
                         transactions: List[Transaction], 
                         block_num: int) -> List[Tuple[str, List[Transaction], float]]:
    """Process builder bids, considering their stake levels."""
    builder_results = []
    
    # Distribute transactions to builders
    for i, tx in enumerate(transactions):
        builder_idx = i % len(builder_nodes)
        builder_nodes[builder_idx].mempool.append(tx)
    
    for builder in builder_nodes:
        # Builder's bid power is influenced by their stake
        stake_multiplier = 1 + (builder.get_restaking_stake_ratio() * 10)  # Higher stake = higher bid power
        
        # Select transactions based on stake-influenced capacity
        max_transactions = min(BLOCK_CAP, int(BLOCK_CAP * stake_multiplier))
        selected_transactions = builder.select_transactions(max_transactions)
        
        if selected_transactions:
            # Calculate bid value considering stake influence
            total_gas_fee = sum(tx.gas_fee for tx in selected_transactions)
            total_mev = sum(tx.mev_potential for tx in selected_transactions)
            bid_value = total_gas_fee + total_mev * stake_multiplier
            
            builder_results.append((builder.id, selected_transactions, bid_value))
    
    return builder_results

def _process_proposer_bids(proposer_nodes: List[RestakingProposer], 
                          builder_nodes: List[RestakingBuilder], 
                          builder_results: List[Tuple[str, List[Transaction], float]], 
                          block_num: int) -> Tuple[Tuple[str, List[Transaction], float], RestakingBuilder, RestakingProposer]:
    """Process proposer bids, with stake-weighted selection."""
    
    if not builder_results:
        return None, None, None
    
    # Weight selection by proposer stake (higher stake = higher chance)
    proposer_weights = [p.get_restaking_stake_ratio() + 0.01 for p in proposer_nodes]  # Add small constant to avoid zero weights
    selected_proposer = random.choices(proposer_nodes, weights=proposer_weights, k=1)[0]
    
    # Select winning builder bid (highest bid value)
    winning_bid = max(builder_results, key=lambda x: x[2])
    winning_builder_id = winning_bid[0]
    winning_builder = next(b for b in builder_nodes if b.id == winning_builder_id)
    
    # Award rewards
    block_reward = winning_bid[2]  # Total bid value
    proposer_reward = block_reward * 0.1  # 10% to proposer
    
    winning_builder.receive_block_reward(block_reward - proposer_reward)
    selected_proposer.receive_proposer_reward(proposer_reward)
    
    return winning_bid, winning_builder, selected_proposer

def _create_block_data(block_num: int, 
                      winning_bid: Tuple[str, List[Transaction], float], 
                      winning_builder: RestakingBuilder,
                      selected_proposer: RestakingProposer) -> Dict[str, Any]:
    """Create block data with restaking information."""
    
    if not winning_bid:
        return {}
    
    builder_id, transactions, bid_value = winning_bid
    
    # Assign transaction positions and inclusion times
    for position, tx in enumerate(transactions):
        tx.position = position
        tx.included_at = block_num
    
    # Calculate block metrics
    total_gas_fee = sum(tx.gas_fee for tx in transactions)
    total_mev_available = sum(tx.mev_potential for tx in transactions)
    
    block_data = {
        "block_num": block_num,
        "builder_id": builder_id,
        "proposer_id": selected_proposer.id,
        "builder_stake": winning_builder.active_stake,
        "proposer_stake": selected_proposer.active_stake,
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev_available,
        "bid_value": bid_value,
        "builder_reinvestment_factor": winning_builder.reinvestment_factor,
        "proposer_reinvestment_factor": selected_proposer.reinvestment_factor
    }
    
    return block_data

def process_block_batch(block_range: Tuple[int, int], 
                       network: Any, 
                       builder_nodes: List[RestakingBuilder], 
                       proposer_nodes: List[RestakingProposer]) -> List[Dict[str, Any]]:
    """Process a batch of blocks for multithreading."""
    
    block_data_list = []
    start_block, end_block = block_range
    
    print(f"Processing batch {start_block}-{end_block}")
    
    for block_num in range(start_block, end_block):
        # Extract network nodes
        user_nodes, _, _ = _extract_network_nodes(network)
        
        # Process user transactions and get all transactions
        transactions = _process_user_transactions(user_nodes, block_num)
        
        print(f"Block {block_num}: {len(transactions)} user transactions")
        
        # Process builder bids
        builder_results = _process_builder_bids(builder_nodes, transactions, block_num)
        
        print(f"Block {block_num}: {len(builder_results)} builder bids")
        
        # Process proposer bids
        winning_bid, winning_builder, selected_proposer = _process_proposer_bids(
            proposer_nodes, builder_nodes, builder_results, block_num
        )
        
        # Create block data
        if winning_bid and winning_builder and selected_proposer:
            block_data = _create_block_data(
                block_num, winning_bid, winning_builder, selected_proposer
            )
            
            if block_data:
                block_data_list.append(block_data)
                print(f"Block {block_num}: Created block data")
        else:
            print(f"Block {block_num}: No valid winning bid")
        
        # Clear mempools
        for builder in builder_nodes:
            builder.clear_mempool(block_num)
    
    print(f"Batch {start_block}-{end_block}: Processed {len(block_data_list)} blocks")
    return block_data_list

def simulate_restaking_pbs() -> List[Dict[str, Any]]:
    """Main simulation function for restaking PBS with multithreading."""
    
    print(f"Starting Optimized Restaking PBS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    print(f"Attackers: {BUILDERNUM // 2} builders, {PROPOSERNUM // 2} proposers, {USERNUM // 2} users")
    print(f"Using {MAX_WORKERS} worker threads")
    
    # Initialize network with restaking participants
    network, builder_nodes, proposer_nodes = initialize_network_with_stakes()
    
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
            executor.submit(process_block_batch, batch, network, builder_nodes, proposer_nodes): batch 
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
    _save_stake_evolution(builder_nodes, proposer_nodes)
    
    print(f"Results saved to data/same_seed/restaking_pbs/")
    
    return all_blocks

def _save_block_data(block_data_list: List[Dict[str, Any]]) -> None:
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

def _save_stake_evolution(builder_nodes: List[RestakingBuilder], 
                         proposer_nodes: List[RestakingProposer]) -> None:
    """Save stake evolution data for analysis."""
    filename = f"data/same_seed/restaking_pbs/restaking_pbs_stake_evolution.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['participant_id', 'participant_type', 'is_attacker', 'reinvestment_factor', 
                     'initial_stake', 'final_stake', 'final_capital', 'total_profit', 'validator_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Save builder data
        for builder in builder_nodes:
            writer.writerow({
                'participant_id': builder.id,
                'participant_type': 'builder',
                'is_attacker': builder.is_attacker,
                'reinvestment_factor': builder.reinvestment_factor,
                'initial_stake': builder.stake_history[0] if builder.stake_history else 0,
                'final_stake': builder.active_stake,
                'final_capital': builder.capital,
                'total_profit': sum(builder.profit_history),
                'validator_count': builder.get_validator_count()
            })
        
        # Save proposer data
        for proposer in proposer_nodes:
            writer.writerow({
                'participant_id': proposer.id,
                'participant_type': 'proposer',
                'is_attacker': proposer.is_attacker,
                'reinvestment_factor': proposer.reinvestment_factor,
                'initial_stake': proposer.stake_history[0] if proposer.stake_history else 0,
                'final_stake': proposer.active_stake,
                'final_capital': proposer.capital,
                'total_profit': sum(proposer.profit_history),
                'validator_count': proposer.get_validator_count()
            })

if __name__ == "__main__":
    # Example usage
    print("Optimized Restaking PBS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    # Run simulation
    simulate_restaking_pbs() 