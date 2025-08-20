#!/usr/bin/env python3
"""
Updated Restaking PBS Plots: Validator, Builder, and Proposer Growth
Shows individual participant lines with color for attack status and shading for initial stake.
Uses the new data format from the 10,000 block simulation.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

def plot_builder_growth():
    """Plot individual builder growth lines from new data."""
    print("Plotting builder growth from new data...")
    
    # Load new data
    pbs_blocks = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_blocks_builders25_users50.csv')
    pbs_participants = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    
    # Filter for builders only
    builder_participants = pbs_participants[pbs_participants['participant_type'] == 'builder']
    
    # Create plot
    plt.figure(figsize=(14, 10))
    
    # Plot each builder individually
    for _, builder in builder_participants.iterrows():
        builder_id = builder['participant_id']
        builder_data = pbs_blocks[pbs_blocks['winning_builder_id'] == builder_id]
        
        if len(builder_data) > 0:
            # Color: red for attacker, blue for non-attacker
            color = 'red' if builder['is_attacker'] else 'blue'
            # Alpha: based on initial stake (higher stake = more opaque)
            initial_stake_eth = builder['initial_stake_eth']
            alpha = min(0.8, 0.3 + (initial_stake_eth / 256) * 0.5)
            
            # Get validator stake data for this builder
            validator_data = pbs_blocks[pbs_blocks['validator_id'] == builder_id]
            if len(validator_data) > 0:
                plt.plot(validator_data['block_num'], 
                        validator_data['validator_stake'] / 1e9,  # Convert to ETH
                        color=color, alpha=alpha, linewidth=1.5,
                        label=f"{'Attacker' if builder['is_attacker'] else 'Non-Attacker'} ({initial_stake_eth:.0f} ETH)")
    
    plt.xlabel('Block Number')
    plt.ylabel('Stake (ETH)')
    plt.title('PBS Builder Growth Over Time (10,000 Blocks)\n25 Attack Builders, 50 Attack Users')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_builder_growth_new.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_builder_growth_new.png")

def plot_proposer_growth():
    """Plot individual proposer growth lines from new data."""
    print("Plotting proposer growth from new data...")
    
    # Load new data
    pbs_blocks = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_blocks_builders25_users50.csv')
    pbs_participants = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    
    # Filter for proposers only
    proposer_participants = pbs_participants[pbs_participants['participant_type'] == 'proposer']
    
    # Create plot
    plt.figure(figsize=(14, 10))
    
    # Plot each proposer individually
    for _, proposer in proposer_participants.iterrows():
        proposer_id = proposer['participant_id']
        proposer_data = pbs_blocks[pbs_blocks['validator_id'] == proposer_id]
        
        if len(proposer_data) > 0:
            # Color: blue for proposers (they're all non-attackers)
            color = 'blue'
            # Alpha: based on initial stake (higher stake = more opaque)
            initial_stake_eth = proposer['initial_stake_eth']
            alpha = min(0.8, 0.3 + (initial_stake_eth / 256) * 0.5)
            
            plt.plot(proposer_data['block_num'], 
                    proposer_data['validator_stake'] / 1e9,  # Convert to ETH
                    color=color, alpha=alpha, linewidth=1.5,
                    label=f"Proposer ({initial_stake_eth:.0f} ETH)")
    
    plt.xlabel('Block Number')
    plt.ylabel('Stake (ETH)')
    plt.title('PBS Proposer Growth Over Time (10,000 Blocks)\n25 Attack Builders, 50 Attack Users')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_proposer_growth_new.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_proposer_growth_new.png")

def plot_centralization_metrics():
    """Plot centralization metrics over time."""
    print("Plotting centralization metrics...")
    
    # Load new data
    pbs_blocks = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_blocks_builders25_users50.csv')
    
    # Create subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    # Plot Gini coefficient
    ax1.plot(pbs_blocks['block_num'], pbs_blocks['gini_coefficient'], 'b-', linewidth=2)
    ax1.set_ylabel('Gini Coefficient')
    ax1.set_title('Gini Coefficient Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Plot HHI
    ax2.plot(pbs_blocks['block_num'], pbs_blocks['hhi'], 'r-', linewidth=2)
    ax2.set_ylabel('HHI')
    ax2.set_title('Herfindahl-Hirschman Index Over Time')
    ax2.grid(True, alpha=0.3)
    
    # Plot Top 5 concentration
    ax3.plot(pbs_blocks['block_num'], pbs_blocks['top_5_share'] * 100, 'g-', linewidth=2)
    ax3.set_xlabel('Block Number')
    ax3.set_ylabel('Top 5 Share (%)')
    ax3.set_title('Top 5 Concentration Over Time')
    ax3.grid(True, alpha=0.3)
    
    plt.suptitle('Centralization Metrics Over Time (10,000 Blocks)\n25 Attack Builders, 50 Attack Users', fontsize=16)
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/centralization_metrics_new.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: centralization_metrics_new.png")

def plot_attack_vs_nonattack_comparison():
    """Plot comparison of attack vs non-attack builder performance."""
    print("Plotting attack vs non-attack comparison...")
    
    # Load new data
    pbs_participants = pd.read_csv(PROJECT_ROOT / 'data/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    
    # Filter for builders only
    builder_participants = pbs_participants[pbs_participants['participant_type'] == 'builder']
    
    # Separate attack and non-attack builders
    attack_builders = builder_participants[builder_participants['is_attacker'] == True]
    nonattack_builders = builder_participants[builder_participants['is_attacker'] == False]
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Growth rate comparison
    attack_growth = attack_builders['growth_rate']
    nonattack_growth = nonattack_builders['growth_rate']
    
    ax1.boxplot([attack_growth, nonattack_growth], labels=['Attack Builders', 'Non-Attack Builders'])
    ax1.set_ylabel('Growth Rate (%)')
    ax1.set_title('Growth Rate Comparison')
    ax1.grid(True, alpha=0.3)
    
    # Final stake comparison
    attack_final = attack_builders['final_stake_eth']
    nonattack_final = nonattack_builders['final_stake_eth']
    
    ax2.boxplot([attack_final, nonattack_final], labels=['Attack Builders', 'Non-Attack Builders'])
    ax2.set_ylabel('Final Stake (ETH)')
    ax2.set_title('Final Stake Comparison')
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle('Attack vs Non-Attack Builder Performance (10,000 Blocks)\n25 Attack Builders, 50 Attack Users', fontsize=16)
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/attack_vs_nonattack_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: attack_vs_nonattack_comparison.png")

def main():
    """Generate all plots with new data."""
    print("Generating updated restaking plots with new 10,000 block data...")
    
    # Create figures/restake directory
    figures_dir = PROJECT_ROOT / 'figures/restake'
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plots
    plot_builder_growth()
    plot_proposer_growth()
    plot_centralization_metrics()
    plot_attack_vs_nonattack_comparison()
    
    print("All plots completed with new data!")

if __name__ == "__main__":
    main() 