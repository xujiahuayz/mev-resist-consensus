import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, t
import os

# Function to calculate Gini coefficient
def gini_coefficient(profits):
    sorted_profits = np.sort(profits)
    n = len(profits)
    cumulative_profits = np.cumsum(sorted_profits, dtype=float)
    cumulative_profits /= cumulative_profits[-1]
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * cumulative_profits)) / (n * np.sum(cumulative_profits))

def simulate_data(total_builders, num_builders_list, num_simulations, mu_mev, sigma_mev, mu_gas, sigma_gas):
    results = {
        'gini_pbs': [],
        'gini_pos': [],
        'selected_pbs': [],
        'selected_pos': []
    }

    for num_mev_builders in num_builders_list:
        num_non_mev_builders = total_builders - num_mev_builders
        gini_pbs = []
        gini_pos = []
        selected_pbs = []
        selected_pos = []
        for _ in range(num_simulations):
            mev_profits_pbs = norm.rvs(loc=mu_mev, scale=sigma_mev, size=num_mev_builders)
            non_mev_profits_pbs = norm.rvs(loc=mu_gas, scale=sigma_gas, size=num_non_mev_builders)
            total_profits_pbs = np.concatenate([mev_profits_pbs, non_mev_profits_pbs])
            
            mev_profits_pos = norm.rvs(loc=mu_mev, scale=sigma_mev, size=num_mev_builders)
            non_mev_profits_pos = norm.rvs(loc=mu_gas, scale=sigma_gas, size=num_non_mev_builders)
            total_profits_pos = np.concatenate([mev_profits_pos, non_mev_profits_pos])
            
            selected_pbs.append(np.argmax(total_profits_pbs))
            selected_pos.append(np.argmax(total_profits_pos))
            
            gini_pbs.append(gini_coefficient(total_profits_pbs))
            gini_pos.append(gini_coefficient(total_profits_pos))
        
        results['gini_pbs'].append(gini_pbs)
        results['gini_pos'].append(gini_pos)
        results['selected_pbs'].append(selected_pbs)
        results['selected_pos'].append(selected_pos)
    
    return results

def plot_gini_coefficient(num_builders_list, results):
    mean_gini_pbs = [np.mean(g) for g in results['gini_pbs']]
    mean_gini_pos = [np.mean(g) for g in results['gini_pos']]
    ci_gini_pbs = [t.interval(0.95, len(g)-1, loc=np.mean(g), scale=np.std(g)/np.sqrt(len(g))) for g in results['gini_pbs']]
    ci_gini_pos = [t.interval(0.95, len(g)-1, loc=np.mean(g), scale=np.std(g)/np.sqrt(len(g))) for g in results['gini_pos']]

    plt.figure(figsize=(10, 6))
    plt.errorbar(num_builders_list, mean_gini_pbs, yerr=[(top-bot)/2 for bot, top in ci_gini_pbs], label='PBS', color='blue', fmt='-o')
    plt.errorbar(num_builders_list, mean_gini_pos, yerr=[(top-bot)/2 for bot, top in ci_gini_pos], label='PoS', color='orange', fmt='-o')
    plt.xlabel('Number of MEV Builders/Validators')
    plt.ylabel('Gini Coefficient')
    plt.title('Gini Coefficient of Builder/Validator Selection')
    plt.legend()
    plt.grid(True)
    plt.savefig('figures/new/gini_coefficient.png')
    plt.close()

def plot_selected_distribution(num_builders_list, results, total_builders):
    selected_indices = [num_builders_list.index(x) for x in [1, 25, 50]]
    fig, axs = plt.subplots(1, len(selected_indices), figsize=(18, 6), sharey=True)

    for idx, selected_index in enumerate(selected_indices):
        num_builders = num_builders_list[selected_index]
        selected_pbs_hist, bins_pbs = np.histogram(results['selected_pbs'][selected_index], bins=np.arange(total_builders+1)-0.5, density=True)
        selected_pos_hist, bins_pos = np.histogram(results['selected_pos'][selected_index], bins=np.arange(total_builders+1)-0.5, density=True)
        
        axs[idx].plot(bins_pbs[:-1], selected_pbs_hist, label='PBS', color='blue')
        axs[idx].fill_between(bins_pbs[:-1], selected_pbs_hist, alpha=0.2, color='blue')
        
        axs[idx].plot(bins_pos[:-1], selected_pos_hist, label='PoS', color='orange')
        axs[idx].fill_between(bins_pos[:-1], selected_pos_hist, alpha=0.2, color='orange')
        
        axs[idx].set_title(f'MEV Builders/Validators = {num_builders}')
        axs[idx].set_xlabel('Number of Blocks Built')
        axs[idx].legend()

    axs[0].set_ylabel('Density')
    plt.tight_layout()
    plt.savefig('figures/new/selected_distribution.png')
    plt.close()

if __name__ == "__main__":
    os.makedirs('figures/new', exist_ok=True)
    total_builders = 50
    num_builders_list = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    num_simulations = 1000
    mu_mev = 10
    sigma_mev = 2
    mu_gas = 5
    sigma_gas = 1

    results = simulate_data(total_builders, num_builders_list, num_simulations, mu_mev, sigma_mev, mu_gas, sigma_gas)
    plot_gini_coefficient(num_builders_list, results)
    plot_selected_distribution(num_builders_list, results, total_builders)
