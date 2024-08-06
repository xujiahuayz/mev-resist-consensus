import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Function to calculate Gini coefficient
def gini_coefficient(profits):
    sorted_profits = np.sort(profits)
    n = len(profits)
    cumulative_profits = np.cumsum(sorted_profits, dtype=float)
    cumulative_profits /= cumulative_profits[-1]
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * cumulative_profits)) / (n * np.sum(cumulative_profits))

# Parameters
num_builders = 50
num_simulations = 1000
mu_mev = 10
sigma_mev = 2
mu_gas = 5
sigma_gas = 1

# Proportions of MEV transactions
mev_proportions = np.linspace(0, 1, 21)

# Store Gini coefficients
gini_values = []

# Simulate and calculate Gini coefficients
for p_mev in mev_proportions:
    p_non_mev = 1 - p_mev
    gini_coeffs = []
    for _ in range(num_simulations):
        mev_profits = norm.rvs(loc=mu_mev, scale=sigma_mev, size=num_builders)
        gas_profits = norm.rvs(loc=mu_gas, scale=sigma_gas, size=num_builders)
        total_profits = p_mev * mev_profits + p_non_mev * gas_profits
        gini_coeffs.append(gini_coefficient(total_profits))
    gini_values.append(np.mean(gini_coeffs))

# Plot Gini coefficient vs. proportion of MEV transactions
plt.figure(figsize=(10, 6))
plt.plot(mev_proportions, gini_values, marker='o')
plt.xlabel('Proportion of MEV Transactions')
plt.ylabel('Expected Gini Coefficient')
plt.title('Expected Gini Coefficient vs. Proportion of MEV Transactions')
plt.grid(True)
plt.show()
