"""Simple optimized PBS simulation with restaking using existing classes."""

import os
import random
import csv
import time
from typing import List, Dict, Any

from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from blockchain_env.transaction import Transaction

# Constants
BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 50
PROPOSERNUM = 50
MAX_ROUNDS = 12  # Reduced from 24

VALIDATOR_THRESHOLD = 100000000  # 0.1 ETH instead of 1 ETH for better visibility

random.seed(16)

def create_participants():
    """Create participants with restaking enabled."""
    # Create builders
    builders = []
    for i in range(BUILDERNUM):
        is_attacker = i < BUILDERNUM // 2
        builder = Builder(f"builder_{i}", is_attacker)
        
        # Add restaking properties
        builder.capital = random.choice([
            VALIDATOR_THRESHOLD,
            VALIDATOR_THRESHOLD * 2,
            VALIDATOR_THRESHOLD * 3,
            VALIDATOR_THRESHOLD * 5,
        ])
        builder.active_stake = builder.capital
        builder.reinvestment_factor = random.random()
        builder.profit_history = []
        builder.stake_history = [builder.capital]
        
        builders.append(builder)
    
    # Create proposers
    proposers = []
    for i in range(PROPOSERNUM):
        proposer = Proposer(f"proposer_{i}")
        
        # Add restaking properties
        proposer.capital = random.choice([
            VALIDATOR_THRESHOLD,
            VALIDATOR_THRESHOLD * 2,
            VALIDATOR_THRESHOLD * 5,
            VALIDATOR_THRESHOLD * 10,
        ])
        proposer.active_stake = proposer.capital
        proposer.reinvestment_factor = random.random()
        proposer.profit_history = []
        proposer.stake_history = [proposer.capital]
        
        proposers.append(proposer)
    
    # Create users
    users = []
    for i in range(USERNUM):
        is_attacker = i < USERNUM // 2
        user = User(f"user_{i}", is_attacker)
        users.append(user)
    
    return builders, proposers, users

def update_stake(participant, profit: int):
    """Update participant stake with restaking."""
    participant.capital += profit
    
    # Apply reinvestment factor
    reinvested = int(profit * participant.reinvestment_factor)
    extracted = profit - reinvested
    participant.capital -= extracted
    
    # Update active stake
    participant.active_stake = VALIDATOR_THRESHOLD * (participant.capital // VALIDATOR_THRESHOLD)
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)

def get_stake_ratio(participant, total_stake):
    """Get participant's stake ratio."""
    return participant.active_stake / total_stake if total_stake > 0 else 0

def process_block(builders, proposers, users, block_num):
    """Process a single block efficiently."""
    # 1. Generate user transactions (simplified)
    all_transactions = []
    for user in users:
        num_tx = random.randint(0, 2)  # Reduced for speed
        for _ in range(num_tx):
            if user.is_attacker:
                tx = user.launch_attack(block_num)
            else:
                tx = user.create_transactions(block_num)
            if tx:
                all_transactions.append(tx)
    
    # 2. Distribute transactions to ALL participants (builders get them for potential building)
    for i, tx in enumerate(all_transactions):
        builder_idx = i % len(builders)
        builders[builder_idx].receive_transaction(tx)
    
    # 3. First select proposer based on stake weights
    all_participants = builders + proposers
    total_stake = sum(p.active_stake for p in all_participants)
    weights = [get_stake_ratio(p, total_stake) + 0.001 for p in all_participants]
    selected_proposer = random.choices(all_participants, weights=weights, k=1)[0]
    
    # 4. Check if selected proposer is a builder
    if selected_proposer in builders:
        # Builder-proposer case: they choose themselves as block builder
        winning_builder = selected_proposer
        
        # Builder selects their own transactions
        selected_txs = winning_builder.select_transactions(block_num)
        
        if selected_txs:
            # Calculate block value
            block_value = sum(tx.gas_fee for tx in selected_txs)
            if winning_builder.is_attacker:
                block_value += sum(getattr(tx, 'mev_potential', 0) for tx in selected_txs)
            
            winning_bid = block_value  # They get full block value
            
            # Builder-proposer gets full reward (no split)
            update_stake(winning_builder, int(winning_bid))
        else:
            return None
    else:
        # Pure proposer case: run proper auction with MEV strategies and reactive bidding
        auction_end = random.randint(8, MAX_ROUNDS)
        last_round_bids = [0.0] * len(builders)
        
        # Initialize builder strategies and bid history if not exists
        for builder in builders:
            if not hasattr(builder, 'strategy'):
                builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
            if not hasattr(builder, 'bid_history'):
                builder.bid_history = []
        
        for round_num in range(auction_end):
            round_bids = []
            
            for builder in builders:
                # Select transactions using MEV strategy
                selected_txs = builder.select_transactions(block_num)
                
                # Calculate block value (gas fees + MEV for attackers)
                if selected_txs:
                    gas_fee = sum(tx.gas_fee for tx in selected_txs)
                    mev_value = 0.0
                    if builder.is_attacker:
                        # MEV value from attack transactions targeting profitable txs
                        for tx in selected_txs:
                            if hasattr(tx, 'target_tx') and tx.target_tx:
                                mev_value += tx.target_tx.mev_potential
                    
                    block_value = gas_fee + mev_value
                    
                    # Reactive bidding strategy (from bidding.py)
                    if builder.strategy == "reactive":
                        highest_last_bid = max(last_round_bids, default=0.0)
                        my_last_bid = builder.bid_history[-1] if builder.bid_history else 0.0
                        second_highest_last_bid = sorted(last_round_bids, reverse=True)[1] if len(last_round_bids) > 1 else 0.0
                        
                        if my_last_bid < highest_last_bid:
                            bid = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
                        elif my_last_bid == highest_last_bid:
                            bid = my_last_bid + random.random() * (block_value - my_last_bid)
                        else:
                            bid = my_last_bid - 0.7 * (my_last_bid - second_highest_last_bid)
                    elif builder.strategy == "late_enter":
                        if round_num < random.randint(7, 10):  # Adjusted for MAX_ROUNDS=12
                            bid = 0.0
                        else:
                            highest_last_bid = max(last_round_bids, default=0.0)
                            bid = min(1.05 * highest_last_bid, block_value)
                    else:
                        bid = 0.5 * block_value
                    
                    # Ensure bid doesn't exceed block value
                    bid = max(0, min(bid, block_value))
                    
                    builder.bid_history.append(bid)
                else:
                    bid = 0.0
                    builder.bid_history.append(bid)
                
                round_bids.append(bid)
            
            last_round_bids = round_bids
        
        # Select winning builder
        if not last_round_bids or max(last_round_bids) == 0:
            return None
        
        winning_idx = last_round_bids.index(max(last_round_bids))
        winning_builder = builders[winning_idx]
        winning_bid = last_round_bids[winning_idx]
        
        # Split reward: 90% to builder, 10% to proposer
        builder_reward = int(winning_bid * 0.9)
        proposer_reward = int(winning_bid * 0.1)
        
        update_stake(winning_builder, builder_reward)
        update_stake(selected_proposer, proposer_reward)
    
    # 5. Clear mempools
    included_txs = winning_builder.selected_transactions
    for builder in builders:
        if hasattr(builder, 'clear_mempool'):
            builder.clear_mempool(block_num)
        else:
            # Simple mempool clearing
            if included_txs:
                included_ids = {tx.id for tx in included_txs}
                builder.mempool = [tx for tx in builder.mempool if tx.id not in included_ids]
    
    # 6. Create block data
    total_gas = sum(tx.gas_fee for tx in winning_builder.selected_transactions)
    total_mev = sum(getattr(tx, 'mev_potential', 0) for tx in winning_builder.selected_transactions)
    
    return {
        "block_num": block_num,
        "builder_id": winning_builder.id,
        "proposer_id": selected_proposer.id,
        "proposer_type": "builder" if selected_proposer in builders else "proposer",
        "builder_stake": winning_builder.active_stake,
        "proposer_stake": selected_proposer.active_stake,
        "builder_is_attacker": winning_builder.is_attacker,
        "total_gas_fee": total_gas,
        "total_mev_available": total_mev,
        "bid_value": winning_bid,
        "num_transactions": len(winning_builder.selected_transactions)
    }

def simulate_restaking_pbs():
    """Main simulation function."""
    print(f"Starting Simple Restaking PBS Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Participants: {BUILDERNUM} builders, {PROPOSERNUM} proposers, {USERNUM} users")
    
    # Create participants
    builders, proposers, users = create_participants()
    
    start_time = time.time()
    all_blocks = []
    
    # Process blocks
    for block_num in range(BLOCKNUM):
        block_data = process_block(builders, proposers, users, block_num)
        
        if block_data:
            all_blocks.append(block_data)
        
        # Progress reporting every 1000 blocks
        if (block_num + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            blocks_per_second = (block_num + 1) / elapsed
            remaining = (BLOCKNUM - block_num - 1) / blocks_per_second / 60
            
            print(f"Block {block_num + 1}/{BLOCKNUM} | "
                  f"Speed: {blocks_per_second:.1f} blocks/s | "
                  f"ETA: {remaining:.1f} min")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nCompleted in {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Speed: {BLOCKNUM/total_time:.1f} blocks/second")
    
    # Save results
    save_results(all_blocks, builders, proposers)
    
    return all_blocks

def save_results(block_data, builders, proposers):
    """Save results to CSV files."""
    output_dir = "data/same_seed/restaking_pbs/"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save block data
    if block_data:
        with open(f"{output_dir}restaking_pbs_blocks.csv", 'w', newline='') as f:
            fieldnames = block_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(block_data)
    
    # Save stake evolution
    with open(f"{output_dir}stake_evolution.csv", 'w', newline='') as f:
        fieldnames = ['participant_id', 'participant_type', 'is_attacker', 'reinvestment_factor',
                     'initial_stake', 'final_stake', 'total_profit']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for builder in builders:
            writer.writerow({
                'participant_id': builder.id,
                'participant_type': 'builder',
                'is_attacker': builder.is_attacker,
                'reinvestment_factor': builder.reinvestment_factor,
                'initial_stake': builder.stake_history[0],
                'final_stake': builder.active_stake,
                'total_profit': sum(builder.profit_history)
            })
        
        for proposer in proposers:
            writer.writerow({
                'participant_id': proposer.id,
                'participant_type': 'proposer',
                'is_attacker': False,
                'reinvestment_factor': proposer.reinvestment_factor,
                'initial_stake': proposer.stake_history[0],
                'final_stake': proposer.active_stake,
                'total_profit': sum(proposer.profit_history)
            })
    
    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    simulate_restaking_pbs()