#!/usr/bin/env python3
"""
Seaborn-based Restaking Plots: Simple stake evolution for different initial stake levels
Shows one participant for each initial stake level (32, 64, 96, 160, 256 ETH).
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set Seaborn style
sns.set_style("whitegrid")

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

def plot_pos_validators():
    """Create PoS validator stake evolution plot."""
    print("Creating PoS validator stake evolution plot...")
    
    # Load PoS data
    pos_blocks = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pos/restaking_pos_blocks.csv')
    
    # Get unique validators with their initial stakes
    validators = pos_blocks.groupby('validator_id').agg({
        'validator_capital': 'first',
        'is_attacker': 'first'
    }).reset_index()
    
    # Convert to ETH
    validators['initial_stake_eth'] = validators['validator_capital'] / 1e9
    
    # Find one attack and one non-attack validator for each stake level
    stake_levels = [32, 64, 96, 160, 256]
    selected_validators = []
    
    for stake in stake_levels:
        # Find attack validators close to this stake level
        attack_candidates = validators[(validators['is_attacker'] == True) & 
                                     (abs(validators['initial_stake_eth'] - stake) < 10)]
        if len(attack_candidates) > 0:
            selected_validators.append(attack_candidates.iloc[0])
        
        # Find non-attack validators close to this stake level
        nonattack_candidates = validators[(validators['is_attacker'] == False) & 
                                        (abs(validators['initial_stake_eth'] - stake) < 10)]
        if len(nonattack_candidates) > 0:
            selected_validators.append(nonattack_candidates.iloc[0])
    
    if len(selected_validators) == 0:
        print("No validators found with expected stake levels")
        return
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each selected validator
    for i, validator in enumerate(selected_validators):
        validator_id = validator['validator_id']
        validator_data = pos_blocks[pos_blocks['validator_id'] == validator_id]
        
        is_attacker = validator['is_attacker']
        initial_stake = validator['initial_stake_eth']
        
        # Create complete dataset for every block (0-10000)
        # Start with all blocks from 0 to max block in data
        max_block = validator_data['block_num'].max()
        all_blocks = pd.DataFrame({'block_num': range(0, max_block + 1)})
        
        # Merge with actual data and forward fill missing values
        complete_data = all_blocks.merge(validator_data[['block_num', 'validator_capital']], 
                                       on='block_num', how='left')
        complete_data['validator_capital'] = complete_data['validator_capital'].fillna(method='ffill')
        
        # Determine color based on attack status
        if is_attacker:
            color = attack_colors[i % len(attack_colors)]
            label_prefix = "Attack"
        else:
            color = nonattack_colors[i % len(nonattack_colors)]
            label_prefix = "Non-Attack"
        
        label = f"{label_prefix} Validator ({initial_stake:.0f} ETH)"
        
        # Plot total stake over time (convert to ETH) - now with complete data
        plt.plot(complete_data['block_num'], 
                complete_data['validator_capital'] / 1e9,
                color=color, linewidth=2.5, alpha=0.8, label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Total Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PoS Validator Stake Evolution: Attack vs Non-Attack per Initial Stake Level\n' +
              'Flare (Attack) vs Crest (Non-Attack) Color Schemes - Complete Block Coverage', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pos_validator_stake_evolution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pos_validator_stake_evolution.png")

def plot_pbs_builders():
    """Create PBS builder stake evolution plot."""
    print("Creating PBS builder stake evolution plot...")
    
    # Load PBS data
    participants_df = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    pbs_blocks = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_blocks_builders25_users50.csv')
    
    # Filter for builders only
    builders = participants_df[participants_df['participant_type'] == 'builder']
    
    # Find one attack and one non-attack builder for each stake level
    stake_levels = [32, 64, 96, 160, 256]
    selected_builders = []
    
    for stake in stake_levels:
        # Find attack builders close to this stake level
        attack_candidates = builders[(builders['is_attacker'] == True) & 
                                   (abs(builders['initial_stake_eth'] - stake) < 10)]
        if len(attack_candidates) > 0:
            selected_builders.append(attack_candidates.iloc[0])
        
        # Find non-attack builders close to this stake level
        nonattack_candidates = builders[(builders['is_attacker'] == False) & 
                                      (abs(builders['initial_stake_eth'] - stake) < 10)]
        if len(nonattack_candidates) > 0:
            selected_builders.append(nonattack_candidates.iloc[0])
    
    if len(selected_builders) == 0:
        print("No builders found with expected stake levels")
        return
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each selected builder
    for i, builder in enumerate(selected_builders):
        builder_id = builder['participant_id']
        builder_data = pbs_blocks[pbs_blocks['validator_id'] == builder_id]
        
        if len(builder_data) > 0:
            is_attacker = builder['is_attacker']
            initial_stake = builder['initial_stake_eth']
            
            # Create complete dataset for every block (0-10000)
            # Start with all blocks from 0 to max block in data
            max_block = builder_data['block_num'].max()
            all_blocks = pd.DataFrame({'block_num': range(0, max_block + 1)})
            
            # Merge with actual data and forward fill missing values
            complete_data = all_blocks.merge(builder_data[['block_num', 'validator_stake']], 
                                           on='block_num', how='left')
            complete_data['validator_stake'] = complete_data['validator_stake'].fillna(method='ffill')
            
            # Determine color based on attack status
            if is_attacker:
                color = attack_colors[i % len(attack_colors)]
                label_prefix = "Attack"
            else:
                color = nonattack_colors[i % len(nonattack_colors)]
                label_prefix = "Non-Attack"
            
            label = f"{label_prefix} Builder ({initial_stake:.0f} ETH)"
            
            # Plot total stake over time (convert to ETH) - now with complete data
            plt.plot(complete_data['block_num'], 
                    complete_data['validator_stake'] / 1e9,
                    color=color, linewidth=2.5, alpha=0.8, label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Total Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PBS Builder Stake Evolution: Attack vs Non-Attack per Initial Stake Level\n' +
              'Flare (Attack) vs Crest (Non-Attack) Color Schemes - Complete Block Coverage', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_builder_stake_evolution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_builder_stake_evolution.png")

def plot_pbs_proposers():
    """Create PBS proposer stake evolution plot."""
    print("Creating PBS proposer stake evolution plot...")
    
    # Load PBS data
    participants_df = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    pbs_blocks = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_blocks_builders25_users50.csv')
    
    # Filter for proposers only
    proposers = participants_df[participants_df['participant_type'] == 'proposer']
    
    # Find one attack and one non-attack proposer for each stake level
    stake_levels = [32, 64, 96, 160, 256]
    selected_proposers = []
    
    for stake in stake_levels:
        # Find attack proposers close to this stake level
        attack_candidates = proposers[(proposers['is_attacker'] == True) & 
                                    (abs(proposers['initial_stake_eth'] - stake) < 10)]
        if len(attack_candidates) > 0:
            selected_proposers.append(attack_candidates.iloc[0])
        
        # Find non-attack proposers close to this stake level
        nonattack_candidates = proposers[(proposers['is_attacker'] == False) & 
                                       (abs(proposers['initial_stake_eth'] - stake) < 10)]
        if len(nonattack_candidates) > 0:
            selected_proposers.append(nonattack_candidates.iloc[0])
    
    if len(selected_proposers) == 0:
        print("No proposers found with expected stake levels")
        return
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each selected proposer
    for i, proposer in enumerate(selected_proposers):
        proposer_id = proposer['participant_id']
        proposer_data = pbs_blocks[pbs_blocks['validator_id'] == proposer_id]
        
        if len(proposer_data) > 0:
            is_attacker = proposer['is_attacker']
            initial_stake = proposer['initial_stake_eth']
            
            # Create complete dataset for every block (0-10000)
            # Start with all blocks from 0 to max block in data
            max_block = proposer_data['block_num'].max()
            all_blocks = pd.DataFrame({'block_num': range(0, max_block + 1)})
            
            # Merge with actual data and forward fill missing values
            complete_data = all_blocks.merge(proposer_data[['block_num', 'validator_stake']], 
                                           on='block_num', how='left')
            complete_data['validator_stake'] = complete_data['validator_stake'].fillna(method='ffill')
            
            # Determine color based on attack status
            if is_attacker:
                color = attack_colors[i % len(attack_colors)]
                label_prefix = "Attack"
            else:
                color = nonattack_colors[i % len(nonattack_colors)]
                label_prefix = "Non-Attack"
            
            label = f"{label_prefix} Proposer ({initial_stake:.0f} ETH)"
            
            # Plot total stake over time (convert to ETH) - now with complete data
            plt.plot(complete_data['block_num'], 
                    complete_data['validator_stake'] / 1e9,
                    color=color, linewidth=2.5, alpha=0.8, label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Total Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PBS Proposer Stake Evolution: Attack vs Non-Attack per Initial Stake Level\n' +
              'Flare (Attack) vs Crest (Non-Attack) Color Schemes - Complete Block Coverage', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_proposer_stake_evolution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_proposer_stake_evolution.png")

def main():
    """Generate all three Seaborn-based plots."""
    print("Generating three separate stake evolution plots...")
    
    # Create figures/restake directory
    figures_dir = PROJECT_ROOT / 'figures/restake'
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all three plots
    plot_pos_validators()
    plot_pbs_builders()
    plot_pbs_proposers()
    
    print("All three plots completed!")

if __name__ == "__main__":
    main() 