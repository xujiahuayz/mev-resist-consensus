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

# Constants for long-term analysis
BLOCKNUM: int = 10000  # Extended to 10,000 blocks for convergence analysis
BLOCK_CAP: int = 100
USERNUM: int = 50
BUILDERNUM: int = 50
PROPOSERNUM: int = 50

# Restaking parameters
VALIDATOR_THRESHOLD: int = 32 * 10**9  # 32 ETH in gwei
TOTAL_NETWORK_STAKE: int = 1000 * VALIDATOR_THRESHOLD  # 1000 active validators
REINVESTMENT_PROBABILITY: float = 0.5  # 50% chance of restaking

random.seed(16)

# Determine the number of CPU cores and set the number of processes
num_cores: int = os.cpu_count()
num_processes: int = max(num_cores - 1, 1)

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
    
    def get_stake_ratio(self) -> float:
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
    
    def __init__(self, proposer_id: str, initial_stake: int = 0):
        Proposer.__init__(self, proposer_id)
        RestakingParticipant.__init__(self, proposer_id, initial_stake)
    
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
        proposer = RestakingProposer(f"proposer_{i}", initial_stake)
        proposer_list.append(proposer)
    
    # Initialize builders with varying initial stakes
    for i in range(BUILDERNUM):
        initial_stake = random.choice([
            VALIDATOR_THRESHOLD,      # 32 ETH
            VALIDATOR_THRESHOLD * 2,  # 64 ETH
            VALIDATOR_THRESHOLD * 3,  # 96 ETH
            VALIDATOR_THRESHOLD * 8,  # 256 ETH
        ])
        builder = RestakingBuilder(f"builder_{i}", False, initial_stake)
        builder_list.append(builder)
    
    # Create users (no stake for users)
    user_list = [User(f"user_{i}", False) for i in range(USERNUM)]
    
    # Build network
    network = build_network(user_list, builder_list, proposer_list)
    
    return network, builder_list, proposer_list

def calculate_centralization_metrics(participants: List[RestakingParticipant]) -> Dict[str, float]:
    """Calculate centralization metrics including Gini coefficient."""
    
    stakes = [p.active_stake for p in participants]
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
        'total_participants': len(participants),
        'total_stake': total_stake
    }

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

def _process_builder_bids(builder_nodes: List[RestakingBuilder], block_num: int) -> List[Tuple[str, List[Transaction], float]]:
    """Process builder bids, considering their stake levels."""
    builder_results = []
    
    for builder in builder_nodes:
        # Builder's bid power is influenced by their stake
        stake_multiplier = 1 + (builder.get_stake_ratio() * 10)  # Higher stake = higher bid power
        
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
                          block_num: int) -> Tuple[Tuple[str, List[Transaction], float], RestakingBuilder]:
    """Process proposer bids, with stake-weighted selection."""
    
    if not builder_results:
        return None, None
    
    # Weight selection by proposer stake (higher stake = higher chance)
    proposer_weights = [p.get_stake_ratio() + 0.01 for p in proposer_nodes]  # Add small constant to avoid zero weights
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
    
    return winning_bid, winning_builder

def _create_block_data(block_num: int, 
                      winning_bid: Tuple[str, List[Transaction], float], 
                      winning_builder: RestakingBuilder,
                      centralization_metrics: Dict[str, float]) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Create block data with restaking information."""
    
    if not winning_bid:
        return {}, []
    
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
        "total_gas_fee": total_gas_fee,
        "total_mev_available": total_mev_available,
        "bid_value": bid_value,
        "builder_stake": winning_builder.active_stake,
        "builder_stake_ratio": winning_builder.get_stake_ratio(),
        "builder_validator_count": winning_builder.get_validator_count(),
        "builder_reinvestment_factor": winning_builder.reinvestment_factor,
        "gini_coefficient": centralization_metrics['gini'],
        "concentration_ratio": centralization_metrics['concentration_ratio'],
        "herfindahl_index": centralization_metrics['herfindahl_index'],
        "total_network_stake": centralization_metrics['total_stake']
    }
    
    return block_data, transactions

def process_block(block_num: int, 
                 network_graph: Any, 
                 builder_nodes: List[RestakingBuilder], 
                 proposer_nodes: List[RestakingProposer]) -> Tuple[Dict[str, Any], List[Transaction]]:
    """Process a single block with restaking dynamics."""
    
    # Extract network nodes
    user_nodes, _, _ = _extract_network_nodes(network_graph)
    
    # Process user transactions
    _process_user_transactions(user_nodes, block_num)
    
    # Process builder bids
    builder_results = _process_builder_bids(builder_nodes, block_num)
    
    # Process proposer bids
    winning_bid, winning_builder = _process_proposer_bids(
        proposer_nodes, builder_nodes, builder_results, block_num
    )
    
    # Calculate centralization metrics
    all_participants = builder_nodes + proposer_nodes
    centralization_metrics = calculate_centralization_metrics(all_participants)
    
    # Create block data
    block_data, transactions = _create_block_data(
        block_num, winning_bid, winning_builder, centralization_metrics
    )
    
    # Clear mempools
    for builder in builder_nodes:
        builder.clear_mempool(block_num)
    
    return block_data, transactions

def _set_attacker_status(attacker_builder_count: int, attacker_user_count: int, 
                        builder_nodes: List[RestakingBuilder], user_nodes: List[User]) -> None:
    """Set attacker status for participants."""
    for i, builder in enumerate(builder_nodes):
        builder.is_attacker = i < attacker_builder_count
    
    for i, user in enumerate(user_nodes):
        user.is_attacker = i < attacker_user_count

def _run_simulation_blocks(builder_nodes: List[RestakingBuilder], 
                          proposer_nodes: List[RestakingProposer],
                          network: Any) -> Tuple[List[Dict[str, Any]], List[Transaction]]:
    """Run simulation for all blocks."""
    
    all_blocks = []
    all_transactions = []
    
    for block_num in range(BLOCKNUM):
        block_data, transactions = process_block(block_num, network, builder_nodes, proposer_nodes)
        if block_data:
            all_blocks.append(block_data)
        all_transactions.extend(transactions)
        
        # Progress indicator for long simulations
        if block_num % 1000 == 0:
            print(f"Processed block {block_num}/{BLOCKNUM}")
    
    return all_blocks, all_transactions

def _save_transaction_data(all_transactions: List[Transaction], 
                          attacker_builder_count: int, 
                          attacker_user_count: int) -> None:
    """Save transaction data to CSV."""
    if not all_transactions:
        return
    
    filename = f"data/restaking_pbs/restaking_pbs_transactions_builders{attacker_builder_count}_users{attacker_user_count}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = all_transactions[0].to_dict().keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tx in all_transactions:
            writer.writerow(tx.to_dict())

def _save_block_data(block_data_list: List[Dict[str, Any]], 
                    attacker_builder_count: int, 
                    attacker_user_count: int) -> None:
    """Save block data to CSV."""
    if not block_data_list:
        return
    
    filename = f"data/restaking_pbs/restaking_pbs_blocks_builders{attacker_builder_count}_users{attacker_user_count}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = block_data_list[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_data in block_data_list:
            writer.writerow(block_data)

def _save_stake_evolution(builder_nodes: List[RestakingBuilder], 
                         proposer_nodes: List[RestakingProposer],
                         attacker_builder_count: int, 
                         attacker_user_count: int) -> None:
    """Save stake evolution data for analysis."""
    filename = f"data/restaking_pbs/restaking_pbs_stake_evolution_builders{attacker_builder_count}_users{attacker_user_count}.csv"
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
                'is_attacker': False,  # Proposers are not attackers in this model
                'reinvestment_factor': proposer.reinvestment_factor,
                'initial_stake': proposer.stake_history[0] if proposer.stake_history else 0,
                'final_stake': proposer.active_stake,
                'final_capital': proposer.capital,
                'total_profit': sum(proposer.profit_history),
                'validator_count': proposer.get_validator_count()
            })

def simulate_restaking_pbs(attacker_builder_count: int, attacker_user_count: int) -> List[Dict[str, Any]]:
    """Main simulation function for restaking PBS."""
    
    print(f"Starting Restaking PBS Simulation")
    print(f"Blocks: {BLOCKNUM}, Attackers: {attacker_builder_count} builders, {attacker_user_count} users")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 10**9:.1f} ETH")
    print(f"Reinvestment probability: {REINVESTMENT_PROBABILITY:.1%}")
    
    # Initialize network with restaking participants
    network, builder_nodes, proposer_nodes = initialize_network_with_stakes()
    
    # Set attacker status
    user_nodes = [data['node'] for node_id, data in network.nodes(data=True) if isinstance(data['node'], User)]
    _set_attacker_status(attacker_builder_count, attacker_user_count, builder_nodes, user_nodes)
    
    # Run simulation
    start_time = time.time()
    block_data_list, all_transactions = _run_simulation_blocks(builder_nodes, proposer_nodes, network)
    end_time = time.time()
    
    print(f"Simulation completed in {end_time - start_time:.2f} seconds")
    
    # Save results
    _save_transaction_data(all_transactions, attacker_builder_count, attacker_user_count)
    _save_block_data(block_data_list, attacker_builder_count, attacker_user_count)
    _save_stake_evolution(builder_nodes, proposer_nodes, attacker_builder_count, attacker_user_count)
    
    # Print final centralization metrics
    all_participants = builder_nodes + proposer_nodes
    final_metrics = calculate_centralization_metrics(all_participants)
    
    print(f"\nFinal Centralization Metrics:")
    print(f"Gini Coefficient: {final_metrics['gini']:.4f}")
    print(f"Top 5 Concentration Ratio: {final_metrics['concentration_ratio']:.4f}")
    print(f"Herfindahl Index: {final_metrics['herfindahl_index']:.4f}")
    print(f"Total Network Stake: {final_metrics['total_stake'] / 10**9:.1f} ETH")
    
    return block_data_list

def run_simulation_in_process(attacker_builder_count: int, attacker_user_count: int) -> None:
    """Run simulation in a separate process."""
    try:
        simulate_restaking_pbs(attacker_builder_count, attacker_user_count)
    except Exception as e:
        print(f"Error in simulation: {e}")

if __name__ == "__main__":
    # Example usage
    print("Restaking PBS Simulation for Long-term Centralization Analysis")
    print("=" * 70)
    
    # Run simulation with different attacker configurations
    attacker_configs = [
        (0, 0),   # No attackers
        (5, 10),  # 5 attacker builders, 10 attacker users
        (10, 20), # 10 attacker builders, 20 attacker users
    ]
    
    for builder_attackers, user_attackers in attacker_configs:
        print(f"\nRunning simulation with {builder_attackers} attacker builders and {user_attackers} attacker users")
        simulate_restaking_pbs(builder_attackers, user_attackers) 