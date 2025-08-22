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

BLOCKNUM = 10000
BLOCK_CAP = 100
USERNUM = 100
BUILDERNUM = 50
PROPOSERNUM = 50
AUCTION_ROUNDS = 5

VALIDATOR_THRESHOLD = 32 * 10**9
MIN_VALIDATOR_NODES = 1

random.seed(16)

def create_participants_with_config(attacker_builders, attacker_users):
    builders = []
    
    # Define specific stake levels with guaranteed attack/benign distribution
    stake_levels = [
        (8, 1, 1),  # 8 ETH: 1 attack, 1 benign
        (5, 1, 1),  # 5 ETH: 1 attack, 1 benign  
        (3, 1, 1),  # 3 ETH: 1 attack, 1 benign
        (2, 1, 1),  # 2 ETH: 1 attack, 1 benign
    ]
    
    builder_count = 0
    attack_count = 0
    benign_count = 0
    
    # Create builders with specific stake levels first
    for stake_multiplier, num_attack, num_benign in stake_levels:
        initial_stake = VALIDATOR_THRESHOLD * stake_multiplier
        
        # Create attack builders for this stake level
        for _ in range(num_attack):
            if builder_count >= BUILDERNUM:
                break
            builder = Builder(f"builder_{builder_count}", True)  # is_attacker = True
            builder.capital = initial_stake
            builder.active_stake = initial_stake
            builder.initial_stake = initial_stake
            builder.reinvestment_factor = 1.0
            builder.profit_history = []
            builder.stake_history = [builder.capital]
            builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
            builder.bid_history = []
            builder.mempool = []
            builder.selected_transactions = []
            builders.append(builder)
            builder_count += 1
            attack_count += 1
        
        # Create benign builders for this stake level
        for _ in range(num_benign):
            if builder_count >= BUILDERNUM:
                break
            builder = Builder(f"builder_{builder_count}", False)  # is_attacker = False
            builder.capital = initial_stake
            builder.active_stake = initial_stake
            builder.initial_stake = initial_stake
            builder.reinvestment_factor = 1.0
            builder.profit_history = []
            builder.stake_history = [builder.capital]
            builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
            builder.bid_history = []
            builder.mempool = []
            builder.selected_transactions = []
            builders.append(builder)
            builder_count += 1
            benign_count += 1
    
    # Fill remaining builder slots with 1 ETH stake builders
    # Ensure we maintain the requested attack/benign ratio for remaining slots
    remaining_slots = BUILDERNUM - builder_count
    remaining_attack_needed = attacker_builders - attack_count
    remaining_benign_needed = (BUILDERNUM - attacker_builders) - benign_count
    
    # Create remaining attack builders with 1 ETH stake
    for _ in range(min(remaining_attack_needed, remaining_slots)):
        if builder_count >= BUILDERNUM:
            break
        builder = Builder(f"builder_{builder_count}", True)
        builder.capital = VALIDATOR_THRESHOLD  # 1 ETH
        builder.active_stake = VALIDATOR_THRESHOLD
        builder.initial_stake = VALIDATOR_THRESHOLD
        builder.reinvestment_factor = 1.0
        builder.profit_history = []
        builder.stake_history = [builder.capital]
        builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
        builder.bid_history = []
        builder.mempool = []
        builder.selected_transactions = []
        builders.append(builder)
        builder_count += 1
    
    # Create remaining benign builders with 1 ETH stake
    for _ in range(min(remaining_benign_needed, BUILDERNUM - builder_count)):
        if builder_count >= BUILDERNUM:
            break
        builder = Builder(f"builder_{builder_count}", False)
        builder.capital = VALIDATOR_THRESHOLD  # 1 ETH
        builder.active_stake = VALIDATOR_THRESHOLD
        builder.initial_stake = VALIDATOR_THRESHOLD
        builder.reinvestment_factor = 1.0
        builder.profit_history = []
        builder.stake_history = [builder.capital]
        builder.strategy = "reactive" if random.random() < 0.7 else "late_enter"
        builder.bid_history = []
        builder.mempool = []
        builder.selected_transactions = []
        builders.append(builder)
        builder_count += 1
    
    proposers = []
    
    # Define proposer stake levels (no attack/benign distinction)
    proposer_stake_levels = [8, 5, 3, 2]  # ETH values
    
    proposer_count = 0
    
    # Create proposers with specific stake levels first
    for stake_multiplier in proposer_stake_levels:
        if proposer_count >= PROPOSERNUM:
            break
        initial_stake = VALIDATOR_THRESHOLD * stake_multiplier
        
        proposer = Proposer(f"proposer_{proposer_count}")
        proposer.capital = initial_stake
        proposer.active_stake = initial_stake
        proposer.initial_stake = initial_stake
        proposer.reinvestment_factor = 1.0
        proposer.profit_history = []
        proposer.stake_history = [proposer.capital]
        proposers.append(proposer)
        proposer_count += 1
    
    # Fill remaining proposer slots with 1 ETH stake
    for _ in range(PROPOSERNUM - proposer_count):
        proposer = Proposer(f"proposer_{proposer_count}")
        proposer.capital = VALIDATOR_THRESHOLD  # 1 ETH
        proposer.active_stake = VALIDATOR_THRESHOLD
        proposer.initial_stake = VALIDATOR_THRESHOLD
        proposer.reinvestment_factor = 1.0
        proposer.profit_history = []
        proposer.stake_history = [proposer.capital]
        proposers.append(proposer)
        proposer_count += 1
    
    users = []
    for i in range(USERNUM):
        is_attacker = i < attacker_users
        user = User(f"user_{i}", is_attacker)
        users.append(user)
    
    return builders, proposers, users

def get_validator_nodes(participants):
    nodes = []
    for participant in participants:
        num_nodes = participant.active_stake // VALIDATOR_THRESHOLD
        if num_nodes >= MIN_VALIDATOR_NODES:
            for _ in range(num_nodes):
                nodes.append(participant)
    return nodes

def update_stake(participant, profit: int):
    if profit <= 0:
        return
    
    old_capital = participant.capital
    old_stake = participant.active_stake
    old_validator_nodes = participant.active_stake // VALIDATOR_THRESHOLD
    
    participant.capital += profit
    
    new_validator_nodes = participant.capital // VALIDATOR_THRESHOLD
    participant.active_stake = new_validator_nodes * VALIDATOR_THRESHOLD
    
    participant.profit_history.append(profit)
    participant.stake_history.append(participant.active_stake)
    
    if len(participant.profit_history) > 1000:
        participant.profit_history = participant.profit_history[-500:]
        participant.stake_history = participant.stake_history[-500:]
    
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
    all_participants = builders + proposers
    
    stakes = [p.active_stake for p in all_participants]
    total_stake = sum(stakes)
    
    if total_stake == 0:
        return {'gini': 0, 'hhi': 0, 'top_5_share': 0, 'total_stake_eth': 0}
    
    sorted_stakes = sorted(stakes, reverse=True)
    
    top_5_share = sum(sorted_stakes[:5]) / total_stake * 100
    
    market_shares = [stake / total_stake for stake in stakes]
    hhi = sum(share ** 2 for share in market_shares) * 10000
    
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
    if not selected_transactions:
        return 0.0
    
    gas_fee = sum(tx.gas_fee for tx in selected_transactions)
    
    mev_value = 0.0
    if builder.is_attacker:
        for tx in selected_transactions:
            if hasattr(tx, 'target_tx') and tx.target_tx:
                mev_value += tx.target_tx.mev_potential
    
    return gas_fee + mev_value

def clear_mempool_efficiently(builder, included_tx_ids: Set[int]):
    remaining_txs = [tx for tx in builder.mempool if tx.id not in included_tx_ids]
    builder.mempool.clear()
    builder.mempool.extend(remaining_txs)
    
    if len(builder.mempool) > 10000:
        builder.mempool = list(builder.mempool)[-5000:]

def process_block(builders, proposers, users, block_num):
    # First, create transactions and add them to ALL builders' mempools
    for user in users:
        tx_count = random.randint(1, 5)
        for _ in range(tx_count):
            if user.is_attacker:
                tx = user.launch_attack(block_num)
            else:
                tx = user.create_transactions(block_num)
            
            if tx:
                # Add transaction to ALL builders' mempools (not just the selected validator)
                for builder in builders:
                    builder.mempool.append(tx)
    
    all_staking_participants = builders + proposers
    validator_nodes = get_validator_nodes(all_staking_participants)
    
    if not validator_nodes:
        return None
    
    selected_validator = random.choice(validator_nodes)
    
    winning_builder = None
    winning_bid = 0.0
    validator_type = ""
    
    if selected_validator in builders:
        winning_builder = selected_validator
        winning_builder.selected_transactions = winning_builder.select_transactions(block_num)
        
        if not winning_builder.selected_transactions:
            return None
        
        block_value = calculate_block_value(winning_builder, winning_builder.selected_transactions)
        
        if block_value > 0:
            update_stake(winning_builder, int(block_value))
        
        winning_bid = 0.0
        validator_type = "builder"
        
    else:
        auction_rounds = AUCTION_ROUNDS
        
        builder_selections = []
        for builder in builders:
            builder.selected_transactions = builder.select_transactions(block_num)
            block_value = calculate_block_value(builder, builder.selected_transactions)
            builder_selections.append((builder, block_value))
        
        last_round_bids = [0.0] * len(builders)
        
        for round_num in range(auction_rounds):
            round_bids = []
            
            for i, (builder, block_value) in enumerate(builder_selections):
                if block_value > 0:
                    if round_num == 0:
                        bid = block_value * 0.5
                    else:
                        highest_last_bid = max(last_round_bids) if last_round_bids else 0.0
                        
                        my_last_bid = last_round_bids[i] if i < len(last_round_bids) else 0.0
                        
                        if len(last_round_bids) > 1:
                            sorted_bids = sorted(last_round_bids, reverse=True)
                            second_highest_last_bid = sorted_bids[1]
                        else:
                            second_highest_last_bid = 0.0
                        
                        if my_last_bid < highest_last_bid:
                            bid = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
                        elif my_last_bid == highest_last_bid:
                            bid = my_last_bid + random.random() * (block_value - my_last_bid)
                        else:
                            bid = my_last_bid - 0.7 * (my_last_bid - second_highest_last_bid)
                        
                        bid = max(0.0, min(bid, block_value * 0.9))
                    
                    round_bids.append(bid)
                else:
                    round_bids.append(0.0)
            
            last_round_bids = round_bids
        
        if not last_round_bids or max(last_round_bids) == 0:
            return None
        
        winning_bid = max(last_round_bids)
        winning_builder_idx = last_round_bids.index(winning_bid)
        winning_builder = builder_selections[winning_builder_idx][0]
        
        if winning_bid > 0:
            update_stake(selected_validator, int(winning_bid))
            
            block_value = builder_selections[winning_builder_idx][1]
            builder_profit = block_value - winning_bid
            if builder_profit > 0:
                update_stake(winning_builder, int(builder_profit))
        
        validator_type = "proposer"
    
    if winning_builder and winning_builder.selected_transactions:
        included_tx_ids = {tx.id for tx in winning_builder.selected_transactions}
        for builder in builders:
            clear_mempool_efficiently(builder, included_tx_ids)
    
    centralization_metrics = calculate_centralization_metrics(builders, proposers)
    
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
                'is_attacker': False,
                'initial_stake_eth': proposer.initial_stake / 1e9,
                'final_stake_eth': proposer.active_stake / 1e9,
                'final_capital_eth': proposer.capital / 1e9,
                'initial_nodes': proposer.initial_stake // VALIDATOR_THRESHOLD,
                'final_nodes': proposer.active_stake // VALIDATOR_THRESHOLD,
                'total_profit_eth': sum(proposer.profit_history) / 1e9,
                'growth_rate': growth_rate
            })

def save_metrics_evolution(metrics_history, attacker_builders, attacker_users):
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
    all_participants = builders + proposers
    
    for participant in all_participants:
        participant_block_data = {
            'block_num': block_num,
            'participant_id': participant.id,
            'participant_type': 'builder' if participant in builders else 'proposer',
            'is_attacker': getattr(participant, 'is_attacker', False),
            'current_stake': participant.active_stake,
            'current_capital': participant.capital,
            'current_nodes': participant.active_stake // VALIDATOR_THRESHOLD
        }
        continuous_stake_data.append(participant_block_data)

def save_continuous_stake_data(continuous_stake_data, attacker_builders, attacker_users):
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
    print(f"Starting PBS Restaking Simulation")
    print(f"Blocks: {BLOCKNUM}")
    print(f"Attackers: {attacker_builders}/{BUILDERNUM} builders, {attacker_users}/{USERNUM} users")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD / 1e9:.1f} ETH")
    print(f"Auction rounds: {AUCTION_ROUNDS}")
    print("="*70)
    
    builders, proposers, users = create_participants_with_config(attacker_builders, attacker_users)
    
    block_data_list = []
    continuous_stake_data = []
    metrics_history = []
    
    start_time = time.time()
    
    for block_num in range(BLOCKNUM):
        block_data = process_block(builders, proposers, users, block_num)
        
        if block_data:
            block_data_list.append(block_data)
            
            metrics = {
                'gini': block_data['gini_coefficient'],
                'hhi': block_data['hhi'],
                'top_5_share': block_data['top_5_share'],
                'total_stake_eth': block_data['total_stake_eth']
            }
            metrics_history.append(metrics)
        
        record_continuous_stake_data(builders, proposers, block_num, continuous_stake_data)
        
        if block_num % 100 == 0:
            print(f"Processed block {block_num}/{BLOCKNUM}")
    
    end_time = time.time()
    
    save_block_data(block_data_list, attacker_builders, attacker_users)
    save_continuous_stake_data(continuous_stake_data, attacker_builders, attacker_users)
    save_participant_evolution(builders, proposers, attacker_builders, attacker_users)
    save_metrics_evolution(metrics_history, attacker_builders, attacker_users)
    
    print(f"\nSimulation completed in {end_time - start_time:.2f} seconds")
    
    final_metrics = calculate_centralization_metrics(builders, proposers)
    print(f"\nFinal Centralization Metrics:")
    print(f"Gini Coefficient: {final_metrics['gini']:.4f}")
    print(f"HHI: {final_metrics['hhi']:.0f}")
    print(f"Top 5 Concentration: {final_metrics['top_5_share']:.2f}%")
    print(f"Total Stake: {final_metrics['total_stake_eth']:.1f} ETH")
    
    attack_builders = [b for b in builders if b.is_attacker]
    non_attack_builders = [b for b in builders if not b.is_attacker]
    
    if attack_builders and non_attack_builders:
        avg_attack_growth = sum((b.capital - b.initial_stake) / b.initial_stake for b in attack_builders) / len(attack_builders)
        avg_non_attack_growth = sum((b.capital - b.initial_stake) / b.initial_stake for b in non_attack_builders) / len(non_attack_builders)
        
        print(f"\nBuilder Growth Analysis:")
        print(f"Attack builders average growth: {avg_attack_growth * 100:.2f}%")
        print(f"Non-attack builders average growth: {avg_non_attack_growth * 100:.2f}%")
        print(f"Attack advantage: {(avg_attack_growth - avg_non_attack_growth) * 100:.2f} percentage points")
    
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