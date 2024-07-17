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
    relative_mean = cumulative_values[-1] / n
    gini_coefficient = (2 * (np.arange(1, n + 1) * sorted_arr).sum() / cumulative_values[-1] - (n + 1)) / n
    return gini_coefficient

# Calculate the number of blocks built by type
blocks_built_pbs = block_data_pbs.groupby(['builder_type']).size().reset_index(name='blocks_built')
blocks_built_pos = block_data_pos.groupby(['validator_type']).size().reset_index(name='blocks_built')

blocks_built_pbs['type'] = 'PBS'
blocks_built_pos['type'] = 'PoS'

blocks_built = pd.concat([blocks_built_pbs.rename(columns={'builder_type': 'participant_type'}),
                          blocks_built_pos.rename(columns={'validator_type': 'participant_type'})])

# Calculate profits
builder_profits_pbs = block_data_pbs.groupby('builder_type')['total_gas'].sum().reset_index(name='profit')
validator_profits_pos = block_data_pos.groupby('validator_type')['total_gas'].sum().reset_index(name='profit')

builder_profits_pbs['type'] = 'PBS'
validator_profits_pos['type'] = 'PoS'

profits = pd.concat([builder_profits_pbs.rename(columns={'builder_type': 'participant_type'}),
                     validator_profits_pos.rename(columns={'validator_type': 'participant_type'})])

# Create the directory for saving figures
os.makedirs('figures/new', exist_ok=True)

# Plot the number of blocks built
plt.figure(figsize=(12, 6))
sns.barplot(x='participant_type', y='blocks_built', hue='type', data=blocks_built)
plt.title('Number of Blocks Built')
plt.xlabel('Participant Type')
plt.ylabel('Number of Blocks Built')
plt.savefig('figures/new/number_of_blocks_built.png')
plt.close()

# Plot the profits
plt.figure(figsize=(12, 6))
sns.barplot(x='participant_type', y='profit', hue='type', data=profits)
plt.title('Profits')
plt.xlabel('Participant Type')
plt.ylabel('Profit')
plt.savefig('figures/new/profits.png')
plt.close()

# Print Gini coefficient comparison
builder_profits = block_data_pbs.groupby('builder_type')['total_gas'].sum()
validator_profits = block_data_pos.groupby('validator_type')['total_gas'].sum()

builder_profits_gini = gini(builder_profits.values)
validator_profits_gini = gini(validator_profits.values)

print(f"Gini Coefficient for PBS: {builder_profits_gini}")
print(f"Gini Coefficient for PoS: {validator_profits_gini}")

if validator_profits_gini < builder_profits_gini:
    print("PoS distributes more equally than PBS")
else:
    print("PBS distributes more equally than PoS")

# Profit distribution for builders and validators
print("Builder Profits Distribution (PBS):")
print(builder_profits)
print("\nValidator Profits Distribution (PoS):")
print(validator_profits)
