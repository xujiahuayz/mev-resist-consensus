import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os

# Load the data
block_data_pbs = pd.read_csv('data/block_data_pbs.csv')
block_data_pos = pd.read_csv('data/block_data_pos.csv')
transaction_data_pbs = pd.read_csv('data/transaction_data_pbs.csv')
transaction_data_pos = pd.read_csv('data/transaction_data_pos.csv')

# Calculate the Gini coefficient
def gini(arr):
    sorted_arr = np.sort(arr)
    n = arr.shape[0]
    cumulative_values = np.cumsum(sorted_arr)
    gini_coefficient = (2.0 / n) * (np.arange(1, n + 1) * sorted_arr).sum() - (n + 1) / n
    return gini_coefficient

# Profit distribution for builders and validators
builder_profits = block_data_pbs.groupby('builder_type')['total_gas'].sum()
validator_profits = block_data_pos.groupby('validator_type')['total_gas'].sum()

# Create the directory for saving figures
os.makedirs('figures/new', exist_ok=True)

# Plot builder and validator distribution
plt.figure(figsize=(12, 6))
sns.countplot(x='builder_type', data=block_data_pbs)
plt.title('Builder Distribution under PBS')
plt.savefig('figures/new/builder_distribution_pbs.png')
plt.close()

plt.figure(figsize=(12, 6))
sns.countplot(x='validator_type', data=block_data_pos)
plt.title('Validator Distribution under PoS')
plt.savefig('figures/new/validator_distribution_pos.png')
plt.close()

# Gini coefficient heatmap for profit distribution
builder_profits_gini = gini(builder_profits.values)
validator_profits_gini = gini(validator_profits.values)

# Print Gini coefficient comparison
print(f"Gini Coefficient for PBS: {builder_profits_gini}")
print(f"Gini Coefficient for PoS: {validator_profits_gini}")

if validator_profits_gini < builder_profits_gini:
    print("PoS distributes more equally than PBS")
else:
    print("PBS distributes more equally than PoS")

# Lorenz curve plot for profit distribution
def lorenz_curve(arr):
    sorted_arr = np.sort(arr)
    n = arr.shape[0]
    cumulative_values = np.cumsum(sorted_arr)
    lorenz_curve = cumulative_values / cumulative_values[-1]
    lorenz_curve = np.insert(lorenz_curve, 0, 0)
    return lorenz_curve

builder_lorenz = lorenz_curve(builder_profits.values)
validator_lorenz = lorenz_curve(validator_profits.values)

plt.figure(figsize=(12, 6))
plt.plot(np.linspace(0, 1, builder_lorenz.size), builder_lorenz, label='PBS Builders')
plt.plot(np.linspace(0, 1, validator_lorenz.size), validator_lorenz, label='PoS Validators')
plt.plot([0, 1], [0, 1], linestyle='--', color='k', label='Equality Line')
plt.xlabel('Cumulative Share of Builders/Validators')
plt.ylabel('Cumulative Share of Profits')
plt.title('Lorenz Curve for Profit Distribution')
plt.legend()
plt.savefig('figures/new/lorenz_curve.png')
plt.close()

# Profit distribution variations under different scenarios
plt.figure(figsize=(12, 6))
sns.boxplot(x='block_id', y='total_gas', hue='builder_type', data=block_data_pbs)
plt.title('Profit Distribution Variations under Different Scenarios within PBS')
plt.savefig('figures/new/profit_distribution_pbs.png')
plt.close()

plt.figure(figsize=(12, 6))
sns.boxplot(x='block_id', y='total_gas', hue='validator_type', data=block_data_pos)
plt.title('Profit Distribution Variations under Different Scenarios within PoS')
plt.savefig('figures/new/profit_distribution_pos.png')
plt.close()
