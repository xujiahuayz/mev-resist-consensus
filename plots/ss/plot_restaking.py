#!/usr/bin/env python3
"""
Simple Restaking Plots: Validator, Builder, and Proposer Growth
Shows individual participant lines with color for attack status and shading for initial stake.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

def plot_validator_growth():
    """Plot individual validator growth lines."""
    print("Plotting validator growth...")
    
    # Load data
    pos_blocks = pd.read_csv('../../data/same_seed/restaking_pos/restaking_pos_blocks.csv')
    pos_stakes = pd.read_csv('../../data/same_seed/restaking_pos/stake_evolution.csv')
    
    # Merge data
    pos_data = pd.merge(pos_blocks, pos_stakes, left_on='validator_id', right_on='participant_id', how='left')
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot each validator individually
    for _, validator in pos_stakes.iterrows():
        validator_data = pos_data[pos_data['participant_id'] == validator['participant_id']]
        if len(validator_data) > 0:
            # Color: red for attacker, blue for non-attacker
            color = 'red' if validator['is_attacker'] else 'blue'
            # Alpha: based on initial stake (higher stake = more opaque)
            alpha = min(0.8, 0.3 + (validator['initial_stake'] / (256 * 1e9)) * 0.5)
            
            plt.plot(validator_data['block_num'], 
                    validator_data['validator_capital'] / 1e9,  # Convert to ETH
                    color=color, alpha=alpha, linewidth=1.5,
                    label=f"{'Attacker' if validator['is_attacker'] else 'Non-Attacker'} ({validator['initial_stake']/1e9:.0f} ETH)")
    
    plt.xlabel('Block Number')
    plt.ylabel('Stake (ETH)')
    plt.title('PoS Validator Growth Over Time')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('../../figures/restake/pos_validator_growth_simple.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pos_validator_growth_simple.png")

def plot_builder_growth():
    """Plot individual builder growth lines."""
    print("Plotting builder growth...")
    
    # Load data
    pbs_blocks = pd.read_csv('../../data/same_seed/restaking_pbs/restaking_pbs_blocks.csv')
    pbs_stakes = pd.read_csv('../../data/same_seed/restaking_pbs/stake_evolution.csv')
    
    # Filter for builders only
    builder_stakes = pbs_stakes[pbs_stakes['participant_id'].str.startswith('builder')]
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot each builder individually
    for _, builder in builder_stakes.iterrows():
        builder_data = pbs_blocks[pbs_blocks['builder_id'] == builder['participant_id']]
        if len(builder_data) > 0:
            # Color: red for attacker, blue for non-attacker
            color = 'red' if builder['is_attacker'] else 'blue'
            # Alpha: based on initial stake (higher stake = more opaque)
            alpha = min(0.8, 0.3 + (builder['initial_stake'] / (256 * 1e9)) * 0.5)
            
            plt.plot(builder_data['block_num'], 
                    builder_data['builder_stake'] / 1e9,  # Convert to ETH
                    color=color, alpha=alpha, linewidth=1.5,
                    label=f"{'Attacker' if builder['is_attacker'] else 'Non-Attacker'} ({builder['initial_stake']/1e9:.0f} ETH)")
    
    plt.xlabel('Block Number')
    plt.ylabel('Stake (ETH)')
    plt.title('PBS Builder Growth Over Time')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('../../figures/restake/pbs_builder_growth_simple.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_builder_growth_simple.png")

def plot_proposer_growth():
    """Plot individual proposer growth lines."""
    print("Plotting proposer growth...")
    
    # Load data
    pbs_blocks = pd.read_csv('../../data/same_seed/restaking_pbs/restaking_pbs_blocks.csv')
    pbs_stakes = pd.read_csv('../../data/same_seed/restaking_pbs/stake_evolution.csv')
    
    # Filter for proposers only
    proposer_stakes = pbs_stakes[pbs_stakes['participant_id'].str.startswith('proposer')]
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot each proposer individually
    for _, proposer in proposer_stakes.iterrows():
        proposer_data = pbs_blocks[pbs_blocks['proposer_id'] == proposer['participant_id']]
        if len(proposer_data) > 0:
            # Color: red for attacker, blue for non-attacker
            color = 'red' if proposer['is_attacker'] else 'blue'
            # Alpha: based on initial stake (higher stake = more opaque)
            alpha = min(0.8, 0.3 + (proposer['initial_stake'] / (256 * 1e9)) * 0.5)
            
            plt.plot(proposer_data['block_num'], 
                    proposer_data['proposer_stake'] / 1e9,  # Convert to ETH
                    color=color, alpha=alpha, linewidth=1.5,
                    label=f"{'Attacker' if proposer['is_attacker'] else 'Non-Attacker'} ({proposer['initial_stake']/1e9:.0f} ETH)")
    
    plt.xlabel('Block Number')
    plt.ylabel('Stake (ETH)')
    plt.title('PBS Proposer Growth Over Time')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('../../figures/restake/pbs_proposer_growth_simple.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_proposer_growth_simple.png")

def main():
    """Generate all three plots."""
    print("Generating simple restaking plots...")
    
    # Create figures/restake directory
    figures_dir = Path('../../figures/restake')
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plots
    plot_validator_growth()
    plot_builder_growth()
    plot_proposer_growth()
    
    print("All plots completed!")

if __name__ == "__main__":
    main()
