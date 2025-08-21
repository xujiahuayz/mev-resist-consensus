#!/usr/bin/env python3
"""
Seaborn-based Restaking Plots: Three separate plots for PoS, PBS Builders, and PBS Proposers
Shows stake evolution over time with flare/crest color schemes for attack vs non-attack.
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
    
    # Get unique validators and sample a few from each stake level
    validators = pos_blocks.groupby('validator_id').agg({
        'validator_capital': 'first',
        'is_attacker': 'first'
    }).reset_index()
    
    # Sample validators by attack status and initial stake
    attack_validators = validators[validators['is_attacker'] == True]
    nonattack_validators = validators[validators['is_attacker'] == False]
    
    # Sample 3 from each category
    sampled_attack = attack_validators.sample(min(3, len(attack_validators)))['validator_id'].tolist()
    sampled_nonattack = nonattack_validators.sample(min(3, len(nonattack_validators)))['validator_id'].tolist()
    
    all_sampled = sampled_attack + sampled_nonattack
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each sampled validator
    for validator_id in all_sampled:
        validator_data = pos_blocks[pos_blocks['validator_id'] == validator_id]
        validator_info = validators[validators['validator_id'] == validator_id].iloc[0]
        
        is_attacker = validator_info['is_attacker']
        initial_capital = validator_info['validator_capital'] / 1e9  # Convert to ETH
        
        # Determine color based on attack status and initial stake
        if is_attacker:
            color_idx = min(4, int((initial_capital / 256) * 4))
            color = attack_colors[color_idx]
            label_prefix = "Attack"
        else:
            color_idx = min(4, int((initial_capital / 256) * 4))
            color = nonattack_colors[color_idx]
            label_prefix = "Non-Attack"
        
        label = f"{label_prefix} Validator ({initial_capital:.0f} ETH)"
        
        # Plot stake evolution (convert to ETH)
        sns.lineplot(data=validator_data, 
                    x='block_num', 
                    y=validator_data['validator_capital'] / 1e9,
                    color=color,
                    linewidth=2.5,
                    alpha=0.8,
                    label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Validator Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PoS Validator Stake Evolution Over Time\n' +
              'Flare (Attack) vs Crest (Non-Attack) Color Schemes', 
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
    
    # Sample builders by attack status
    attack_builders = builders[builders['is_attacker'] == True]
    nonattack_builders = builders[builders['is_attacker'] == False]
    
    sampled_attack = attack_builders.sample(min(3, len(attack_builders)))['participant_id'].tolist()
    sampled_nonattack = nonattack_builders.sample(min(3, len(nonattack_builders)))['participant_id'].tolist()
    
    all_sampled = sampled_attack + sampled_nonattack
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each sampled builder
    for participant_id in all_sampled:
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        validator_blocks = pbs_blocks[pbs_blocks['validator_id'] == participant_id]
        
        if len(validator_blocks) > 0:
            is_attacker = participant_info['is_attacker']
            initial_stake = participant_info['initial_stake_eth']
            
            # Determine color based on attack status and initial stake
            if is_attacker:
                color_idx = min(4, int((initial_stake / 256) * 4))
                color = attack_colors[color_idx]
                label_prefix = "Attack"
            else:
                color_idx = min(4, int((initial_stake / 256) * 4))
                color = nonattack_colors[color_idx]
                label_prefix = "Non-Attack"
            
            label = f"{label_prefix} Builder ({initial_stake:.0f} ETH)"
            
            # Plot stake evolution (convert to ETH)
            sns.lineplot(data=validator_blocks, 
                        x='block_num', 
                        y=validator_blocks['validator_stake'] / 1e9,
                        color=color,
                        linewidth=2.5,
                        alpha=0.8,
                        label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Builder Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PBS Builder Stake Evolution Over Time\n' +
              'Flare (Attack) vs Crest (Non-Attack) Color Schemes', 
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
    
    # Filter for proposers only (all non-attack in this simulation)
    proposers = participants_df[participants_df['participant_type'] == 'proposer']
    
    # Sample proposers
    sampled_proposers = proposers.sample(min(6, len(proposers)))['participant_id'].tolist()
    
    # Create the plot
    plt.figure(figsize=(16, 10))
    
    # Color palette: crest for non-attackers (all proposers are non-attack)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot each sampled proposer
    for participant_id in sampled_proposers:
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        validator_blocks = pbs_blocks[pbs_blocks['validator_id'] == participant_id]
        
        if len(validator_blocks) > 0:
            initial_stake = participant_info['initial_stake_eth']
            
            # Determine color based on initial stake
            color_idx = min(4, int((initial_stake / 256) * 4))
            color = nonattack_colors[color_idx]
            
            label = f"Proposer ({initial_stake:.0f} ETH)"
            
            # Plot stake evolution (convert to ETH)
            sns.lineplot(data=validator_blocks, 
                        x='block_num', 
                        y=validator_blocks['validator_stake'] / 1e9,
                        color=color,
                        linewidth=2.5,
                        alpha=0.8,
                        label=label)
    
    # Customize the plot
    plt.xlabel('Block Number', fontsize=14, fontweight='bold')
    plt.ylabel('Proposer Stake (ETH)', fontsize=14, fontweight='bold')
    plt.title('PBS Proposer Stake Evolution Over Time\n' +
              'Crest Color Scheme (All Non-Attack)', 
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