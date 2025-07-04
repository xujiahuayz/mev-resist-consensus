import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, List, Tuple

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        'data/same_seed/pbs_network_m1',
        'data/same_seed/pbs_network_m2',
        'figure'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def load_network_metrics(m: int) -> pd.DataFrame:
    """Load network metrics for a given m value."""
    try:
        return pd.read_csv(f"data/same_seed/pbs_network_m{m}/network_metrics.csv")
    except FileNotFoundError:
        print(f"Network metrics for m={m} not found. Please run the simulation first.")
        return pd.DataFrame()

def load_block_data(m: int, num_attacker_builders: int, num_attacker_users: int) -> pd.DataFrame:
    """Load block data for a given configuration."""
    try:
        return pd.read_csv(f"data/same_seed/pbs_network_m{m}/pbs_block_data_builders{num_attacker_builders}_users{num_attacker_users}.csv")
    except FileNotFoundError:
        print(f"Block data for m={m}, builders={num_attacker_builders}, users={num_attacker_users} not found.")
        return pd.DataFrame()

def analyze_builder_performance(block_data: pd.DataFrame) -> Dict[str, float]:
    """Analyze builder performance metrics."""
    # Calculate winning rate
    total_blocks = len(block_data)
    winning_blocks = block_data[block_data['builder_id'] != '']
    winning_rate = len(winning_blocks) / total_blocks if total_blocks > 0 else 0

    # Calculate average profit per winning block
    avg_profit = winning_blocks['total_gas_fee'].mean() if len(winning_blocks) > 0 else 0

    return {
        'winning_rate': winning_rate,
        'avg_profit': avg_profit
    }

def plot_network_effects():
    # Ensure directories exist
    ensure_directories()

    # Set up the plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    # Load network metrics for both m values
    metrics_m1 = load_network_metrics(1)
    metrics_m2 = load_network_metrics(2)

    if metrics_m1.empty or metrics_m2.empty:
        print("Please run the simulation first to generate network metrics.")
        return

    # Add m value to each dataframe for better plotting
    metrics_m1['m'] = 'm=1'
    metrics_m2['m'] = 'm=2'
    metrics_combined = pd.concat([metrics_m1, metrics_m2])

    # Plot 1: Degree Distribution Comparison
    sns.kdeplot(data=metrics_combined, x='degree', hue='m', ax=axes[0,0])
    axes[0,0].set_title('Node Degree Distribution')
    axes[0,0].set_xlabel('Degree')
    axes[0,0].set_ylabel('Density')

    # Plot 2: Latency Distribution
    sns.kdeplot(data=metrics_combined, x='avg_latency', hue='m', ax=axes[0,1])
    axes[0,1].set_title('Average Latency Distribution')
    axes[0,1].set_xlabel('Average Latency')
    axes[0,1].set_ylabel('Density')

    # Analyze builder performance for different configurations
    builder_performance = {
        'm1': {'winning_rates': [], 'avg_profits': []},
        'm2': {'winning_rates': [], 'avg_profits': []}
    }

    # Test configurations
    attacker_builders = [1, 5, 10, 15, 20]
    attacker_users = [0, 10, 25, 50]

    for m in [1, 2]:
        for num_builders in attacker_builders:
            for num_users in attacker_users:
                block_data = load_block_data(m, num_builders, num_users)
                if not block_data.empty:
                    performance = analyze_builder_performance(block_data)
                    builder_performance[f'm{m}']['winning_rates'].append(performance['winning_rate'])
                    builder_performance[f'm{m}']['avg_profits'].append(performance['avg_profit'])

    if not builder_performance['m1']['winning_rates'] or not builder_performance['m2']['winning_rates']:
        print("No block data found. Please run the simulation first.")
        return

    # Create performance dataframe for seaborn
    performance_data = pd.DataFrame({
        'm': ['m=1', 'm=2'] * 2,
        'metric': ['Winning Rate'] * 2 + ['Average Profit'] * 2,
        'value': [
            sum(builder_performance['m1']['winning_rates'])/len(builder_performance['m1']['winning_rates']),
            sum(builder_performance['m2']['winning_rates'])/len(builder_performance['m2']['winning_rates']),
            sum(builder_performance['m1']['avg_profits'])/len(builder_performance['m1']['avg_profits']),
            sum(builder_performance['m2']['avg_profits'])/len(builder_performance['m2']['avg_profits'])
        ]
    })

    # Plot 3: Winning Rate Comparison
    sns.barplot(data=performance_data[performance_data['metric'] == 'Winning Rate'],
                x='m', y='value', ax=axes[1,0])
    axes[1,0].set_title('Average Winning Rate')
    axes[1,0].set_ylabel('Winning Rate')

    # Plot 4: Average Profit Comparison
    sns.barplot(data=performance_data[performance_data['metric'] == 'Average Profit'],
                x='m', y='value', ax=axes[1,1])
    axes[1,1].set_title('Average Profit per Winning Block')
    axes[1,1].set_ylabel('Profit (Gas Fee)')

    plt.tight_layout()
    plt.savefig('figures/ss/network_effects.png')
    plt.close()

if __name__ == "__main__":
    plot_network_effects()
