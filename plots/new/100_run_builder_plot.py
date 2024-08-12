import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import t, norm

# Function to calculate Gini coefficient
def gini_coefficient(profits):
    sorted_profits = np.sort(profits)
    n = len(profits)
    cumulative_profits = np.cumsum(sorted_profits, dtype=float)
    cumulative_profits /= cumulative_profits[-1]
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * cumulative_profits)) / (n * np.sum(cumulative_profits))

# Function to load builder data and calculate Gini coefficients for PBS
def load_pbs_data(data_dir, mev_counts):
    pbs_gini = []

    for mev_count in mev_counts:
        gini_values = []
        for run_id in range(1, 51):
            file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pbs', 'block_data_pbs.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                builder_counts = df['builder_id'].value_counts().values
                gini = gini_coefficient(builder_counts)
                gini_values.append(gini)
        pbs_gini.append(gini_values)

    return pbs_gini

# Function to simulate PoS Gini coefficients
def simulate_pos_gini(num_builders_list, num_simulations):
    results = []
    for num_mev_builders in num_builders_list:
        gini_values = []
        for _ in range(num_simulations):
            profits = np.random.uniform(0, 1, 50)
            gini = gini_coefficient(profits)
            gini_values.append(gini)
        results.append(gini_values)
    return results

# Function to calculate mean and confidence intervals
def calculate_confidence_intervals(data):
    means = [np.mean(run) for run in data]
    cis = [t.interval(0.95, len(run)-1, loc=np.mean(run), scale=np.std(run)/np.sqrt(len(run))) for run in data]
    return means, cis

# Function to plot Gini coefficient with confidence intervals
def plot_gini_with_confidence(pbs_data, pos_data, num_builders_list):
    mean_gini_pbs, ci_gini_pbs = calculate_confidence_intervals(pbs_data)
    mean_gini_pos, ci_gini_pos = calculate_confidence_intervals(pos_data)
    
    plt.figure(figsize=(12, 8))
    
    # Plot PBS with confidence intervals
    plt.plot(num_builders_list, mean_gini_pbs, label='PBS', color='blue')
    plt.fill_between(num_builders_list, [ci[0] for ci in ci_gini_pbs], [ci[1] for ci in ci_gini_pbs], color='blue', alpha=0.2)
    
    # Plot PoS with confidence intervals
    plt.plot(num_builders_list, mean_gini_pos, label='PoS (Simulated)', color='orange')
    plt.fill_between(num_builders_list, [ci[0] for ci in ci_gini_pos], [ci[1] for ci in ci_gini_pos], color='orange', alpha=0.2)
    
    # Labels and Title
    plt.xlabel('Number of MEV Builders/Validators', fontsize=18)
    plt.ylabel('Gini Coefficient', fontsize=18)
    plt.title('Gini Coefficient with 95% Confidence Intervals', fontsize=20)
    
    # Legends
    plt.legend(loc='best', fontsize=14)
    plt.grid(True)
    
    # Save the plot
    os.makedirs('figures/new', exist_ok=True)
    plt.savefig('figures/new/gini_coefficient_with_confidence_intervals.png')
    plt.show()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    num_builders_list = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    num_simulations = 1000

    # Load PBS data
    pbs_gini_data = load_pbs_data(data_dir, num_builders_list)
    
    # Simulate PoS Gini results
    pos_gini_data = simulate_pos_gini(num_builders_list, num_simulations)
    
    # Plot results with confidence intervals
    plot_gini_with_confidence(pbs_gini_data, pos_gini_data, num_builders_list)
