import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.signal import savgol_filter
import os

# Ensure the output directory exists
os.makedirs('figures/theory', exist_ok=True)

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
num_simulations = 10000  # Increased number of simulations for smoother results
mu_mev = 10
sigma_mev = 2
mu_gas = 5
sigma_gas = 1

# Number of MEV builders/validators
mev_builders_range = np.arange(1, num_builders + 1)

# Store Gini coefficients
gini_values = []

# Simulate and calculate Gini coefficients
for mev_builders in mev_builders_range:
    non_mev_builders = num_builders - mev_builders
    gini_coeffs = []
    for _ in range(num_simulations):
        mev_profits = norm.rvs(loc=mu_mev, scale=sigma_mev, size=mev_builders)
        gas_profits = norm.rvs(loc=mu_gas, scale=sigma_gas, size=non_mev_builders)
        total_profits = np.concatenate((mev_profits, gas_profits))
        gini_coeffs.append(gini_coefficient(total_profits))
    gini_values.append(np.mean(gini_coeffs))

# Apply Savitzky-Golay filter for smoothing
gini_values_smooth = savgol_filter(gini_values, window_length=7, polyorder=2)

# Plot smoothed Gini coefficient vs. number of MEV builders/validators
plt.figure(figsize=(10, 6))
plt.plot(mev_builders_range, gini_values_smooth)
plt.xlabel('Number of MEV Builders/Validators')
plt.ylabel('Expected Gini Coefficient')
plt.title('Expected Gini Coefficient vs. Number of MEV Builders/Validators')
plt.grid(True)
plt.savefig('figures/theory/gini.png')
plt.show()
