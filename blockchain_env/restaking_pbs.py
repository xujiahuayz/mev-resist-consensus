"""PBS simulation with restaking dynamics - COMPLETE IMPLEMENTATION."""

import os
import random
import csv
import time
import gc
from typing import List, Dict, Any, Tuple, Set

from user import User
from builder import Builder
from proposer import Proposer
from transaction import Transaction

# Constants
BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 100
BUILDERNUM = 50
PROPOSERNUM = 50
AUCTION_ROUNDS = 5  # FIXED: Exactly 5 rounds as specified

VALIDATOR_THRESHOLD = 32 * 10**9  # 32 ETH in gwei
MIN_VALIDATOR_NODES = 1

random.seed(16)

def create_participants_with_config(attacker_builders, attacker_users):
    """Create participants with configurable attacker counts."""
    # Create builders (ALL STAKE)
    builders = []
    for i in range(BUILDERNUM):
        is_attacker = i < attacker_builders
        
        # Stake distribution for builders
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
        builder.reinvestment_factor = 1.0  # 100% reinvestment
        builder.profit_history = []
        builder.stake_history = [builder.capital]
        builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
        builder.bid_history = []
        builder.mempool = []  # Keep as list instead of deque
        builder.selected_transactions = []
        
        builders.append(builder)
    
    # Create proposers (ALL STAKE)
    proposers = []
    for i in range(PROPOSERNUM):
        proposer = Proposer(f"proposer_{i}")
        
        # Same stake distribution for proposers
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
        proposer.reinvestment_factor = 1.0  # 100% reinvestment
        proposer.profit_history = []
        proposer.stake_history = [proposer.capital]
        
        proposers.append(proposer)
    
    # Create users (DO NOT STAKE)
    users = []
    for i in range(USERNUM):
        is_attacker = i < attacker_users
        user = User(f"user_{i}", is_attacker)
        # Users do not have staking properties
        users.append(user)
    
    return builders, proposers, users

def get_validator_nodes(participants):
    """Get all validator nodes for uniform selection from ALL staking participants."""
    # ✅ KEEP STAKE-BASED WEIGHTING - this is correct PoS behavior!
    # Participants with more stake (more validator nodes) should have higher selection probability
    
    nodes = []
    for participant in participants:
        num_nodes = participant.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            for _ in range(num_nodes):
                nodes.append(participant)  # ✅ This creates proper stake-based weighting
    return nodes

def update_stake(participant, profit: int):
    """Update participant stake with 100% restaking logic."""
    if profit <= 0:
        return
    
    # Track old state for debugging
    old_capital = participant.capital
    old_stake = participant.active_stake
    old_validator_nodes = participant.active_stake // VALIDATOR_THRESHOLD
    
    # 100% reinvestment
    participant.capital += profit
    
    # Update active stake based on validator node thresholds
    new_validator_nodes = participant.capital // VALIDATOR_THRESHOLD
    participant.active_stake = new_validator_nodes * VALIDATOR_THRESHOLD
    
    # Record history (limit size for memory management)
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)
    
    # Limit history size to prevent memory issues
    if len(participant.profit_history) > 1000:
        participant.profit_history = participant.profit_history[-500:]
        participant.stake_history = participant.stake_history[-500:]
    
    # Enhanced debug output
    if hasattr(update_stake, 'debug_count'):
        update_stake.debug_count += 1
    else:
        update_stake.debug_count = 1
    
    if update_stake.debug_count <= 20:
        stake_change = participant.active_stake - old_stake
        node_change = new_validator_nodes - old_validator_nodes
        participant_type = "Builder" if hasattr(participant, 'is_attacker') else "Proposer"
        attack_status = f"({'Attack' if getattr(participant, 'is_attacker', False) else 'NonAttack'})" if participant_type == "Builder" else ""
        print(f"Debug: {participant.id} ({participant_type}{attack_status}) profit={profit/1e9:.3f} ETH, "
              f"capital: {old_capital/1e9:.2f}→{participant.capital/1e9:.2f} ETH, "
              f"stake_change={stake_change/1e9:.3f} ETH, "
              f"nodes: {old_validator_nodes}→{new_validator_nodes} (+{node_change})")

def calculate_centralization_metrics(builders, proposers):
    """Calculate centralization metrics for monitoring."""
    all_participants = builders + proposers
    
    # Calculate stakes and total
    stakes = [p.active_stake for p in all_participants]
    total_stake = sum(stakes)
    
    if total_stake == 0:
        return {'gini': 0, 'hhi': 0, 'top_5_share': 0, 'total_stake_eth': 0}
    
    # Sort stakes in descending order
    sorted_stakes = sorted(stakes, reverse=True)
    
    # Top 5 concentration ratio
    top_5_share = sum(sorted_stakes[:5]) / total_stake * 100
    
    # Herfindahl-Hirschman Index
    market_shares = [stake / total_stake for stake in stakes]
    hhi = sum(share ** 2 for share in market_shares) * 10000
    
    # Simplified Gini coefficient
    n = len(stakes)
    if n == 0:
        gini = 0
    else:
        sorted_stakes_norm = sorted([stake / total_stake for stake in stakes])
        gini = (2 * sum(i * stake for i, stake in enumerate(sorted_stakes_norm, 1)) - (n + 1) * sum(sorted_stakes_norm)) / (n * sum(sorted_stakes_norm))
    
    return {
        'gini': gini,
        'hhi': hhi,
        'top_5_share': top_5_share,
        'total_stake_eth': total_stake / 1e9
    }

def calculate_block_value(builder, selected_transactions):
    """Calculate block value - includes MEV for attack builders."""
    if not selected_transactions:
        return 0.0
    
    # Gas fees from all transactions
    gas_fee = sum(tx.gas_fee for tx in selected_transactions)
    
    # MEV value only for attack builders
    mev_value = 0.0
    if builder.is_attacker:
        for tx in selected_transactions:
            if hasattr(tx, 'target_tx') and tx.target_tx:
                mev_value += tx.target_tx.mev_potential
    
    return gas_fee + mev_value

def clear_mempool_efficiently(builder, included_tx_ids: Set[int]):
    """Efficiently clear mempool of included transactions."""
    remaining_txs = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
    builder.mempool.clear()
    builder.mempool.extend(remaining_txs)
    
    # Prevent mempool from growing too large
    if len(builder.mempool) > 10000:
        builder.mempool = list(builder.mempool)[-5000:]  # Keep as list instead of deque

def process_block(builders, proposers, users, block_num):
    """Process a single block according to specifications."""
    
    # 1. Generate and distribute transactions to builders only
    # ✅ FIX: Use the improved network structure from network.py for fair distribution
    
    for user in users:
        tx_count = random.randint(1, 5)
        for _ in range(tx_count):
            if user.is_attacker:
                tx = user.launch_attack(block_num)
            else:
                tx = user.create_transactions(block_num)
            
            if tx:
                # ✅ USE: Network-based distribution - the network.py ensures fair connectivity
                # Users will naturally distribute transactions to their network neighbors
                # This eliminates the need for manual transaction balancing
                user.broadcast_transactions(tx)
    
    # 2. Select validator with proper stake-based weighting (this is CORRECT)
    all_staking_participants = builders + proposers
    validator_nodes = get_validator_nodes(all_staking_participants)
    
    if not validator_nodes:
        return None
    
    # ✅ This is correct - stake-based weighting for validator selection
    selected_validator = random.choice(validator_nodes)
    
    # 3. Process based on validator type
    winning_builder = None
    winning_bid = 0.0
    validator_type = ""
    
    if selected_validator in builders:
        # CASE 1: Builder selected as validator → Direct building
        winning_builder = selected_validator
        winning_builder.selected_transactions = winning_builder.select_transactions(block_num)
        
        if not winning_builder.selected_transactions:
            return None
        
        block_value = calculate_block_value(winning_builder, winning_builder.selected_transactions)
        
        # Builder gets ALL profit
        if block_value > 0:
            update_stake(winning_builder, int(block_value))
        
        winning_bid = 0.0  # No auction, so no bid
        validator_type = "builder"
        
    else:
        # CASE 2: Proposer selected as validator → Auction process
        # CORRECTED: Fixed 5 rounds as specified
        auction_rounds = AUCTION_ROUNDS
        
        # Pre-select transactions for all builders
        builder_selections = []
        for builder in builders:
            builder.selected_transactions = builder.select_transactions(block_num)
            block_value = calculate_block_value(builder, builder.selected_transactions)
            builder_selections.append((builder, block_value))
        
        # Run auction for exactly 5 rounds
        last_round_bids = [0.0] * len(builders)
        
        for round_num in range(auction_rounds):
            round_bids = []
            
            for i, (builder, block_value) in enumerate(builder_selections):
                if block_value > 0:
                    # ✅ IMPLEMENT: All builders use the same reactive bidding strategy
                    # This ensures fair competition regardless of attack status
                    
                    if round_num == 0:
                        # First round: start with 50% of block value
                        bid = block_value * 0.5
                    else:
                        # Reactive bidding strategy (same for all builders)
                        highest_last_bid = max(last_round_bids) if last_round_bids else 0.0
                        
                        # Get builder's last bid from previous round
                        my_last_bid = last_round_bids[i] if i < len(last_round_bids) else 0.0
                        
                        # Get second highest bid from previous round
                        if len(last_round_bids) > 1:
                            sorted_bids = sorted(last_round_bids, reverse=True)
                            second_highest_last_bid = sorted_bids[1]
                        else:
                            second_highest_last_bid = 0.0
                        
                        # Reactive bidding logic (same for attack and non-attack builders)
                        if my_last_bid < highest_last_bid:
                            # My bid was too low, increase it
                            bid = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
                        elif my_last_bid == highest_last_bid:
                            # I was tied for highest, bid slightly higher with randomness
                            bid = my_last_bid + random.random() * (block_value - my_last_bid)
                        else:
                            # My bid was highest, reduce it slightly to stay competitive
                            bid = my_last_bid - 0.7 * (my_last_bid - second_highest_last_bid)
                        
                        # Ensure bid is reasonable
                        bid = max(0.0, min(bid, block_value * 0.9))
                    
                    round_bids.append(bid)
                else:
                    round_bids.append(0.0)
            
            last_round_bids = round_bids
        
        # Select winning builder
        if not last_round_bids or max(last_round_bids) == 0:
            return None
        
        winning_bid = max(last_round_bids)
        winning_builder_idx = last_round_bids.index(winning_bid)
        winning_builder = builder_selections[winning_builder_idx][0]
        
        # Distribute profits
        if winning_bid > 0:
            # Proposer gets the bid
            update_stake(selected_validator, int(winning_bid))
            
            # Builder gets remaining value
            block_value = builder_selections[winning_builder_idx][1]
            builder_profit = block_value - winning_bid
            if builder_profit > 0:
                update_stake(winning_builder, int(builder_profit))
        
        validator_type = "proposer"
    
    # 4. Clear mempools efficiently
    if winning_builder and winning_builder.selected_transactions:
        included_tx_ids = {tx.id for tx in winning_builder.selected_transactions}
        for builder in builders:
            clear_mempool_efficiently(builder, included_tx_ids)
    
    # 5. Calculate centralization metrics
    centralization_metrics = calculate_centralization_metrics(builders, proposers)
    
    # 6. Create block data
    block_data = {
        'block_num': block_num,
        'validator_id': selected_validator.id,
        'validator_type': validator_type,
        'winning_builder_id': winning_builder.id if winning_builder else "",
        'winning_bid': winning_bid,
        'total_gas_fee': sum(tx.gas_fee for tx in winning_builder.selected_transactions) if winning_builder and winning_builder.selected_transactions else 0,
        'total_mev': sum(tx.mev_potential for tx in winning_builder.selected_transactions) if winning_builder and winning_builder.selected_transactions else 0,
        'validator_stake': selected_validator.active_stake,
        'validator_nodes': selected_validator.active_stake // VALIDATOR_THRESHOLD,
        'gini_coefficient': centralization_metrics['gini'],
        'hhi': centralization_metrics['hhi'],
        'top_5_share': centralization_metrics['top_5_share'],
        'total_stake_eth': centralization_metrics['total_stake_eth']
    }
    
    return block_data

def save_block_data(block_data_list, attacker_builders, attacker_users):
    """Save block data to CSV."""
    filename = f"data/same_seed/restaking_pbs/pbs_restaking_blocks_builders{attacker_builders}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if block_data_list:
            fieldnames = block_data_list[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for block_data in block_data_list:
                writer.writerow(block_data)

def save_participant_evolution(builders, proposers, attacker_builders, attacker_users):
    """Save participant evolution data."""
    filename = f"data/same_seed/restaking_pbs/pbs_restaking_participants_builders{attacker_builders}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'participant_id', 'participant_type', 'is_attacker',
            'initial_stake_eth', 'final_stake_eth', 'final_capital_eth',
            'initial_nodes', 'final_nodes', 'total_profit_eth', 'growth_rate'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for builder in builders:
            growth_rate = ((builder.capital - builder.initial_stake) / builder.initial_stake * 100) if builder.initial_stake > 0 else 0
            writer.writerow({
                'participant_id': builder.id,
                'participant_type': 'builder',
                'is_attacker': builder.is_attacker,
                'initial_stake_eth': builder.initial_stake / 1e9,
                'final_stake_eth': builder.active_stake / 1e9,
                'final_capital_eth': builder.capital / 1e9,
                'initial_nodes': builder.initial_stake // VALIDATOR_THRESHOLD,
                'final_nodes': builder.active_stake // VALIDATOR_THRESHOLD,
                'total_profit_eth': sum(builder.profit_history) / 1e9,
                'growth_rate': growth_rate
            })
        
        for proposer in proposers:
            growth_rate = ((proposer.capital - proposer.initial_stake) / proposer.initial_stake * 100) if proposer.initial_stake > 0 else 0
            writer.writerow({
                'participant_id': proposer.id,
                'participant_type': 'proposer',
                'is_attacker': False,  # Proposers are never attackers
                'initial_stake_eth': proposer.initial_stake / 1e9,
                'final_stake_eth': proposer.active_stake / 1e9,
                'final_capital_eth': proposer.capital / 1e9,
                'initial_nodes': proposer.initial_stake // VALIDATOR_THRESHOLD,
                'final_nodes': proposer.active_stake // VALIDATOR_THRESHOLD,
                'total_profit_eth': sum(proposer.profit_history) / 1e9,
                'growth_rate': growth_rate
            })

def save_metrics_evolution(metrics_history, attacker_builders, attacker_users):
    """Save metrics evolution data."""
    filename = f"data/same_seed/restaking_pbs/pbs_restaking_metrics_builders{attacker_builders}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['block_num', 'gini', 'hhi', 'top_5_share', 'total_stake_eth']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block_num, metrics in enumerate(metrics_history):
            row = {'block_num': block_num}
            row.update(metrics)
            writer.writerow(row)

def record_continuous_stake_data(builders, proposers, block_num, continuous_stake_data):
    """Record stake data for every participant at every block for continuous plotting."""
    all_participants = builders + proposers
    
    for participant in all_participants:
        # Record stake data for this participant at this block
        participant_block_data = {
            'block_num': block_num,
            'participant_id': participant.id,
            'participant_type': 'builder' if participant in builders else 'proposer',
            'is_attacker': getattr(participant, 'is_attacker', False),  # False for proposers
            'current_stake': participant.active_stake,
            'current_capital': participant.capital,
            'current_nodes': participant.active_stake // VALIDATOR_THRESHOLD
        }
        continuous_stake_data.append(participant_block_data)

def save_continuous_stake_data(continuous_stake_data, attacker_builders, attacker_users):
    """Save continuous stake data for every participant at every block."""
    filename = f"data/same_seed/restaking_pbs/pbs_restaking_continuous_stake_builders{attacker_builders}_users{attacker_users}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['block_num', 'participant_id', 'participant_type', 'is_attacker', 
                     'current_stake', 'current_capital', 'current_nodes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for stake_data in continuous_stake_data:
            writer.writerow(stake_data)

def run_pbs_restaking_simulation(attacker_builders, attacker_users):
    """Run the complete PBS restaking simulation."""
    print(f"Starting PBS Restaking Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Attackers: {attacker_builders}/{BUILDERNUM} builders, {attacker_users}/{USERNUM} users")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 1e9:.1f} ETH")
    print(f"Auction rounds: {AUCTION_ROUNDS}")
    print("="*70)
    
    # Create participants
    builders, proposers, users = create_participants_with_config(attacker_builders, attacker_users)
    
    # Initialize tracking
    block_data_list = []
    continuous_stake_data = []  # New: for continuous stake recording
    metrics_history = []
    
    start_time = time.time()
    
    # Run simulation
    for block_num in range(BLOCKNUM):
        block_data = process_block(builders, proposers, users, block_num)
        
        if block_data:
            block_data_list.append(block_data)
            
            # Track metrics
            metrics = {
                'gini': block_data['gini_coefficient'],
                'hhi': block_data['hhi'],
                'top_5_share': block_data['top_5_share'],
                'total_stake_eth': block_data['total_stake_eth']
            }
            metrics_history.append(metrics)
        
        # NEW: Record continuous stake data for every participant at every block
        record_continuous_stake_data(builders, proposers, block_num, continuous_stake_data)
        
        # Progress update
        if block_num % 100 == 0:
            print(f"Processed block {block_num}/{BLOCKNUM}")
    
    end_time = time.time()
    
    # Save all data to data/same_seed/restaking_pbs/ folder
    save_block_data(block_data_list, attacker_builders, attacker_users)
    save_continuous_stake_data(continuous_stake_data, attacker_builders, attacker_users)  # New
    save_participant_evolution(builders, proposers, attacker_builders, attacker_users)
    save_metrics_evolution(metrics_history, attacker_builders, attacker_users)
    
    # Final analysis
    print(f"\nSimulation completed in {end_time - start_time:.2f} seconds")
    
    # Calculate final metrics
    final_metrics = calculate_centralization_metrics(builders, proposers)
    print(f"\nFinal Centralization Metrics:")
    print(f"Gini Coefficient: {final_metrics['gini']:.4f}")
    print(f"HHI: {final_metrics['hhi']:.0f}")
    print(f"Top 5 Concentration: {final_metrics['top_5_share']:.2f}%")
    print(f"Total Stake: {final_metrics['total_stake_eth']:.1f} ETH")
    
    # Analyze attack vs non-attack builders
    attack_builders = [b for b in builders if b.is_attacker]
    non_attack_builders = [b for b in builders if not b.is_attacker]
    
    if attack_builders and non_attack_builders:
        avg_attack_growth = sum((b.capital - b.initial_stake) / b.initial_stake for b in attack_builders) / len(attack_builders)
        avg_non_attack_growth = sum((b.capital - b.initial_stake) / b.initial_stake for b in non_attack_builders) / len(non_attack_builders)
        
        print(f"\nBuilder Growth Analysis:")
        print(f"Attack builders average growth: {avg_attack_growth * 100:.2f}%")
        print(f"Non-attack builders average growth: {avg_non_attack_growth * 100:.2f}%")
        print(f"Attack advantage: {(avg_attack_growth - avg_non_attack_growth) * 100:.2f} percentage points")
    
    # Memory cleanup
    gc.collect()
    
    return block_data_list

if __name__ == "__main__":
    
    for attacker_builders, attacker_users in [(25, 50)]:
        print(f"\n{'='*80}")
        print(f"Running configuration: {attacker_builders} attack builders, {attacker_users} attack users")
        print(f"{'='*80}")
        
        run_pbs_restaking_simulation(attacker_builders, attacker_users)
        
        print(f"\nConfiguration completed. Files saved in data/restaking_pbs/")
        print(f"Waiting 5 seconds before next configuration...")
        time.sleep(5)
    
    print(f"\n{'='*80}")
    print("All simulations completed!")
    print("Check data/restaking_pbs/ for results")
    print(f"{'='*80}")